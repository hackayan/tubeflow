---
description: Learn from the audience - pull analytics, retention, search terms and comments from YouTube, then update the audience knowledge file that every idea and script is built from
argument-hint: "[days, default 28]"
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, AskUserQuestion
---

# /learn Command

Turn what the audience did and said into knowledge the next video is built from.

## Steps

1. **Pull a snapshot.**
   ```bash
   python automation/ytapi.py snapshot --days 28   # use the number in $ARGUMENTS instead of 28 if one was given
   ```
   If it says "Not signed in", tell the user to run `python automation/ytapi.py auth` and stop.
   The snapshot lands in `data/snapshots/YYYY-MM-DD/`: `videos.json`, `analytics-Nd.json`,
   `comments/channel.json`, and `retention/*.csv`.

2. **Retention.** For each CSV, run the yt-retention tool with the video's duration from `videos.json`:
   ```bash
   python3 .claude/skills/yt-retention/retention.py data/snapshots/DATE/retention/ID.csv --duration SECONDS
   ```
   Follow `.claude/skills/yt-retention/SKILL.md`: name the biggest leak per video and what was being
   said there (download the auto-captions if they exist and pass `--transcript`).

3. **Comments.** Follow `.claude/skills/yt-comment/SKILL.md` on `comments/channel.json`: triage into
   questions, corrections, praise and bait. Group repeated questions into topics. Note the language
   mix in `summary.languages`: it is the evidence for which videos get Hindi or Bengali versions.

4. **Demand.** From `analytics-Nd.json` read `search_terms` (what people typed before finding the
   channel), `traffic_sources`, `countries` and `age_gender`. Compare long videos against Shorts.

5. **Update the knowledge file** `03-YouTube/audience-learnings.md`. Edit it in place, never start over:
   - **What they ask for:** repeated questions and search terms, each with a count, newest first.
   - **What keeps them:** the openings and segments that held retention.
   - **What loses them:** the leaks, with the line that was being said.
   - **Who they are:** countries, age groups, language mix (numbers from the snapshot only).
   - **Language plan:** which videos to translate first, and why.
   - **Idea bank:** each question or search term that could be a video, with its evidence.
   - A dated changelog line at the bottom: what changed since the last /learn.

6. **Replies.** Draft replies to the unanswered questions in the creator's voice (yt-comment rules).
   Show them, ask which to post, and post only the approved ones with
   `python automation/ytapi.py reply COMMENT_ID --text "..." --yes`.

## Rules

- Never put a commenter's name or channel into `audience-learnings.md`. It may end up in a public repo.
- Never invent a number. Everything in the file comes from the snapshot.
- End with the three most important things learned, and the question: **ship it, or change it?**
