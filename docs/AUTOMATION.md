# Channel automation (@ayandas9197)

How this fork runs the channel: what is automatic, what stays manual, and how to connect it all.
Everything runs on your own computer with Claude Code.

## What is automated, and what is not

| Step | How | Automatic? |
|------|-----|-----------|
| Learn from the audience (analytics, retention, search terms, comments, language mix) | `/learn` → `automation/ytapi.py snapshot` | Yes, read-only |
| Find what is working in the niche | `/trend` → `ytapi.py trends` + `yt-viral/swipe.py` | Yes, read-only |
| Plan the week, research, script, title, thumbnail text, description, chapters, Shorts | `/weekly`, `/youtube full`, `yt-*` skills | Drafts are automatic, you approve them |
| Playlists and series | `profile/series-plan.yaml` → `ytapi.py playlists --yes` (created private) | When you run it |
| Voice-over | ElevenLabs via `automation/voiceover.py` (see "AI voice" below) | When you run it; you check the audio |
| Edit the video | `/yt-edit` writes the cut list; you edit | Manual |
| Upload | `ytapi.py upload` (private by default) or YouTube Studio | Only when you run it |
| Reply to comments | `/learn` drafts replies; `ytapi.py reply --yes` posts the ones you approve | Only when you approve |
| Public video catalog + roadmap voting | `/youtube sync`, `.claude/scripts/create_issues.py` | When you run it |
| LinkedIn, X, Facebook | `/social video "<slug>"` writes the posts | You post them (see below) |

Nothing publishes, goes public or gets posted without you saying yes to that item.

## 1. Install (once)

