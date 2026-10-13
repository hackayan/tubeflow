---
description: Find what is working right now in the channel's niche, ranked by how far each video beat its own channel, matched against what our own audience asks for
argument-hint: "[query ...] (default: youtube_api.trend_queries in config.yaml)"
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, WebSearch, WebFetch, Task
---

# /trend Command

1. **Collect.** For English, then again for Hindi and Bengali audiences when useful:
   ```bash
   python automation/ytapi.py trends $ARGUMENTS
   python automation/ytapi.py trends $ARGUMENTS --lang hi --region IN
   python automation/ytapi.py trends $ARGUMENTS --lang bn --region BD
   ```
   Each query costs about 100 of the 10,000 free daily API units. Do not run more than about 30 queries a day.

2. **Rank.** Follow `.claude/skills/yt-viral/SKILL.md`:
   ```bash
   python3 .claude/skills/yt-viral/swipe.py data/trends/DATE-collected.json --min 2.0
   ```

3. **Match against the audience.** Read `03-YouTube/audience-learnings.md`. A trend that matches
   something our own viewers asked for or searched beats a bigger trend they never mentioned. Score
   each candidate on: outlier multiple, audience evidence, fit with the four pillars in
   `03-YouTube/channel-overview.md`, and whether it can be made honestly (citable sources, real PhD
   experience).

4. **Write** `03-YouTube/research/YYYY-MM-DD-trends.md`: the top five outliers with multiple and
   formula, the one structural thing they share, and the three ideas worth making, each with its
   evidence and a working title linted by `.claude/skills/yt-package/title.py`.

5. Offer to run `/youtube-research "<idea>"` on the best one.
