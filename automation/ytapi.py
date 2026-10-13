#!/usr/bin/env python3
"""
ytapi.py - the YouTube Data + Analytics API side of TubeFlow.

Pulls what your audience is telling you (analytics, retention, comments, search terms) and what is
working in your niche (trends), in the file formats the yt-* skills already read. It can also upload
a finished video and post a comment reply, both behind explicit flags.

Usage:
  python automation/ytapi.py auth                         # one-time Google sign-in in your browser
  python automation/ytapi.py videos                       # your uploads with stats
  python automation/ytapi.py analytics --days 28          # per-video metrics, search terms, countries, ages
  python automation/ytapi.py retention VIDEO_ID           # retention CSV for /yt-retention
  python automation/ytapi.py comments --video VIDEO_ID    # one video's comments, for /yt-comment
  python automation/ytapi.py comments --channel           # latest comments across the channel
  python automation/ytapi.py snapshot                     # all of the above in one dated folder (/learn uses this)
  python automation/ytapi.py trends ["query" ...]         # niche outliers, input for yt-viral/swipe.py
  python automation/ytapi.py upload video.mp4 --meta meta.json [--privacy private|unlisted|public]
  python automation/ytapi.py playlists [--yes]            # series playlists from profile/series-plan.yaml
  python automation/ytapi.py reply COMMENT_ID --text "..." [--yes]

Prerequisites:
  pip install -r automation/requirements.txt
  An OAuth client file from Google Cloud Console (see docs/AUTOMATION.md).

Nothing here ever needs your password. Sign-in happens in your own browser through Google, and the
resulting token is stored on your computer only (youtube_api.token_file in config.yaml).
"""

import argparse
import csv
import datetime as dt
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent

SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/youtube.force-ssl",  # needed to post comment replies
    "https://www.googleapis.com/auth/youtube.upload",
]

DEFAULTS = {
    "client_secret_file": "~/.config/tubeflow/client_secret.json",
    "token_file": "~/.config/tubeflow/token.json",
    "data_dir": "data",
    "default_privacy": "private",
    "trend_queries": [],
}

# Words that mark a comment as a question, in English, Hindi (Devanagari and romanised) and Bengali.
QUESTION_WORDS = re.compile(
    r"\b(how|what|why|which|when|where|can you|could you|please make|kaise|kya|kyun|kyon|kaun|kab|"
    r"kahan|kaha)\b|कैसे|क्या|क्यों|कौन|कब|कहाँ|কীভাবে|কিভাবে|কি\b|কী\b|কেন|কোন|কখন|কোথায়",
    re.IGNORECASE,
)


# === CONFIGURATION ===

def load_config() -> dict:
    """Read youtube_api settings from config.yaml (repo root), falling back to profile/config.yaml."""
    for path in (REPO_ROOT / "config.yaml", REPO_ROOT / "profile" / "config.yaml"):
        if path.exists():
            try:
                import yaml
            except ImportError:
                sys.exit("PyYAML is required: pip install -r automation/requirements.txt")
            with open(path, encoding="utf-8") as fh:
                config = yaml.safe_load(fh) or {}
            settings = dict(DEFAULTS)
            settings.update(config.get("youtube_api") or {})
            settings["languages"] = config.get("languages") or {"primary": "en", "also": []}
            return settings
    return dict(DEFAULTS, languages={"primary": "en", "also": []})


def data_dir(settings: dict) -> Path:
    path = Path(os.path.expanduser(settings["data_dir"]))
    if not path.is_absolute():
        path = REPO_ROOT / path
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_json(path: Path, payload) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
    return path


# === AUTH ===

def get_credentials(settings: dict, interactive: bool = True):
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        sys.exit("Google API libraries missing: pip install -r automation/requirements.txt")

    token_file = Path(os.path.expanduser(settings["token_file"]))
    secret_file = Path(os.path.expanduser(settings["client_secret_file"]))
    creds = None
    if token_file.exists():
        creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)
    if creds and creds.valid:
        return creds
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        if not interactive:
            sys.exit("Not signed in. Run: python automation/ytapi.py auth")
        if not secret_file.exists():
            sys.exit(
                f"OAuth client file not found at {secret_file}.\n"
                "Create one in Google Cloud Console (Desktop app) and save it there. See docs/AUTOMATION.md."
            )
        flow = InstalledAppFlow.from_client_secrets_file(str(secret_file), SCOPES)
        creds = flow.run_local_server(port=0, prompt="consent")
    token_file.parent.mkdir(parents=True, exist_ok=True)
    token_file.write_text(creds.to_json(), encoding="utf-8")
    os.chmod(token_file, 0o600)
    return creds


