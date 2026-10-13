# TubeFlow for Ayan Das (@ayandas9197)

This fork runs the YouTube channel https://www.youtube.com/@ayandas9197, an education channel:
science and technology, engineering, data analysis, algorithmic trading, interdisciplinary research
(including the creator's PhD work in the computational neuroscience of psychosis) and learning
skills. The goal is that students learn things correctly and are motivated to keep learning.
English, Hindi and Bengali.

## Read first, every time

- `writing-style.md`: voice, teaching rules, and the rules for AI text-to-speech narration.
- `03-YouTube/channel-overview.md`: the six pillars, the audience and the teaching promise.
- `03-YouTube/audience-learnings.md`: what the audience has asked for and done (written by `/learn`).
  Ideas that match it come before ideas that do not.

## The loop

`/learn` (audience data) -> `/trend` (niche outliers) -> `/weekly` (plan + drafts) ->
`automation/voiceover.py` (ElevenLabs narration) -> edit -> `ytapi.py upload` (private) ->
`/youtube publish` -> `/youtube sync` -> `/social video`.

Commands and agents here came from a self-hosting channel. Where they mention Docker, self-hosting,
open-source sponsorship or FUNDING.yml, skip that part. For this channel the equivalent is citing
papers properly: author, year and a link (DOI or arXiv) for every research claim.

## Playlists and series

`profile/series-plan.yaml` is the plan: six playlists, each a series taught in order. A new video
idea either fits a series (in its `builds_on` order) or is a stand-alone video that the audience
asked for. When a series changes, edit that file, run `python automation/plan.py check`, then
regenerate the voting roadmap (docs/AUTOMATION.md).

## Every long video gets a learning kit

Next to `script.md` in the draft folder, write `learning-kit.md`:

- the learning goal (one sentence) and the prerequisites, each with a link;
- the misconception the video corrects;
- two or three "pause and think" questions with their answers;
- one exercise with its solution (for code: the repo path and how to run it);
- the sources used (author, year, DOI/arXiv/official docs link) and the one thing to read next.

The description and pinned comment draw on it. Shorts link back to the long video that has the kit.

## Accuracy before speed

- Check every fact against a primary source and list it in the learning kit. If a claim cannot be
  checked, cut it or mark it as opinion.
- Run code before it goes in a script. Never write output you did not get.
- Psychosis and mental health: follow "Mental health and psychosis" in `writing-style.md`
  (person-first language, no medical advice, theories labelled as theories, helpline line).
- Algorithmic trading and finance: education only. Follow the rules in `writing-style.md`
  (disclaimer, no profit claims, costs and biases shown, no buy or sell calls).

## Unset links

A `{{CONFIGURE_SOMETHING}}` left in a template means that link is not set in config.yaml. Drop the
whole line from anything you write (description, pinned comment, social post). Never print the placeholder.

## Never

- Publish, upload public, post a reply or post on social media without the user saying yes to that
  specific item. `ytapi.py upload` is private by default; `ytapi.py reply` is a dry run without `--yes`.
- Invent a number, a study, a citation or a result. Ask, or leave it out.
- Describe unpublished lab work beyond what the user has said can be shared.
- Write a commenter's name, or anything from `data/`, into a file that gets committed. `data/` is gitignored.
- Ask for or store a password. YouTube access is OAuth through `automation/ytapi.py auth` only.
