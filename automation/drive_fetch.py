#!/usr/bin/env python3
"""
drive_fetch.py - download a Google Drive folder of footage to this computer.

Usage:
  python automation/drive_fetch.py auth                                    # once per Google account
  python automation/drive_fetch.py list  <folder URL or ID>                # what is there, and how big
  python automation/drive_fetch.py fetch <folder URL or ID> [--dest footage/] [--videos-only]

Read-only: it can see and download your Drive files, never change or delete them. Sub-folders are
kept as sub-folders. Files already downloaded with the same size are skipped, so an interrupted
fetch can simply be re-run.

Use the same OAuth client file as ytapi.py (enable "Google Drive API" in the same Cloud project).
Sign in with the Google account that owns or can see the footage; --account keeps several apart.
"""

import argparse
import io
import os
import re
import sys
from pathlib import Path
from typing import List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
CLIENT_SECRET = "~/.config/tubeflow/client_secret.json"
FOLDER = "application/vnd.google-apps.folder"
MEDIA_PREFIXES = ("video/", "image/", "audio/")


def folder_id(value: str) -> str:
    """Accept a full Drive folder URL or a bare ID."""
    m = re.search(r"/folders/([A-Za-z0-9_-]+)", value) or re.search(r"[?&]id=([A-Za-z0-9_-]+)", value)
    return m.group(1) if m else value.strip()


def get_service(account: str, interactive: bool = False):
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError:
        sys.exit("Google API libraries missing: pip install -r automation/requirements.txt")
    token = Path(os.path.expanduser(f"~/.config/tubeflow/token-drive-{account}.json"))
    creds = Credentials.from_authorized_user_file(str(token), SCOPES) if token.exists() else None
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    elif not (creds and creds.valid):
        if not interactive:
            sys.exit(f"Not signed in to Drive. Run: python automation/drive_fetch.py --account {account} auth")
        secret = Path(os.path.expanduser(CLIENT_SECRET))
        if not secret.exists():
            sys.exit(f"OAuth client file not found at {secret}. See docs/AUTOMATION.md.")
        creds = InstalledAppFlow.from_client_secrets_file(str(secret), SCOPES).run_local_server(port=0)
    token.parent.mkdir(parents=True, exist_ok=True)
    token.write_text(creds.to_json(), encoding="utf-8")
    os.chmod(token, 0o600)
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def walk(drive, fid: str, prefix: str = "") -> List[dict]:
    """Every file under a folder, depth first, with its relative path."""
    out, token = [], None
    while True:
        resp = drive.files().list(
            q=f"'{fid}' in parents and trashed = false", pageSize=1000, pageToken=token,
            fields="nextPageToken, files(id, name, mimeType, size, createdTime, videoMediaMetadata)",
            supportsAllDrives=True, includeItemsFromAllDrives=True,
        ).execute()
        for f in resp.get("files", []):
            rel = f"{prefix}{f['name']}"
            if f["mimeType"] == FOLDER:
                out += walk(drive, f["id"], rel + "/")
            else:
                out.append({**f, "path": rel, "size": int(f.get("size") or 0)})
        token = resp.get("nextPageToken")
        if not token:
            return out


def human(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return f"{n:.1f} {unit}"
        n /= 1024


def select(files: List[dict], videos_only: bool) -> List[dict]:
    prefixes = ("video/",) if videos_only else MEDIA_PREFIXES
    # Google Docs and other native files have no bytes to download, so they are always skipped.
    return [f for f in files if f["mimeType"].startswith(prefixes)]


def download(drive, f: dict, dest: Path) -> Optional[Path]:
    from googleapiclient.http import MediaIoBaseDownload

    target = dest / f["path"]
    if target.exists() and target.stat().st_size == f["size"]:
        print(f"  skip  {f['path']} (already here)")
        return None
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_name(target.name + ".part")
    with io.FileIO(partial, "wb") as fh:
        loader = MediaIoBaseDownload(fh, drive.files().get_media(fileId=f["id"], supportsAllDrives=True),
                                     chunksize=32 * 1024 * 1024)
        done = False
        while not done:
            status, done = loader.next_chunk()
            if status:
                print(f"\r  {int(status.progress() * 100):3d}%  {f['path']}", end="")
    partial.replace(target)
    print(f"\r  done  {f['path']}  ({human(f['size'])})")
    return target


def main(argv=None, drive=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--account", default="default", help="a name for the Google account, e.g. 'personal'")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("auth")
    for name in ("list", "fetch"):
        s = sub.add_parser(name)
        s.add_argument("folder", help="Drive folder URL or ID")
        s.add_argument("--videos-only", action="store_true")
        if name == "fetch":
            s.add_argument("--dest", type=Path, default=REPO_ROOT / "footage")
    args = p.parse_args(argv)

    if args.command == "auth":
        drive = get_service(args.account, interactive=True)
        about = drive.about().get(fields="user(emailAddress)").execute()
        print(f"Signed in to Drive as {about['user']['emailAddress']}")
        return 0

    drive = drive or get_service(args.account)
    fid = folder_id(args.folder)
    meta = drive.files().get(fileId=fid, fields="name", supportsAllDrives=True).execute()
    files = select(walk(drive, fid), args.videos_only)
    total = sum(f["size"] for f in files)
    print(f"{meta['name']}: {len(files)} media files, {human(total)}")
    if args.command == "list":
        for f in files:
            secs = int((f.get("videoMediaMetadata") or {}).get("durationMillis", 0)) // 1000
            length = f"  {secs // 60}:{secs % 60:02d}" if secs else ""
            print(f"  {f.get('createdTime', '')[:10]}  {human(f['size']):>9}{length}  {f['path']}")
        return 0
    dest = args.dest / meta["name"]
    for f in files:
        download(drive, f, dest)
    print(f"Footage in {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
