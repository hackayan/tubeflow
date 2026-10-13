#!/usr/bin/env python3
"""
footage.py - log a folder of travel footage, then assemble a rough cut from a shot list.

Usage:
  python automation/footage.py log footage/Trip --frames 3       # footage-log.md/json + still frames
  python automation/footage.py cut footage/Trip/shotlist.yaml    # rough-cut.mp4 from the shot list

LOG reads every video with ffprobe: when it was shot, how long it is, resolution, whether it has
sound, and the GPS tag if the camera wrote one, sorted into shooting order. With --frames it saves
still frames from each clip into frames/, so Claude can look at them and draft the story and the
shot list without anyone scrubbing through hours of footage.

CUT reads a shot list and joins the chosen ranges into one file in edit/ next to the shot list, every shot scaled to the same size
and frame rate (pad keeps the whole frame, crop fills it - crop is the one for vertical Shorts).
Clips with no sound get silence so the timeline stays in sync. It never changes the originals.

  output: rough-cut.mp4
  resolution: 1920x1080       # 1080x1920 for a Short
  fps: 30
  fit: pad                    # or crop
  shots:
    - {file: DJI_0012.MP4, in: 4.0, out: 11.5, note: "arrival, wide"}
    - {file: IMG_2231.MOV, in: 0, out: 6}

Needs ffmpeg and ffprobe on PATH.
"""

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List, Optional

VIDEO_EXT = {".mp4", ".mov", ".m4v", ".mkv", ".avi", ".mts", ".3gp", ".webm"}


def need(tool: str):
    if not shutil.which(tool):
        sys.exit(f"{tool} not found. Install ffmpeg (https://ffmpeg.org/download.html) and try again.")


def run(cmd: List[str]) -> str:
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        sys.exit(f"Command failed: {' '.join(cmd[:6])} ...\n{res.stderr[-800:]}")
    return res.stdout


def probe(path: Path) -> dict:
    info = json.loads(run(["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format",
                           "-show_streams", str(path)]))
    fmt = info.get("format", {})
    tags = {k.lower(): v for k, v in (fmt.get("tags") or {}).items()}
    video = next((s for s in info.get("streams", []) if s.get("codec_type") == "video"), {})
    rotate = int((video.get("tags") or {}).get("rotate", 0) or 0)
    for side in video.get("side_data_list", []) or []:
        rotate = int(side.get("rotation", rotate) or rotate)
    w, h = video.get("width", 0), video.get("height", 0)
    if abs(rotate) in (90, 270):
        w, h = h, w
    num, _, den = (video.get("avg_frame_rate") or "0/1").partition("/")
    return {
        "file": path.name,
        "duration": round(float(fmt.get("duration", 0) or 0), 2),
        "shot_at": tags.get("com.apple.quicktime.creationdate") or tags.get("creation_time", ""),
        "resolution": f"{w}x{h}",
        "orientation": "vertical" if h > w else "horizontal",
        "fps": round(float(num) / float(den), 2) if float(den or 0) else None,
        "audio": any(s.get("codec_type") == "audio" for s in info.get("streams", [])),
        "location": tags.get("com.apple.quicktime.location.iso6709") or tags.get("location", ""),
    }


def frames(path: Path, stem: str, duration: float, count: int, out_dir: Path) -> List[str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    names = []
    for i in range(count):
        t = duration * (i + 1) / (count + 1)
        name = f"{stem}_{i + 1}.jpg"
        run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", str(path), "-frames:v", "1",
             "-vf", "scale=480:-2", str(out_dir / name)])
        names.append(name)
    return names


