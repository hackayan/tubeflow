"""Offline tests for the travel pipeline: channel profiles, Drive fetch and footage.py (needs ffmpeg)."""
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import drive_fetch  # noqa: E402
import footage  # noqa: E402
import ytapi  # noqa: E402
from test_ytapi import FakeResource  # noqa: E402


class ProfileTest(unittest.TestCase):
    def test_main_and_travel_never_share_token_or_data(self):
        main, travel = ytapi.load_config(), ytapi.load_config("travel")
        self.assertNotEqual(main["token_file"], travel["token_file"])
        self.assertNotEqual(main["data_dir"], travel["data_dir"])
        self.assertIn("india travel vlog", travel["trend_queries"])

    def test_unknown_profile_stops(self):
        with self.assertRaises(SystemExit):
            ytapi.load_config("no-such-channel")


class DriveFetchTest(unittest.TestCase):
    FILES = {
        "ROOT": [{"id": "D1", "name": "Day 1", "mimeType": drive_fetch.FOLDER},
                 {"id": "V1", "name": "IMG_0001.MOV", "mimeType": "video/quicktime", "size": "3"},
                 {"id": "G1", "name": "notes", "mimeType": "application/vnd.google-apps.document"}],
        "D1": [{"id": "V2", "name": "IMG_0001.MOV", "mimeType": "video/quicktime", "size": "5"},
               {"id": "P1", "name": "photo.jpg", "mimeType": "image/jpeg", "size": "2"}],
    }

    def fake_drive(self):
        files = self.FILES
        return FakeResource({
            "files.list": lambda kw: {"files": files[kw["q"].split("'")[1]]},
            "files.get": lambda kw: {"name": "Trip"},
        }, [])

    def test_folder_id_from_url(self):
        url = "https://drive.google.com/drive/folders/1Mmz7OMDG7TVs968Sor5nJb5xqUv0jQp0?usp=sharing"
        self.assertEqual(drive_fetch.folder_id(url), "1Mmz7OMDG7TVs968Sor5nJb5xqUv0jQp0")
        self.assertEqual(drive_fetch.folder_id("abc_-1"), "abc_-1")

    def test_walk_keeps_subfolders_and_skips_google_docs(self):
        files = drive_fetch.walk(self.fake_drive(), "ROOT")
        self.assertEqual([f["path"] for f in drive_fetch.select(files, videos_only=False)],
                         ["Day 1/IMG_0001.MOV", "Day 1/photo.jpg", "IMG_0001.MOV"])
        self.assertEqual(len(drive_fetch.select(files, videos_only=True)), 2)

    def test_list_downloads_nothing(self):
        out = io.StringIO()
        with mock.patch("sys.stdout", out), mock.patch.object(drive_fetch, "download") as dl:
            drive_fetch.main(["list", "ROOT"], drive=self.fake_drive())
        dl.assert_not_called()
        self.assertIn("Trip: 3 media files", out.getvalue())


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "ffmpeg not installed")
class FootageTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        (self.dir / "day1").mkdir()
        (self.dir / "day2").mkdir()

        def make(path, size, audio, when):
            cmd = ["ffmpeg", "-v", "error", "-f", "lavfi", "-i", f"testsrc=size={size}:rate=25"]
            cmd += ["-f", "lavfi", "-i", "sine"] if audio else []
            cmd += ["-t", "3", "-metadata", f"creation_time={when}", "-c:v", "libx264"]
            cmd += ["-c:a", "aac", "-shortest"] if audio else []
            subprocess.run(cmd + [str(path)], check=True)
        make(self.dir / "day1" / "IMG_0001.mp4", "640x360", True, "2025-12-02T10:00:00Z")
        make(self.dir / "day2" / "IMG_0001.mp4", "360x640", False, "2025-12-01T10:00:00Z")

    def tearDown(self):
        self.tmp.cleanup()

    def test_log_orders_by_time_and_names_frames_uniquely(self):
        with mock.patch("sys.stdout", new=io.StringIO()):
            log = footage.cmd_log(self.dir, 1)
        self.assertEqual([e["file"] for e in log], ["day2/IMG_0001.mp4", "day1/IMG_0001.mp4"])
        self.assertEqual(log[0]["orientation"], "vertical")
        self.assertFalse(log[0]["audio"])
        self.assertEqual(len(list((self.dir / "frames").glob("*.jpg"))), 2)
        self.assertEqual(len(json.loads((self.dir / "footage-log.json").read_text())), 2)

    def test_cut_joins_mixed_clips_and_is_not_logged_as_footage(self):
        (self.dir / "s.yaml").write_text(
            "output: rc.mp4\nresolution: 1280x720\nfps: 30\nshots:\n"
            "  - {file: day2/IMG_0001.mp4, in: 0.5, out: 2.5}\n  - {file: day1/IMG_0001.mp4, in: 1}\n")
        with mock.patch("sys.stdout", new=io.StringIO()):
            out = footage.cmd_cut(self.dir / "s.yaml")
            info = footage.probe(out)
            self.assertAlmostEqual(info["duration"], 4.0, delta=0.3)
            self.assertEqual(info["resolution"], "1280x720")
            self.assertTrue(info["audio"])
            self.assertEqual(len(footage.cmd_log(self.dir, 0)), 2)


if __name__ == "__main__":
    unittest.main()
