# TubeFlow for Ayan Das (@ayandas9197)

This fork runs the YouTube channel https://www.youtube.com/@ayandas9197: computer science,
neuroscience, PhD research work, and motivation for students to do research. English, Hindi and Bengali.

## Read first, every time

- `writing-style.md`: voice and the rules for AI text-to-speech narration.
- `03-YouTube/channel-overview.md`: the four pillars and who the audience is.
- `03-YouTube/audience-learnings.md`: what the audience has asked for and done (written by `/learn`).
  Ideas that match it come before ideas that do not.

## The loop

`/learn` (audience data) -> `/trend` (niche outliers) -> `/weekly` (plan + drafts) -> record ->
`ytapi.py upload` (private) -> `/youtube publish` -> `/youtube sync` -> `/social video`.

Commands and agents here came from a self-hosting channel. Where they mention Docker, self-hosting,
open-source sponsorship or FUNDING.yml, skip that part. For this channel the equivalent is citing
papers properly: author, year and a link (DOI or arXiv) for every research claim.

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
