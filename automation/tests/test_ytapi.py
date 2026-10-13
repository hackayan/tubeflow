"""Offline tests for ytapi.py against a fake YouTube API. Run: python -m unittest discover automation/tests"""
import argparse
import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import ytapi  # noqa: E402


class Call:
    def __init__(self, result):
        self.result = result

    def execute(self):
        return self.result


class FakeResource:
    """fake.<resource>().<method>(**kw).execute() -> handler(kw); every call is recorded."""

    def __init__(self, handlers, calls):
        self.handlers, self.calls = handlers, calls

    def __getattr__(self, resource):
        def res():
            outer = self

            class Methods:
                def __getattr__(self, method):
                    def call(**kw):
                        outer.calls.append((f"{resource}.{method}", kw))
                        return Call(outer.handlers[f"{resource}.{method}"](kw))
                    return call
            return Methods()
        return res


def video(vid, channel="Other", seconds="PT10M", views=100):
    return {"id": vid, "snippet": {"channelTitle": channel, "channelId": channel, "title": f"t {vid}",
                                   "publishedAt": "2026-10-01T00:00:00Z"},
            "contentDetails": {"duration": seconds}, "statistics": {"viewCount": str(views)}}


class YtapiTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.settings = dict(ytapi.DEFAULTS, data_dir=self.tmp.name, languages={"primary": "en", "also": ["hi", "bn"]})
        self.calls = []
        yt = {
            "channels.list": lambda kw: {"items": [{"id": "ME", "snippet": {"title": "Ayan Das"},
                                                   "contentDetails": {"relatedPlaylists": {"uploads": "UU" + kw.get("id", "ME").split(",")[0]}}}]},
            "playlistItems.list": lambda kw: {"items": [{"contentDetails": {"videoId": f"{kw['playlistId']}-{i}"}} for i in range(4)]},
            "videos.list": lambda kw: {"items": [video(i, seconds="PT45S" if i.endswith("-3") else "PT12M", views=100 * (n + 1))
                                                 for n, i in enumerate(kw["id"].split(","))]},
            "commentThreads.list": lambda kw: {"items": [
                {"snippet": {"videoId": "v1", "totalReplyCount": 1,
                             "topLevelComment": {"id": "c1", "snippet": {"textDisplay": "How do I start research in 2nd year?", "authorDisplayName": "a"}}},
                 "replies": {"comments": [{"snippet": {"authorChannelId": {"value": "ME"}}}]}},
                {"snippet": {"videoId": "v1", "totalReplyCount": 0,
                             "topLevelComment": {"id": "c2", "snippet": {"textDisplay": "রিসার্চ কিভাবে শুরু করব", "authorDisplayName": "b"}}}},
                {"snippet": {"videoId": "v1", "totalReplyCount": 0,
                             "topLevelComment": {"id": "c3", "snippet": {"textDisplay": "बहुत अच्छा वीडियो", "authorDisplayName": "c"}}}},
            ]},
            "search.list": lambda kw: {"items": [{"id": {"videoId": "s1"}, "snippet": {"channelId": "CH1", "title": "x"}},
                                                 {"id": {"videoId": "s2"}, "snippet": {"channelId": "ME", "title": "mine"}}]},
            "comments.insert": lambda kw: {"id": "r1"},
        }
        an = {"reports.query": self.analytics_report}
        self.clients = ytapi.Clients(self.settings, youtube=FakeResource(yt, self.calls), analytics=FakeResource(an, self.calls))

    def tearDown(self):
        self.tmp.cleanup()

    @staticmethod
    def analytics_report(kw):
        if kw.get("dimensions") == "elapsedVideoTimeRatio":
            return {"columnHeaders": [{"name": "elapsedVideoTimeRatio"}, {"name": "audienceWatchRatio"},
                                      {"name": "relativeRetentionPerformance"}],
                    "rows": [[i / 100, 1 - i / 200, 0.5] for i in range(1, 101)]}
        dims = kw.get("dimensions", "").split(",")
        return {"columnHeaders": [{"name": d} for d in dims] + [{"name": "views"}], "rows": [["x"] * len(dims) + [5]]}

    def test_parsers(self):
        self.assertEqual(ytapi.parse_duration("PT1H2M3S"), 3723)
        self.assertEqual(ytapi.parse_duration("P1DT1S"), 86401)
        self.assertEqual(ytapi.guess_language("রিসার্চ কিভাবে"), "bn")
        self.assertEqual(ytapi.guess_language("कैसे करें"), "hi")
        self.assertEqual(ytapi.guess_language("research kaise kare"), "en")
        self.assertTrue(ytapi.is_question("research kaise start kare"))
        self.assertTrue(ytapi.is_question("কেন এটা হয়"))
        self.assertFalse(ytapi.is_question("great video"))

    def test_snapshot(self):
        out = ytapi.cmd_snapshot(self.clients, argparse.Namespace(days=28, comments=50, retention=2))
        videos = json.loads((out / "videos.json").read_text())
        self.assertEqual(len(videos), 4)
        self.assertTrue(videos[3]["short_guess"])
        comments = json.loads((out / "comments" / "channel.json").read_text())
        self.assertEqual(comments["summary"], {"total": 3, "languages": {"en": 1, "bn": 1, "hi": 1},
                                               "questions": 2, "unanswered_questions": 1})
        retention = sorted((out / "retention").glob("*.csv"))
        self.assertEqual(len(retention), 2)
        with retention[0].open() as fh:
            rows = list(csv.reader(fh))
        self.assertEqual(rows[1][:2], ["1.0", "99.5"])
        analytics = json.loads((out / "analytics-28d.json").read_text())
        self.assertIn("search_terms", analytics)
        searched = [kw for name, kw in self.calls if name == "reports.query" and kw.get("filters") == "insightTrafficSourceType==YT_SEARCH"]
        self.assertEqual(len(searched), 1)

    def test_retention_csv_feeds_retention_py(self):
        path = ytapi.cmd_retention(self.clients, argparse.Namespace(video_id="v1", days=365))
        skill = Path(__file__).resolve().parents[3] / "youtube-agent-skill" / "skills" / "yt-retention"
        if not skill.exists():
            self.skipTest("youtube-agent-skill not checked out next to tubeflow")
        sys.path.insert(0, str(skill))
        import retention
        self.assertEqual(len(retention.load_csv(path)), 100)

    def test_trends_excludes_own_channel_and_matches_swipe_format(self):
        result = ytapi.cmd_trends(self.clients, argparse.Namespace(queries=["phd life"], days=90, channels=5,
                                                                   per_channel=4, lang=None, region=None))
        self.assertEqual({h["channel_id"] for h in result["hits"]}, {"CH1"})
        self.assertEqual(len(result["collected"]), 4)
        for key in ("channel", "title", "views", "url", "duration"):
            self.assertIn(key, result["collected"][0])

    def test_reply_is_dry_run_without_yes(self):
        ytapi.cmd_reply(self.clients, argparse.Namespace(comment_id="c2", text="hi", yes=False))
        self.assertNotIn("comments.insert", [n for n, _ in self.calls])
        ytapi.cmd_reply(self.clients, argparse.Namespace(comment_id="c2", text="hi", yes=True))
        self.assertIn("comments.insert", [n for n, _ in self.calls])

    def test_upload_body(self):
        body = ytapi.build_upload_body({"title": "T", "localizations": {"hi": {"title": "टी"}},
                                        "publish_at": "2026-11-01T10:00:00Z"}, "public", "en")
        self.assertEqual(body["status"]["privacyStatus"], "private")
        self.assertEqual(body["snippet"]["categoryId"], "27")
        self.assertEqual(body["localizations"]["hi"]["title"], "टी")
        self.assertEqual(ytapi.build_upload_body({"title": "T"}, "private", "bn")["snippet"]["defaultLanguage"], "bn")


if __name__ == "__main__":
    unittest.main()
