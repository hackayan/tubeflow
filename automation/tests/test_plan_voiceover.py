"""Offline tests for plan.py, the playlists command and voiceover.py."""
import argparse
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import plan  # noqa: E402
import voiceover  # noqa: E402
import ytapi  # noqa: E402
from test_ytapi import FakeResource  # noqa: E402


class PlanTest(unittest.TestCase):
    def test_shipped_plan_is_valid(self):
        self.assertEqual(plan.check(plan.load_plan()), [])

    def test_roadmap_matches_create_issues_schema(self):
        road = plan.to_roadmap(plan.load_plan())
        cats = {c["id"] for c in road["categories"]}
        for key in ("id", "label", "color", "name"):
            self.assertIn(key, road["categories"][0])
        for v in road["videos"]:
            self.assertIn(v["category"], cats)
            self.assertIn(v["complexity"], {"beginner", "intermediate", "advanced"})
        self.assertEqual(len({v["id"] for v in road["videos"]}), len(road["videos"]))

    def test_check_finds_broken_links(self):
        bad = {"levels": [{"id": "beginner"}], "playlists": [{"id": "x", "title": {"en": "X", "hi": "", "bn": "B"},
               "episodes": [{"id": "a", "level": "expert", "goal": "g", "builds_on": "nope"}]}]}
        problems = " ".join(plan.check(bad))
        for part in ("missing hi", "unknown level", "nope does not exist"):
            self.assertIn(part, problems)


class PlaylistsTest(unittest.TestCase):
    def run_cmd(self, yes):
        calls = []
        yt = {"playlists.list": lambda kw: {"items": [{"id": "PL1", "snippet": {"title": "Neuroscience from Zero"}}]},
              "playlists.insert": lambda kw: {"id": "NEW"}}
        with tempfile.TemporaryDirectory() as tmp:
            settings = dict(ytapi.DEFAULTS, data_dir=tmp, languages={"primary": "en"})
            clients = ytapi.Clients(settings, youtube=FakeResource(yt, calls))
            args = argparse.Namespace(plan=str(plan.DEFAULT_PLAN), privacy="private", yes=yes)
            with mock.patch("sys.stdout", new=io.StringIO()):
                ytapi.cmd_playlists(clients, args)
        return [kw for name, kw in calls if name == "playlists.insert"]

    def test_dry_run_creates_nothing(self):
        self.assertEqual(self.run_cmd(yes=False), [])

    def test_creates_only_missing_private_with_localizations(self):
        inserts = self.run_cmd(yes=True)
        self.assertEqual(len(inserts), 5)  # one of six already exists
        body = inserts[0]["body"]
        self.assertEqual(body["status"]["privacyStatus"], "private")
        self.assertEqual(set(body["localizations"]), {"hi", "bn"})


class VoiceoverTest(unittest.TestCase):
    SCRIPT = ("# Title\n\n## Hook (0:00)\n\n**Hello** there. [ON SCREEN: x]\nSecond line.\n\n"
              "[B-ROLL]\n\n```python\ncode()\n```\n\n| a | b |\n\n- bullet one\n\n(0:45)\n\nবাংলা বাক্য।\n")

    def test_narration_keeps_only_spoken_lines(self):
        self.assertEqual(voiceover.narration(self.SCRIPT), ["Hello there. Second line.", "bullet one", "বাংলা বাক্য।"])

    def test_group_respects_limit_and_splits_long_paragraphs(self):
        parts = voiceover.group(["a" * 50, "b" * 50, "Sentence one. " * 20], 120)
        self.assertTrue(all(len(p) <= 120 for p in parts))
        self.assertEqual("".join(parts).count("Sentence one."), 20)

    def test_run_writes_parts_and_joined_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp) / "script.md"
            script.write_text(self.SCRIPT, encoding="utf-8")
            sent = []

            def fake_urlopen(req, timeout):
                sent.append((req.full_url, json.loads(req.data), req.headers))
                return io.BytesIO(b"MP3")
            with mock.patch.dict("os.environ", {"ELEVENLABS_API_KEY": "k"}), \
                    mock.patch("urllib.request.urlopen", fake_urlopen), \
                    mock.patch("sys.stdout", new=io.StringIO()):
                voiceover.main([str(script), "--lang", "bn", "--voice", "VOICE"])
            self.assertEqual((Path(tmp) / "voiceover-bn.mp3").read_bytes(), b"MP3")
            url, body, headers = sent[0]
            self.assertIn("/text-to-speech/VOICE", url)
            self.assertEqual(body["model_id"], "eleven_v3")
            self.assertEqual(headers["Xi-api-key"], "k")

    def test_no_key_no_spend(self):
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp) / "s.md"
            script.write_text("Hello.", encoding="utf-8")
            with mock.patch.dict("os.environ", {}, clear=True), mock.patch("sys.stdout", new=io.StringIO()):
                with self.assertRaises(SystemExit):
                    voiceover.main([str(script), "--voice", "V"])


if __name__ == "__main__":
    unittest.main()
