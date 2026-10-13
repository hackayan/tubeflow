#!/usr/bin/env python3
"""
plan.py - turn profile/series-plan.yaml into the files the rest of TubeFlow reads.

Usage:
  python automation/plan.py check                                   # validate the plan
  python automation/plan.py roadmap  --out ../ayandas-videos/roadmap.json   # for create_issues.py
  python automation/plan.py markdown --out ../ayandas-videos/SERIES.md      # readable series plan
"""

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PLAN = REPO_ROOT / "profile" / "series-plan.yaml"


def load_plan(path: Path = DEFAULT_PLAN) -> dict:
    try:
        import yaml
    except ImportError:
        sys.exit("PyYAML is required: pip install -r automation/requirements.txt")
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def check(plan: dict) -> list:
    """Return a list of problems: duplicate ids, unknown levels, broken builds_on links."""
    problems = []
    levels = {lv["id"] for lv in plan["levels"]}
    ids = {}
    for pl in plan["playlists"]:
        for lang in ("en", "hi", "bn"):
            if not pl["title"].get(lang):
                problems.append(f"{pl['id']}: missing {lang} playlist title")
        for ep in pl["episodes"]:
            if ep["id"] in ids:
                problems.append(f"duplicate episode id {ep['id']}")
            ids[ep["id"]] = ep
            if ep.get("level") not in levels:
                problems.append(f"{ep['id']}: unknown level {ep.get('level')}")
            if not ep.get("goal"):
                problems.append(f"{ep['id']}: no learning goal")
    for ep in ids.values():
        if ep.get("builds_on") and ep["builds_on"] not in ids:
            problems.append(f"{ep['id']}: builds_on {ep['builds_on']} does not exist")
    return problems


def to_roadmap(plan: dict) -> dict:
    """The roadmap.json shape that .claude/scripts/create_issues.py expects."""
    videos = []
    titles = {ep["id"]: ep["title"] for pl in plan["playlists"] for ep in pl["episodes"]}
    for pl in plan["playlists"]:
        total = len(pl["episodes"])
        for n, ep in enumerate(pl["episodes"], 1):
            notes = [f"You will learn to: {ep['goal']}"]
            if ep.get("builds_on"):
                notes.append(f"Watch first: {titles[ep['builds_on']]}.")
            if ep.get("notes"):
                notes.append(ep["notes"])
            videos.append({
                "id": ep["id"],
                "title": ep["title"],
                "category": pl["id"],
                "complexity": ep["level"],
                "series": True,
                "seriesInfo": f"{pl['title']['en']}, part {n} of {total}",
                "notes": " ".join(notes),
            })
    return {
        "lastUpdated": dt.date.today().isoformat(),
        "categories": [{"id": pl["id"], "name": pl["title"]["en"], "label": pl["label"], "color": pl["color"]}
                       for pl in plan["playlists"]],
        "complexityLabels": plan["levels"],
        "videos": videos,
    }


def to_markdown(plan: dict) -> str:
    lines = ["# Series plan", "",
             "Every playlist is a series taught in order. Vote for what you want first in the "
             "[roadmap](ROADMAP.md).", ""]
    titles = {ep["id"]: ep["title"] for pl in plan["playlists"] for ep in pl["episodes"]}
    for pl in plan["playlists"]:
        lines += [f"## {pl['title']['en']}", "",
                  f"*{pl['pillar']}* · {pl['title']['hi']} · {pl['title']['bn']}", "",
                  pl["description"].strip(), "",
                  "| # | Video | Level | You will learn to | Watch first |",
                  "|---|-------|-------|-------------------|-------------|"]
        for n, ep in enumerate(pl["episodes"], 1):
            lines.append(f"| {n} | {ep['title']} | {ep['level'].capitalize()} | {ep['goal']} | "
                         f"{titles.get(ep.get('builds_on'), '-')} |")
        shorts = [s for ep in pl["episodes"] for s in ep.get("shorts", [])]
        if shorts:
            lines += ["", "Shorts: " + " · ".join(shorts)]
        lines.append("")
    return "\n".join(lines)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("command", choices=["check", "roadmap", "markdown"])
    p.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    p.add_argument("--out", type=Path)
    args = p.parse_args(argv)
    plan = load_plan(args.plan)
    problems = check(plan)
    if problems or args.command == "check":
        for msg in problems:
            print(f"  x {msg}")
        episodes = sum(len(pl["episodes"]) for pl in plan["playlists"])
        print(f"{len(plan['playlists'])} playlists, {episodes} episodes, {len(problems)} problems")
        return 1 if problems else 0
    text = (json.dumps(to_roadmap(plan), indent=2, ensure_ascii=False) + "\n"
            if args.command == "roadmap" else to_markdown(plan))
    if args.out:
        args.out.write_text(text, encoding="utf-8")
        print(f"wrote {args.out}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
