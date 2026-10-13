#!/usr/bin/env python3
"""
voiceover.py - turn a finished script into ElevenLabs narration.

Usage:
  python automation/voiceover.py 03-YouTube/drafts/SLUG/script.md --dry-run      # see the narration text and size
  python automation/voiceover.py 03-YouTube/drafts/SLUG/script.md                # English
  python automation/voiceover.py 03-YouTube/drafts/SLUG/script-hi.md --lang hi   # Hindi
  python automation/voiceover.py 03-YouTube/drafts/SLUG/script-bn.md --lang bn   # Bengali

Only the spoken lines are sent: headings, [ON SCREEN: ...] and other bracketed directions, tables,
code blocks, quotes and markdown formatting are removed. The audio is written in parts (one per
paragraph group, so a bad take can be regenerated alone) plus one joined file, next to the script.

Needs ELEVENLABS_API_KEY in your environment (never in a committed file) and voiceover settings in
config.yaml. Every run that is not --dry-run spends ElevenLabs credits, roughly one per character.
"""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
API = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}?output_format={fmt}"

DEFAULTS = {
    "voice_id": "",
    # Model per language. Check https://elevenlabs.io/docs/models for current language support:
    # Multilingual v2 covers English and Hindi; Bengali needs a model that lists it (Eleven v3 does).
    "models": {"en": "eleven_multilingual_v2", "hi": "eleven_multilingual_v2", "bn": "eleven_v3"},
    "output_format": "mp3_44100_128",
    "max_chars": 2500,
    "stability": 0.5,
    "similarity_boost": 0.75,
}


def load_settings() -> dict:
    settings = dict(DEFAULTS)
    for path in (REPO_ROOT / "config.yaml", REPO_ROOT / "profile" / "config.yaml"):
        if path.exists():
            import yaml
            with open(path, encoding="utf-8") as fh:
                settings.update((yaml.safe_load(fh) or {}).get("voiceover") or {})
            break
    return settings


def narration(markdown: str) -> list:
    """Spoken paragraphs from a script: everything a viewer should hear, nothing they should only see."""
    text = re.sub(r"```.*?```", "", markdown, flags=re.S)        # code blocks
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)           # comments
    paragraphs, current = [], []
    for raw in text.splitlines():
        line = raw.strip()
        skip = (line.startswith(("#", "|", ">", "---", "- [", "* [")) or
                re.fullmatch(r"\[[^\]]*\]", line) or re.fullmatch(r"\(?\d{1,2}:\d{2}.*\)?", line))
        if not line or skip:
            if current:
                paragraphs.append(" ".join(current))
                current = []
            continue
        line = re.sub(r"\[[^\]]*\]", "", line)                    # inline [ON SCREEN: ...], [B-ROLL] ...
        line = re.sub(r"\*\*|__|\*|`", "", line)                  # emphasis and inline code marks
        line = re.sub(r"^[-*]\s+", "", line)                     # bullet marks
        line = re.sub(r"\s+", " ", line).strip()
        if line:
            current.append(line)
    if current:
        paragraphs.append(" ".join(current))
    return [p for p in paragraphs if re.search(r"\w", p)]


def group(paragraphs: list, max_chars: int) -> list:
    """Join paragraphs into requests under max_chars, never splitting a paragraph unless it alone is too long."""
    parts, buf = [], ""
    for p in paragraphs:
        pieces = [p] if len(p) <= max_chars else re.split(r"(?<=[.!?।])\s+", p)
        for piece in pieces:
            if buf and len(buf) + len(piece) + 2 > max_chars:
                parts.append(buf)
                buf = ""
            buf = f"{buf}\n\n{piece}" if buf else piece
    if buf:
        parts.append(buf)
    return parts


def synthesise(text: str, settings: dict, model: str, api_key: str) -> bytes:
    url = API.format(voice_id=settings["voice_id"], fmt=settings["output_format"])
    body = json.dumps({
        "text": text,
        "model_id": model,
        "voice_settings": {"stability": settings["stability"], "similarity_boost": settings["similarity_boost"]},
    }).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST", headers={
        "xi-api-key": api_key, "Content-Type": "application/json", "Accept": "audio/mpeg"})
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            return resp.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:300]
        sys.exit(f"ElevenLabs error {exc.code}: {detail}")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("script", type=Path)
    p.add_argument("--lang", default="en", choices=["en", "hi", "bn"])
    p.add_argument("--voice", help="ElevenLabs voice_id (default: voiceover.voice_id in config.yaml)")
    p.add_argument("--model", help="override the model for this run")
    p.add_argument("--only", type=int, help="regenerate only this part number")
    p.add_argument("--dry-run", action="store_true", help="print the narration and character count, spend nothing")
    args = p.parse_args(argv)

    settings = load_settings()
    if args.voice:
        settings["voice_id"] = args.voice
    model = args.model or settings["models"].get(args.lang, DEFAULTS["models"]["en"])
    parts = group(narration(args.script.read_text(encoding="utf-8")), int(settings["max_chars"]))
    chars = sum(len(x) for x in parts)
    print(f"{len(parts)} parts, {chars:,} characters, model {model}, language {args.lang}")

    if args.dry_run:
        for n, text in enumerate(parts, 1):
            print(f"\n--- part {n} ({len(text)} chars) ---\n{text}")
        return 0
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        sys.exit("Set ELEVENLABS_API_KEY in your environment (ElevenLabs -> Profile -> API keys).")
    if not settings["voice_id"]:
        sys.exit("Set voiceover.voice_id in config.yaml, or pass --voice VOICE_ID.")

    out_dir = args.script.parent / f"voiceover-{args.lang}"
    out_dir.mkdir(exist_ok=True)
    for n, text in enumerate(parts, 1):
        if args.only and n != args.only:
            continue
        audio = synthesise(text, settings, model, api_key)
        (out_dir / f"part-{n:02d}.mp3").write_bytes(audio)
        (out_dir / f"part-{n:02d}.txt").write_text(text, encoding="utf-8")
        print(f"  part {n}/{len(parts)}  {len(text)} chars -> {out_dir / f'part-{n:02d}.mp3'}")
    # MP3 frames concatenate cleanly, so the joined file plays straight through.
    joined = args.script.parent / f"voiceover-{args.lang}.mp3"
    with open(joined, "wb") as fh:
        for n in range(1, len(parts) + 1):
            part = out_dir / f"part-{n:02d}.mp3"
            if part.exists():
                fh.write(part.read_bytes())
    print(f"Joined: {joined}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