class Clients:
    """Lazily built API clients, so tests can inject fakes."""

    def __init__(self, settings: dict, youtube=None, analytics=None):
        self.settings = settings
        self._youtube = youtube
        self._analytics = analytics

    def _build(self, name: str, version: str):
        from googleapiclient.discovery import build
        return build(name, version, credentials=get_credentials(self.settings, interactive=False),
                     cache_discovery=False)

    @property
    def youtube(self):
        if self._youtube is None:
            self._youtube = self._build("youtube", "v3")
        return self._youtube

    @property
    def analytics(self):
        if self._analytics is None:
            self._analytics = self._build("youtubeAnalytics", "v2")
        return self._analytics


# === HELPERS ===

def parse_duration(iso: str) -> int:
    """ISO 8601 duration (PT1H2M3S) to seconds."""
    m = re.fullmatch(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    if not m:
        return 0
    d, h, mi, s = (int(x) if x else 0 for x in m.groups())
    return d * 86400 + h * 3600 + mi * 60 + s


def guess_language(text: str) -> str:
    """Script-based guess: Bengali, Devanagari (Hindi), or Latin (English or romanised Hindi)."""
    bengali = len(re.findall(r"[ঀ-৿]", text))
    devanagari = len(re.findall(r"[ऀ-ॿ]", text))
    if bengali > devanagari and bengali >= 3:
        return "bn"
    if devanagari >= 3:
        return "hi"
    return "en"


def is_question(text: str) -> bool:
    return "?" in text or "？" in text or bool(QUESTION_WORDS.search(text))


def chunks(items: List[str], size: int) -> Iterable[List[str]]:
    for i in range(0, len(items), size):
        yield items[i:i + size]


def iso_date(days_ago: int) -> str:
    return (dt.date.today() - dt.timedelta(days=days_ago)).isoformat()


def rows_as_dicts(report: dict) -> List[dict]:
    headers = [h["name"] for h in report.get("columnHeaders", [])]
    return [dict(zip(headers, row)) for row in report.get("rows", []) or []]


def my_channel(clients: Clients) -> dict:
    resp = clients.youtube.channels().list(part="snippet,contentDetails,statistics", mine=True).execute()
    items = resp.get("items", [])
    if not items:
        sys.exit("This Google account has no YouTube channel. Sign in with the channel's account.")
    return items[0]


def video_details(clients: Clients, ids: List[str]) -> List[dict]:
    out = []
    for batch in chunks(ids, 50):
        resp = clients.youtube.videos().list(part="snippet,statistics,contentDetails", id=",".join(batch)).execute()
        for v in resp.get("items", []):
            seconds = parse_duration(v["contentDetails"].get("duration", ""))
            stats = v.get("statistics", {})
            out.append({
                "id": v["id"],
                "url": f"https://www.youtube.com/watch?v={v['id']}",
                "channel": v["snippet"].get("channelTitle", ""),
                "channel_id": v["snippet"].get("channelId", ""),
                "title": v["snippet"].get("title", ""),
                "published": v["snippet"].get("publishedAt", ""),
                "language": v["snippet"].get("defaultAudioLanguage") or v["snippet"].get("defaultLanguage") or "",
                "duration": seconds,
                # The API does not say whether a video is a Short; up to 3 minutes is the best guess.
                "short_guess": seconds <= 180,
                "views": int(stats.get("viewCount", 0)),
                "likes": int(stats.get("likeCount", 0)),
                "comments": int(stats.get("commentCount", 0)),
            })
    return out


def playlist_video_ids(clients: Clients, playlist_id: str, limit: int) -> List[str]:
    ids, token = [], None
    while len(ids) < limit:
        resp = clients.youtube.playlistItems().list(
            part="contentDetails", playlistId=playlist_id, maxResults=min(50, limit - len(ids)), pageToken=token
        ).execute()
        ids += [i["contentDetails"]["videoId"] for i in resp.get("items", [])]
        token = resp.get("nextPageToken")
        if not token:
            break
    return ids


# === COMMANDS ===

def cmd_auth(clients: Clients, args) -> dict:
    get_credentials(clients.settings, interactive=True)
    ch = my_channel(clients)
    print(f"Signed in. Channel: {ch['snippet']['title']} ({ch['id']})")
    return {"channel_id": ch["id"], "title": ch["snippet"]["title"]}


def cmd_videos(clients: Clients, args, out_dir: Optional[Path] = None) -> List[dict]:
    ch = my_channel(clients)
    uploads = ch["contentDetails"]["relatedPlaylists"]["uploads"]
    videos = video_details(clients, playlist_video_ids(clients, uploads, args.limit))
    path = write_json((out_dir or data_dir(clients.settings)) / "videos.json", videos)
    print(f"{len(videos)} videos -> {path}")
    for v in videos[:15]:
        kind = "short" if v["short_guess"] else "long "
        print(f"  {v['published'][:10]}  {kind}  {v['views']:>8,} views  {v['title'][:70]}")
    return videos


def cmd_analytics(clients: Clients, args, out_dir: Optional[Path] = None) -> dict:
    start, end = iso_date(args.days), iso_date(0)
    q = clients.analytics.reports()

    def run(**kw):
        return rows_as_dicts(q.query(ids="channel==MINE", startDate=start, endDate=end, **kw).execute())

    report = {
        "period": {"start": start, "end": end},
        "per_video": run(
            metrics="views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,"
                    "subscribersGained,likes,comments,shares",
            dimensions="video", sort="-views", maxResults=200),
        # What people typed into YouTube search before watching you: the clearest demand signal.
        "search_terms": run(metrics="views", dimensions="insightTrafficSourceDetail",
                            filters="insightTrafficSourceType==YT_SEARCH", sort="-views", maxResults=25),
        "traffic_sources": run(metrics="views,estimatedMinutesWatched", dimensions="insightTrafficSourceType",
                               sort="-views"),
        "countries": run(metrics="views,estimatedMinutesWatched", dimensions="country", sort="-views",
                         maxResults=15),
        "age_gender": run(metrics="viewerPercentage", dimensions="ageGroup,gender"),
    }
    path = write_json((out_dir or data_dir(clients.settings)) / f"analytics-{args.days}d.json", report)
    print(f"Analytics {start} to {end} -> {path}")
    print("  Top search terms:", ", ".join(r["insightTrafficSourceDetail"] for r in report["search_terms"][:8]) or "none")
    print("  Top countries:   ", ", ".join(r["country"] for r in report["countries"][:6]) or "none")
    return report


def cmd_retention(clients: Clients, args, out_dir: Optional[Path] = None) -> Path:
    """Write a two-column CSV (position %, still watching %) that retention.py reads directly."""
    rows = rows_as_dicts(clients.analytics.reports().query(
        ids="channel==MINE", startDate=iso_date(args.days), endDate=iso_date(0),
        metrics="audienceWatchRatio,relativeRetentionPerformance",
        dimensions="elapsedVideoTimeRatio", filters=f"video=={args.video_id}",
    ).execute())
    if not rows:
        print(f"No retention data for {args.video_id} yet (new or low-view videos have none).")
        return None
    path = (out_dir or data_dir(clients.settings)) / "retention" / f"{args.video_id}.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["position_percent", "watching_percent", "relative_retention"])
        for r in rows:
            w.writerow([round(r["elapsedVideoTimeRatio"] * 100, 2), round(r["audienceWatchRatio"] * 100, 2),
                        r.get("relativeRetentionPerformance")])
    print(f"Retention -> {path}")
    duration = video_details(clients, [args.video_id])
    if duration:
        print(f"  Read it with: python3 <yt-retention>/retention.py {path} --duration {duration[0]['duration']}")
    return path


def fetch_comments(clients: Clients, limit: int, video_id: Optional[str] = None,
                   channel_id: Optional[str] = None, owner_id: Optional[str] = None) -> List[dict]:
    out, token = [], None
    params = {"videoId": video_id} if video_id else {"allThreadsRelatedToChannelId": channel_id}
    while len(out) < limit:
        resp = clients.youtube.commentThreads().list(
            part="snippet,replies", maxResults=min(100, limit - len(out)), order="time",
            textFormat="plainText", pageToken=token, **params,
        ).execute()
        for t in resp.get("items", []):
            top = t["snippet"]["topLevelComment"]
            s = top["snippet"]
            replies = (t.get("replies") or {}).get("comments", [])
            text = s.get("textDisplay") or s.get("textOriginal") or ""
            out.append({
                "id": top["id"],
                "video_id": t["snippet"].get("videoId", ""),
                "author": s.get("authorDisplayName", ""),
                "text": text,
                "likes": s.get("likeCount", 0),
                "published": s.get("publishedAt", ""),
                "reply_count": t["snippet"].get("totalReplyCount", 0),
                "answered_by_me": any(
                    (r["snippet"].get("authorChannelId") or {}).get("value") == owner_id for r in replies
                ) if owner_id else None,
                "language": guess_language(text),
                "is_question": is_question(text),
            })
        token = resp.get("nextPageToken")
        if not token:
            break
    return out


def summarise_comments(comments: List[dict]) -> dict:
    langs: Dict[str, int] = {}
    for c in comments:
        langs[c["language"]] = langs.get(c["language"], 0) + 1
    unanswered = [c for c in comments if c["is_question"] and not c["answered_by_me"]]
    return {"total": len(comments), "languages": langs,
            "questions": sum(c["is_question"] for c in comments), "unanswered_questions": len(unanswered)}


def cmd_comments(clients: Clients, args, out_dir: Optional[Path] = None) -> dict:
    ch = my_channel(clients)
    comments = fetch_comments(clients, args.limit, video_id=args.video,
                              channel_id=None if args.video else ch["id"], owner_id=ch["id"])
    payload = {"summary": summarise_comments(comments), "comments": comments}
    name = args.video or "channel"
    path = write_json((out_dir or data_dir(clients.settings)) / "comments" / f"{name}.json", payload)
    s = payload["summary"]
    print(f"{s['total']} comments -> {path}")
    print(f"  questions: {s['questions']} ({s['unanswered_questions']} unanswered)   languages: {s['languages']}")
    return payload


def cmd_snapshot(clients: Clients, args) -> Path:
    """Everything /learn needs, in one dated folder."""
    out = data_dir(clients.settings) / "snapshots" / dt.date.today().isoformat()
    videos = cmd_videos(clients, argparse.Namespace(limit=200), out)
    cmd_analytics(clients, argparse.Namespace(days=args.days), out)
    cmd_comments(clients, argparse.Namespace(video=None, limit=args.comments), out)
    long_videos = [v for v in videos if not v["short_guess"]][:args.retention]
    for v in long_videos:
        cmd_retention(clients, argparse.Namespace(video_id=v["id"], days=365), out)
    print(f"\nSnapshot ready: {out}")
    return out


def cmd_trends(clients: Clients, args) -> dict:
    """Search the niche, then pull each channel's recent uploads so swipe.py can rank outliers
    against that channel's OWN median. Costs about 100 quota units per query (10,000 a day free)."""
    queries = args.queries or clients.settings.get("trend_queries") or []
    if not queries:
        sys.exit("Give one or more queries, or set youtube_api.trend_queries in config.yaml")
    after = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=args.days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    me = None
    try:
        me = my_channel(clients)["id"]
    except SystemExit:
        pass
    seen: Dict[str, int] = {}
    hits = []
    for q in queries:
        params = dict(part="snippet", q=q, type="video", order="viewCount", publishedAfter=after,
                      maxResults=25)
        if args.lang:
            params["relevanceLanguage"] = args.lang
        if args.region:
            params["regionCode"] = args.region
        for item in clients.youtube.search().list(**params).execute().get("items", []):
            cid = item["snippet"]["channelId"]
            if cid == me:
                continue
            seen[cid] = seen.get(cid, 0) + 1
            hits.append({"query": q, "video_id": item["id"]["videoId"], "channel_id": cid,
                         "title": item["snippet"]["title"]})
    top_channels = sorted(seen, key=lambda c: -seen[c])[:args.channels]
    collected = []
    for batch in chunks(top_channels, 50):
        resp = clients.youtube.channels().list(part="contentDetails", id=",".join(batch)).execute()
        for ch in resp.get("items", []):
            uploads = ch["contentDetails"]["relatedPlaylists"]["uploads"]
            collected += video_details(clients, playlist_video_ids(clients, uploads, args.per_channel))
    stamp = dt.date.today().isoformat()
    out = data_dir(clients.settings) / "trends"
    write_json(out / f"{stamp}-search-hits.json", hits)
    path = write_json(out / f"{stamp}-collected.json", collected)
    print(f"{len(hits)} search hits, {len(top_channels)} channels, {len(collected)} videos -> {path}")
    print(f"  Rank outliers with: python3 <yt-viral>/swipe.py {path} --min 2.0")
    return {"hits": hits, "collected": collected}


def build_upload_body(meta: dict, privacy: str, primary_lang: str) -> dict:
    snippet = {
        "title": meta["title"][:100],
        "description": meta.get("description", "")[:5000],
        "tags": meta.get("tags", []),
        "categoryId": str(meta.get("category_id", 27)),  # 27 = Education
        "defaultLanguage": meta.get("language", primary_lang),
        "defaultAudioLanguage": meta.get("audio_language", meta.get("language", primary_lang)),
    }
    status = {
        "privacyStatus": privacy,
        "selfDeclaredMadeForKids": bool(meta.get("made_for_kids", False)),
        # YouTube's altered-or-synthetic content disclosure. Set it true in meta.json when the video
        # contains realistic synthetic content (for example a cloned human voice); see docs/AUTOMATION.md.
        "containsSyntheticMedia": bool(meta.get("synthetic_media", False)),
    }
    if meta.get("publish_at"):
        # Scheduled publishing only works on a private upload; YouTube flips it public at that time.
        status["privacyStatus"] = "private"
        status["publishAt"] = meta["publish_at"]
    body = {"snippet": snippet, "status": status}
    if meta.get("localizations"):
        body["localizations"] = {
            lang: {"title": v["title"][:100], "description": v.get("description", "")[:5000]}
            for lang, v in meta["localizations"].items()
        }
    return body


def cmd_upload(clients: Clients, args) -> dict:
    from googleapiclient.http import MediaFileUpload

    with open(args.meta, encoding="utf-8") as fh:
        meta = json.load(fh)
    privacy = args.privacy or clients.settings.get("default_privacy", "private")
    body = build_upload_body(meta, privacy, clients.settings["languages"].get("primary", "en"))
    parts = "snippet,status" + (",localizations" if "localizations" in body else "")
    print(f"Uploading {args.file} as {body['status']['privacyStatus']}"
          + (f", scheduled {body['status']['publishAt']}" if "publishAt" in body["status"] else ""))
    request = clients.youtube.videos().insert(
        part=parts, body=body, media_body=MediaFileUpload(args.file, chunksize=8 * 1024 * 1024, resumable=True)
    )
    response = None
    while response is None:
        progress, response = request.next_chunk()
        if progress:
            print(f"  {int(progress.progress() * 100)}%")
    video_id = response["id"]
    if meta.get("thumbnail"):
        clients.youtube.thumbnails().set(videoId=video_id, media_body=MediaFileUpload(meta["thumbnail"])).execute()
    print(f"Done: https://studio.youtube.com/video/{video_id}/edit")
    return response


def cmd_playlists(clients: Clients, args) -> list:
    """Create the playlists in profile/series-plan.yaml that do not exist yet (matched by English title).
    New playlists are private unless --privacy says otherwise; Hindi and Bengali titles are added as
    localizations. Costs about 50 quota units per playlist created."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from plan import load_plan

    plan = load_plan(Path(args.plan))
    existing, token = {}, None
    while True:
        resp = clients.youtube.playlists().list(part="snippet", mine=True, maxResults=50, pageToken=token).execute()
        existing.update({p["snippet"]["title"]: p["id"] for p in resp.get("items", [])})
        token = resp.get("nextPageToken")
        if not token:
            break
    primary = clients.settings["languages"].get("primary", "en")
    results = []
    for pl in plan["playlists"]:
        title = pl["title"]["en"]
        if title in existing:
            print(f"  keep    {title}  (https://www.youtube.com/playlist?list={existing[title]})")
            results.append({"id": pl["id"], "playlist_id": existing[title], "created": False})
            continue
        body = {
            "snippet": {"title": title, "description": " ".join(pl["description"].split()),
                        "defaultLanguage": primary},
            "status": {"privacyStatus": args.privacy},
            "localizations": {lang: {"title": t, "description": " ".join(pl["description"].split())}
                              for lang, t in pl["title"].items() if lang != primary},
        }
        if not args.yes:
            print(f"  would create ({args.privacy})  {title}")
            continue
        made = clients.youtube.playlists().insert(part="snippet,status,localizations", body=body).execute()
        print(f"  created {title}  (https://www.youtube.com/playlist?list={made['id']})")
        results.append({"id": pl["id"], "playlist_id": made["id"], "created": True})
    if not args.yes:
        print("DRY RUN. Add --yes to create them.")
    else:
        write_json(data_dir(clients.settings) / "playlists.json", results)
    return results


def cmd_reply(clients: Clients, args) -> Optional[dict]:
    if not args.yes:
        print(f"DRY RUN. Would reply to {args.comment_id}:\n  {args.text}\nAdd --yes to post it.")
        return None
    resp = clients.youtube.comments().insert(
        part="snippet", body={"snippet": {"parentId": args.comment_id, "textOriginal": args.text}}
    ).execute()
    print(f"Posted reply {resp['id']}")
    return resp


# === CLI ===

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("auth", help="sign in once in your browser")
    s = sub.add_parser("videos", help="your uploads with stats")
    s.add_argument("--limit", type=int, default=200)
    s = sub.add_parser("analytics", help="per-video metrics, search terms, countries, ages")
    s.add_argument("--days", type=int, default=28)
    s = sub.add_parser("retention", help="audience-retention CSV for one video")
    s.add_argument("video_id")
    s.add_argument("--days", type=int, default=365)
    s = sub.add_parser("comments", help="comments for one video or the whole channel")
    s.add_argument("--video")
    s.add_argument("--channel", action="store_true", help="latest comments across the channel (default)")
    s.add_argument("--limit", type=int, default=300)
    s = sub.add_parser("snapshot", help="videos + analytics + comments + retention in one folder")
    s.add_argument("--days", type=int, default=28)
    s.add_argument("--comments", type=int, default=300)
    s.add_argument("--retention", type=int, default=5, help="how many recent long videos to pull retention for")
    s = sub.add_parser("trends", help="niche outliers for yt-viral/swipe.py")
    s.add_argument("queries", nargs="*")
    s.add_argument("--days", type=int, default=90)
    s.add_argument("--channels", type=int, default=10)
    s.add_argument("--per-channel", type=int, default=15)
    s.add_argument("--lang", help="relevanceLanguage, for example en, hi, bn")
    s.add_argument("--region", help="regionCode, for example IN or BD")
    s = sub.add_parser("upload", help="upload a video (private unless you say otherwise)")
    s.add_argument("file")
    s.add_argument("--meta", required=True, help="JSON with title, description, tags, localizations...")
    s.add_argument("--privacy", choices=["private", "unlisted", "public"])
    s = sub.add_parser("playlists", help="create the series playlists from profile/series-plan.yaml")
    s.add_argument("--plan", default=str(REPO_ROOT / "profile" / "series-plan.yaml"))
    s.add_argument("--privacy", choices=["private", "unlisted", "public"], default="private")
    s.add_argument("--yes", action="store_true", help="actually create them (dry run otherwise)")
    s = sub.add_parser("reply", help="reply to a comment (dry run unless --yes)")
    s.add_argument("comment_id")
    s.add_argument("--text", required=True)
    s.add_argument("--yes", action="store_true")
    return p


COMMANDS = {
    "auth": cmd_auth, "videos": cmd_videos, "analytics": cmd_analytics, "retention": cmd_retention,
    "comments": cmd_comments, "snapshot": cmd_snapshot, "trends": cmd_trends, "upload": cmd_upload,
    "playlists": cmd_playlists, "reply": cmd_reply,
}


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    clients = Clients(load_config())
    try:
        COMMANDS[args.command](clients, args)
    except Exception as exc:  # turn API errors into one readable line
        if type(exc).__name__ == "HttpError":
            reason = getattr(exc, "reason", "") or str(exc)
            print(f"YouTube API error ({exc.resp.status}): {reason}", file=sys.stderr)
            if exc.resp.status == 403:
                print("Check that both YouTube Data API v3 and YouTube Analytics API are enabled for your "
                      "Google Cloud project, and that today's quota is not used up.", file=sys.stderr)
            return 1
        raise
    return 0


if __name__ == "__main__":
    sys.exit(main())
