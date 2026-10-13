---
description: Make a travel vlog (and its Shorts) for the separate travel channel from a Google Drive footage folder
argument-hint: "<Drive folder URL or local footage folder>"
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, AskUserQuestion
---

# /travel Command

For the **travel channel** (profile `travel`), never the education channel. Read
`profile/travel/channel-overview.md` and `profile/travel/writing-style.md` first.

1. **Footage.** If `$ARGUMENTS` is a Drive link:
   ```bash
   python automation/drive_fetch.py --account personal list  "$ARGUMENTS" --videos-only
   python automation/drive_fetch.py --account personal fetch "$ARGUMENTS" --videos-only
   ```
   Show the size from `list` and ask before fetching more than a few GB.

2. **Log it.** `python automation/footage.py log footage/<folder> --frames 3`
   Read `footage-log.md` and look at the frames in `frames/` (Read each image). Write
   `footage/<folder>/scenes.md`: per clip, what is in it, how usable it is (shaky, dark, great), and
   anything said on camera.

3. **Ask the user** what they remember of the trip: where, when, why, what happened, costs. The
   footage cannot tell you these, and nothing here is invented.

4. **Story and shot list.** Draft the vlog as a journey (arrival, discovery, a turn, a payoff,
   leaving) in `footage/<folder>/story.md`, then write `footage/<folder>/shotlist.yaml` in the format
   in `automation/footage.py` (16:9, `fit: pad`), aiming for 8-15 minutes. Then up to three Shorts
   shot lists (`short-1.yaml`..., `resolution: 1080x1920`, `fit: crop`, under 60 s each).

5. **Rough cut.** `python automation/footage.py cut footage/<folder>/shotlist.yaml` (and each Short).
   The user refines it in their editor: this is a first assembly, not the finished video.

6. **Narration** for the parts with no talking: write `script.md` per `writing-style.md`, then
   `python automation/voiceover.py footage/<folder>/script.md --dry-run`, and generate it once approved.

7. **Package.** Title and thumbnail with `.claude/skills/yt-package` (place name plus promise),
   description with `yt-seo`, chapters with `yt-chapters` if there is a transcript. Write
   `footage/<folder>/meta.json` (see `automation/meta.example.json`, `category_id` 19).

8. **Upload, private, to the travel channel only:**
   `python automation/ytapi.py --profile travel upload footage/<folder>/edit/final.mp4 --meta footage/<folder>/meta.json`
