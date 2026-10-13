---
description: The weekly loop - learn from the audience, check trends, plan the week, and draft the anchor video and its Shorts
argument-hint: "[hours available this week]"
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, AskUserQuestion, Task, WebSearch, WebFetch
---

# /weekly Command

The whole loop, once a week. Each step writes files; nothing is uploaded or posted without the user's approval.

1. **/learn**: run the steps in `.claude/commands/learn.md` (skip replies until the end).
2. **/trend**: run the steps in `.claude/commands/trend.md`.
3. **Plan**: follow `.claude/skills/yt-plan/SKILL.md`. Ask for hours available (or use `$ARGUMENTS`)
   and what is already half-made. One anchor long video, one cheap one, Shorts cut from the anchor.
   Mark which language each upload is in, based on the language plan in `audience-learnings.md`.
4. **Research the anchor**: `/youtube-research "<anchor topic>"`.
5. **Draft the anchor**: `/youtube full "<anchor topic>"`. Script with `.claude/skills/yt-script`
   (hooks scored in English, then translated), title and thumbnail with `yt-package`, description
   with `yt-seo`, and the `learning-kit.md` described in CLAUDE.md. Narration is AI text-to-speech,
   so follow the TTS rules in `writing-style.md`. For code or trading videos, run the code first.
6. **Hand back**: the plan table, the draft folder, and the questions to answer before recording.

After the user records and uploads (or asks for an upload with `automation/ytapi.py upload`, which
is private by default): `/youtube publish`, `/youtube sync`, `/social video "<slug>"`, then
`/yt-shorts` on the transcript.
