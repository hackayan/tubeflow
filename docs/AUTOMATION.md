# Channel automation (@ayandas9197)

How this fork runs the channel: what is automatic, what stays manual, and how to connect it all.
Everything runs on your own computer with Claude Code.

## What is automated, and what is not

| Step | How | Automatic? |
|------|-----|-----------|
| Learn from the audience (analytics, retention, search terms, comments, language mix) | `/learn` → `automation/ytapi.py snapshot` | Yes, read-only |
| Find what is working in the niche | `/trend` → `ytapi.py trends` + `yt-viral/swipe.py` | Yes, read-only |
| Plan the week, research, script, title, thumbnail text, description, chapters, Shorts | `/weekly`, `/youtube full`, `yt-*` skills | Drafts are automatic, you approve them |
| Voice-over | AI text-to-speech for now (see "AI voice" below) | You generate and edit it |
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

Then open `config.yaml` and fill the lines marked `TODO` (social links, voting repo, featured video).

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

## 5. AI voice

Narration is AI text-to-speech until you send your own recordings. `writing-style.md` makes scripts
TTS-friendly: short sentences, abbreviations spelled out, on-screen text kept out of the spoken lines.

- Any TTS tool works. ElevenLabs has a Claude connector, so Claude can generate the voice-over from a
  finished script if you connect it, and it spends your ElevenLabs credits.
- YouTube requires the "altered or synthetic content" disclosure for realistic synthetic content,
  for example a cloned voice of a real person. A clearly generic narration voice usually does not
  need it. If in doubt, set `"synthetic_media": true` in `meta.json`. Check YouTube's current policy.
- When you have your own voice: replace "How I actually talk" in `~/.claude/youtube/voice.md` with
  transcripts of your recordings, and set `voice.narration: "human"` in `config.yaml`.

## 6. Public video catalog and roadmap voting

1. Create a public repository for it, for example `hackayan/ayandas-videos`, and put its URL in
   `links.voting_repo`.
2. Install and sign in to the GitHub CLI: `gh auth login`.
3. `python .claude/scripts/create_issues.py` turns your roadmap into issues that viewers vote on with 👍.
4. `/youtube sync` adds each published video to the catalog and closes its roadmap issue.

Link the voting repo in your descriptions and pinned comments, so the audience can vote on the next
video. Add their votes to the idea bank in `audience-learnings.md`.

## 7. LinkedIn, X and Facebook

Claude does not log in to your social accounts, and you should never give it a password. `/social`
writes ready-to-paste posts for each platform into `04-Social/`. To publish them:

- **Simplest:** paste them yourself, or load them into a scheduler such as Buffer that is already
  connected to your accounts.
- **Fully automatic posting** would need each platform's developer API: a LinkedIn developer app
  approved for posting, a paid X API plan, and a Meta app with a Facebook Page token. This is not
  built yet; ask if you want it.

Put your profile URLs in `config.yaml` (`links.linkedin`, `links.twitter`, `links.facebook`) so they
appear in descriptions and posts.

## Privacy

- `data/` holds analytics and comments, including viewers' names. It is gitignored.
- `03-YouTube/`, `04-Social/` and `05-Templates/` are gitignored because this fork is public. Make the
  fork private if you want to commit your drafts.
- Never put email addresses or tokens in a file that gets committed.