def cmd_log(folder: Path, frame_count: int) -> List[dict]:
    need("ffprobe")
    clips = sorted(p for p in folder.rglob("*") if p.suffix.lower() in VIDEO_EXT
                   and not {"frames", "edit"} & set(p.relative_to(folder).parts))
    log = []
    for p in clips:
        entry = probe(p)
        entry["file"] = str(p.relative_to(folder))
        if frame_count:
            # Cameras reuse names (IMG_0001) across days, so the frame name carries the sub-folder too.
            stem = "__".join(p.relative_to(folder).with_suffix("").parts)
            entry["frames"] = frames(p, stem, entry["duration"], frame_count, folder / "frames")
        log.append(entry)
        print(f"  {entry['shot_at'][:16]:<16}  {entry['duration']:7.1f}s  {entry['orientation']:<10}  {entry['file']}")
    log.sort(key=lambda e: (e["shot_at"] or "~", e["file"]))
    (folder / "footage-log.json").write_text(json.dumps(log, indent=2), encoding="utf-8")
    total = sum(e["duration"] for e in log)
    lines = [f"# Footage log: {folder.name}", "",
             f"{len(log)} clips, {int(total // 60)} min {int(total % 60)} s in total, in shooting order.", "",
             "| # | Shot at | Length | Orientation | Sound | Location | File |",
             "|---|---------|--------|-------------|-------|----------|------|"]
    for n, e in enumerate(log, 1):
        lines.append(f"| {n} | {e['shot_at'][:16]} | {e['duration']:.1f}s | {e['orientation']} | "
                     f"{'yes' if e['audio'] else 'no'} | {e['location'] or '-'} | {e['file']} |")
    (folder / "footage-log.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{len(log)} clips, {total / 60:.1f} min -> {folder / 'footage-log.md'}")
    return log


def shot_filter(w: int, h: int, fps: float, fit: str) -> str:
    if fit == "crop":
        size = f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}"
    else:
        size = f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2"
    return f"{size},setsar=1,fps={fps},format=yuv420p"


def cmd_cut(shotlist: Path) -> Path:
    need("ffmpeg")
    need("ffprobe")
    import yaml

    spec = yaml.safe_load(shotlist.read_text(encoding="utf-8"))
    base = shotlist.parent
    w, h = (int(x) for x in str(spec.get("resolution", "1920x1080")).lower().split("x"))
    fps = float(spec.get("fps", 30))
    vf = shot_filter(w, h, fps, spec.get("fit", "pad"))
    out = base / "edit" / spec.get("output", "rough-cut.mp4")  # edit/ is never logged as footage
    out.parent.mkdir(exist_ok=True)
    shots = spec.get("shots") or []
    if not shots:
        sys.exit("The shot list has no shots.")
    with tempfile.TemporaryDirectory() as tmp:
        parts = []
        for n, shot in enumerate(shots, 1):
            src = base / shot["file"]
            if not src.exists():
                sys.exit(f"Shot {n}: {src} not found")
            start, end = float(shot.get("in", 0)), shot.get("out")
            length = (float(end) - start) if end is not None else probe(src)["duration"] - start
            if length <= 0:
                sys.exit(f"Shot {n}: out must be after in")
            part = Path(tmp) / f"{n:04d}.mp4"
            cmd = ["ffmpeg", "-v", "error", "-y", "-ss", f"{start:.3f}", "-t", f"{length:.3f}", "-i", str(src)]
            if probe(src)["audio"]:
                amap = ["-map", "0:v:0", "-map", "0:a:0"]
            else:  # silence keeps every part the same shape, so the parts join cleanly
                cmd += ["-f", "lavfi", "-t", f"{length:.3f}", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000"]
                amap = ["-map", "0:v:0", "-map", "1:a:0"]
            cmd += amap + ["-vf", vf, "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                           "-c:a", "aac", "-ar", "48000", "-ac", "2", "-b:a", "160k", "-shortest", str(part)]
            run(cmd)
            parts.append(part)
            print(f"  shot {n}/{len(shots)}  {length:5.1f}s  {shot['file']}  {shot.get('note', '')}")
        listing = Path(tmp) / "parts.txt"
        listing.write_text("".join(f"file '{p}'\n" for p in parts), encoding="utf-8")
        run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(listing), "-c", "copy",
             "-movflags", "+faststart", str(out)])
    print(f"Rough cut: {out} ({probe(out)['duration']:.1f}s)")
    return out


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="command", required=True)
    s = sub.add_parser("log")
    s.add_argument("folder", type=Path)
    s.add_argument("--frames", type=int, default=0, help="still frames to save per clip")
    s = sub.add_parser("cut")
    s.add_argument("shotlist", type=Path)
    args = p.parse_args(argv)
    if args.command == "log":
        cmd_log(args.folder, args.frames)
    else:
        cmd_cut(args.shotlist)
    return 0


if __name__ == "__main__":
    sys.exit(main())