You need Python 3.10+, Git and [Claude Code](https://claude.ai/code).
On Windows, use WSL2 or Git Bash for the setup script.

```bash
git clone https://github.com/hackayan/tubeflow.git
git clone https://github.com/hackayan/youtube-agent-skill.git
cd tubeflow
./setup-channel.sh
```

The script creates `.venv`, installs `automation/requirements.txt`, copies the eleven `yt-*` skills in,
copies your profile (`profile/`) into place and fills the template placeholders.

Then open `config.yaml` and fill the lines marked `TODO` (X link, ElevenLabs voice ID, featured video).

## 2. Connect YouTube (once, about 10 minutes)

YouTube access is OAuth: you sign in on Google's own page in your browser and approve access. Your
password never reaches this tool or Claude. The resulting token stays in `~/.config/tubeflow/`.

1. Go to https://console.cloud.google.com/ and create a project (for example "tubeflow").
2. **APIs & Services → Library**: enable **YouTube Data API v3** and **YouTube Analytics API**.
3. **APIs & Services → OAuth consent screen**: user type **External**. Add your channel's Google
   account under **Test users**.
4. **Credentials → Create credentials → OAuth client ID**, type **Desktop app**. Download the JSON and
   save it as `~/.config/tubeflow/client_secret.json`.
5. Run:
   ```bash
   source .venv/bin/activate
   python automation/ytapi.py auth
   ```
   Sign in with the account that owns the channel. If the channel is a Brand Account, pick the
   channel when Google asks. The script prints the channel name when it works.

While the consent screen is in **Testing**, Google expires the sign-in after 7 days and you have to
run `auth` again. To stop that, click **Publish app** on the consent screen. You will see an
"unverified app" warning when signing in; that is expected for a tool only you use.

### Upload limits you should know about

- Google locks videos uploaded through the API to **private** until the Cloud project passes YouTube's
  API compliance audit. Until then, use `ytapi.py upload` for private review copies and publish from
  YouTube Studio, or apply for the audit at
  https://support.google.com/youtube/contact/yt_api_form.
- The free quota is 10,000 units a day. A search costs 100 (so `/trend` with 7 queries is about 700).
  Uploads are the most expensive call, so a few a day is the practical limit.

To revoke access at any time: https://myaccount.google.com/permissions

## 3. Weekly use

```text
/learn          what the audience did and asked for -> 03-YouTube/audience-learnings.md
/trend          niche outliers matched against what your audience asks for
/weekly         learn + trend + plan + draft the anchor video
/youtube full "topic"      the full package for one video
/yt-shorts      Shorts from a long video's transcript
```

After recording:

```bash
python automation/ytapi.py upload video.mp4 --meta meta.json        # private
```

`automation/meta.example.json` shows the fields, including Hindi and Bengali title and description
(`localizations`), a scheduled `publish_at`, and the thumbnail.

Then run `/youtube publish "topic"`, `/youtube sync` and `/social video "slug"`.

## 4. Languages

- Scripts default to English. `/learn` records the language mix of your comments and the countries
  watching, and keeps a "language plan" saying which videos to make in Hindi or Bengali next.
- Hooks and titles are scored in English and then translated: the scoring tools only read English
  and warn you when given Hindi or Bengali text.
- One upload can carry titles and descriptions in all three languages (`localizations`). For audio
  in each language, make separate videos, or add translated captions.

## 5. AI voice (ElevenLabs)

Narration is ElevenLabs text-to-speech until you send your own recordings. `writing-style.md` makes
scripts TTS-friendly: short sentences, abbreviations spelled out, on-screen text kept out of the
spoken lines.

1. In ElevenLabs, create an API key (Profile → API keys) and put it in your shell, not in a file
   that gets committed: `export ELEVENLABS_API_KEY=...` (add it to `~/.bashrc` or `~/.zshrc`).
2. Pick a voice in the Voice Library, copy its Voice ID into `voiceover.voice_id` in `config.yaml`.
   Try it in Hindi and Bengali too before you commit to it.
3. Check `voiceover.models`: Multilingual v2 covers English and Hindi; Bengali needs a model that
   lists it (Eleven v3 does at the time of writing). The ElevenLabs models page has the current list.
4. Generate:
   ```bash
   python automation/voiceover.py 03-YouTube/drafts/SLUG/script.md --dry-run   # free: shows exactly what is read
   python automation/voiceover.py 03-YouTube/drafts/SLUG/script.md             # English
   python automation/voiceover.py 03-YouTube/drafts/SLUG/script-hi.md --lang hi
   python automation/voiceover.py 03-YouTube/drafts/SLUG/script.md --only 3    # redo one part
   ```
   You get `voiceover-en/part-NN.mp3` (one per section, to fix a part alone) and a joined
   `voiceover-en.mp3`. Each run spends about one ElevenLabs credit per character, so use `--dry-run` first.

YouTube requires the "altered or synthetic content" disclosure for realistic synthetic content, for
example a cloned voice of a real person. A generic ElevenLabs voice narrating slides usually does
not need it; a clone of your own or anyone's voice presented as real speech may. If in doubt, set
`"synthetic_media": true` in `meta.json`, and check YouTube's current policy.

When you have your own voice: replace "How I actually talk" in `~/.claude/youtube/voice.md` with
transcripts of your recordings, and set `voice.narration: "human"` in `config.yaml`.

## 6. Playlists and series

`profile/series-plan.yaml` holds six playlists, one per pillar, each a series of 7-8 videos in
teaching order, with English, Hindi and Bengali playlist titles (have the translations checked).

```bash
python automation/plan.py check                 # validate after editing the plan
python automation/ytapi.py playlists            # dry run: lists what would be created
python automation/ytapi.py playlists --yes      # creates the missing playlists, private
```

Make each playlist public in YouTube Studio when its first video goes live, so nobody lands on an
empty playlist. When you upload a video, add it to its playlist in Studio.

## 7. Public video catalog and roadmap voting

The catalog lives in https://github.com/hackayan/ayandas-videos: `VIDEOS.md` (published videos),
`SERIES.md` (the plan) and `roadmap.json`, which becomes one issue per planned video that viewers
vote on with 👍.

1. Install and sign in to the GitHub CLI: `gh auth login`.
2. Clone the catalog next to this repo: `git clone https://github.com/hackayan/ayandas-videos.git`
3. Open the vote issues (once, and again after you change the plan):
   ```bash
   cd ../ayandas-videos
   python ../tubeflow/automation/plan.py roadmap --out roadmap.json
   python ../tubeflow/automation/plan.py markdown --out SERIES.md
   python ../tubeflow/.claude/scripts/create_issues.py --dry-run    # check first
   python ../tubeflow/.claude/scripts/create_issues.py              # creates labels, issues, ROADMAP.md
   git add -A && git commit -m "Update roadmap" && git push
   ```
4. `/youtube sync` adds each published video to `VIDEOS.md` and closes its roadmap issue.

Link the roadmap in descriptions and pinned comments ("vote for the next video"). `/learn` reads
the votes into the idea bank alongside comments and search terms.

## 8. LinkedIn, X and Facebook

Claude does not log in to your social accounts, and you should never give it a password. `/social`
writes ready-to-paste posts for each platform into `04-Social/`. To publish them:

- **Simplest:** paste them yourself, or load them into a scheduler such as Buffer that is already
  connected to your accounts.
- **Fully automatic posting** would need each platform's developer API: a LinkedIn developer app
  approved for posting, a paid X API plan, and a Meta app with a Facebook Page token. This is not
  built yet; ask if you want it.

Your LinkedIn and Facebook links are in `config.yaml`. Add your X profile to `links.twitter` if you
want X links too.

## 9. Travel vlog channel (separate channel)

Travel vlogs go on their own channel, so each audience gets what it subscribed for. Everything here
works for both channels; `--profile travel` picks the travel one, with its own sign-in, data folder
(`data/travel/`) and settings (`profile/travel/config.yaml`).

### Create the channel (you do this once, on YouTube)

YouTube does not allow channels to be created through its API, so this step is yours:

1. Sign in to YouTube with your Google account, open **Settings → Add or manage your channel(s) →
   Create a channel**. This makes a second channel (a Brand Account) under the same Google account.
2. Name it, add a picture and banner, and note its `@handle`.
3. Put the name, handle and link into `profile/travel/config.yaml` (the lines marked TODO).

### Connect it

```bash
python automation/ytapi.py --profile travel auth      # pick the TRAVEL channel when Google asks
```

### Footage from Google Drive

1. In the same Google Cloud project, also enable the **Google Drive API**.
2. Sign in with the Google account that has the footage (read-only access):
   ```bash
   python automation/drive_fetch.py --account personal auth
   python automation/drive_fetch.py --account personal list "<Drive folder link>" --videos-only
   python automation/drive_fetch.py --account personal fetch "<Drive folder link>" --videos-only
   ```
   Footage lands in `footage/<folder name>/` (gitignored). Re-running skips what is already there.

### Make the vlog

In Claude Code: `/travel "<Drive folder link>"`. It downloads, logs the clips (`footage.py log`
with still frames Claude can look at), asks you what happened on the trip, drafts the story and a
shot list, assembles a rough cut and up to three vertical Shorts (`footage.py cut`), writes the
narration for ElevenLabs, packages title, thumbnail text and description, and uploads privately
to the travel channel. The rough cut is a first assembly; finish it in your editor.

Needs ffmpeg: `brew install ffmpeg` (Mac), `sudo apt install ffmpeg` (Linux/WSL), or
https://ffmpeg.org/download.html (Windows).

## Privacy

- `data/` holds analytics and comments, including viewers' names. It is gitignored.
- `footage/` holds downloaded travel footage. It is gitignored.
- `03-YouTube/`, `04-Social/` and `05-Templates/` are gitignored because this fork is public. Make the
  fork private if you want to commit your drafts.
- Never put email addresses or tokens in a file that gets committed.
