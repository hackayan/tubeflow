#!/usr/bin/env bash
# One-time setup of this TubeFlow fork for the @ayandas9197 channel, on your own computer.
# Safe to re-run: it never overwrites your config, voice files or audience-learnings.md.
#
#   ./setup-channel.sh
#
# Then follow docs/AUTOMATION.md to connect YouTube (Google Cloud OAuth client + `ytapi.py auth`).
set -euo pipefail
cd "$(dirname "$0")"
ROOT="$PWD"
SKILL_REPO="${SKILL_REPO:-https://github.com/hackayan/youtube-agent-skill.git}"
SKILL_BRANCH="${SKILL_BRANCH:-}"

say() { printf '\n==> %s\n' "$*"; }
copy_once() { # copy_once SRC DEST: copy unless DEST already exists
  if [ -e "$2" ]; then echo "  keep  $2 (already exists)"; else mkdir -p "$(dirname "$2")"; cp "$1" "$2"; echo "  new   $2"; fi
}

say "Python environment (.venv)"
command -v python3 >/dev/null || { echo "python3 is required (3.10+)"; exit 1; }
[ -d .venv ] || python3 -m venv .venv
# shellcheck disable=SC1091
if [ -f .venv/bin/activate ]; then . .venv/bin/activate; else . .venv/Scripts/activate; fi
python -m pip install -q --upgrade pip
python -m pip install -q -r automation/requirements.txt
echo "  installed automation/requirements.txt"

say "youtube-agent-skill (the yt-* skills and their tools)"
if [ -d ../youtube-agent-skill/skills ]; then
  SKILLS_DIR="../youtube-agent-skill/skills"
  echo "  using ../youtube-agent-skill"
else
  TMP="$(mktemp -d)"
  git clone -q --depth 1 ${SKILL_BRANCH:+--branch "$SKILL_BRANCH"} "$SKILL_REPO" "$TMP/youtube-agent-skill"
  SKILLS_DIR="$TMP/youtube-agent-skill/skills"
  echo "  cloned $SKILL_REPO"
fi
for d in "$SKILLS_DIR"/yt-*; do
  rm -rf ".claude/skills/$(basename "$d")"
  cp -R "$d" .claude/skills/
done
echo "  copied $(ls -d "$SKILLS_DIR"/yt-* | wc -l | tr -d ' ') skills into .claude/skills/"

say "Channel profile"
copy_once profile/config.yaml config.yaml
copy_once profile/writing-style.md writing-style.md
copy_once profile/channel-overview.md channel-overview.md
copy_once profile/channel-overview.md 03-YouTube/channel-overview.md
copy_once profile/voice.md "$HOME/.claude/youtube/voice.md"

say "Folders"
for d in 03-YouTube/ideas 03-YouTube/drafts 03-YouTube/published 03-YouTube/research \
         04-Social/linkedin 04-Social/twitter 04-Social/facebook 05-Templates data; do
  mkdir -p "$d"
done
cp -n templates/*.md 05-Templates/ 2>/dev/null || true
[ -f 03-YouTube/youtube-index.json ] || echo '{"videos": []}' > 03-YouTube/youtube-index.json
if [ ! -f 03-YouTube/audience-learnings.md ]; then
  cat > 03-YouTube/audience-learnings.md <<'MD'
# Audience learnings: @ayandas9197

Written and updated by /learn from YouTube data. Do not put commenter names here.

## What they ask for
## What keeps them
## What loses them
## Who they are
## Language plan
## Idea bank

## Changelog
MD
  echo "  new   03-YouTube/audience-learnings.md"
fi

say "Filling {{PLACEHOLDERS}} in agents, commands and templates from config.yaml"
python .claude/scripts/process_templates.py config.yaml "$ROOT"

say "Done"
cat <<'TXT'
Next:
  1. Fill the TODO lines in config.yaml (X link, ElevenLabs voice ID), then re-run the placeholders:
       git checkout -- .claude/agents .claude/commands .claude/skills templates && ./setup-channel.sh
  2. Connect YouTube: docs/AUTOMATION.md, section "Connect YouTube" (about 10 minutes, once).
  3. Open Claude Code here and run /learn, then /weekly.
TXT
