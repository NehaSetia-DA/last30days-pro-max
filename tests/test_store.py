import unittest

from last30days_pro_max import store
from last30days_pro_max.report import build_indexed_report


def _ev(evidence_id, url, rank, title="T", competitor="None"):
    return {
        "evidence_id": evidence_id,
        "url": url,
        "query": '"MCP" "web scraping"',
        "title": title,
        "snippet": "s",
        "competitor": competitor,
        "source_type": "web",
        "serp_rank": rank,
    }


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.conn = store.connect(":memory:")

    def tearDown(self):
        self.conn.close()

    def test_first_run_has_no_previous(self):
        deltas = store.compute_deltas(
            self.conn, run_id="r1", topic="agentic", evidence=[_ev("E001", "a", 1)]
        )
        self.assertIsNone(deltas["previous_run_id"])
        self.assertEqual(deltas["new"], [])
        self.assertEqual(deltas["fading"], [])

    def test_deltas_classify_new_recurring_fading_rank_changed(self):
        run1 = [_ev("E001", "a", 1), _ev("E002", "b", 2), _ev("E003", "c", 3)]
        store.save_run(self.conn, run_id="r1", topic="agentic",
                       created_at="2026-06-01T00:00:00Z", days=30, evidence=run1)

        # r2: a unchanged, b moved 2->5 (rank changed), d is new, c dropped (fading)
        run2 = [_ev("E001", "a", 1), _ev("E002", "b", 5), _ev("E004", "d", 4)]
        deltas = store.compute_deltas(
            self.conn, run_id="r2", topic="agentic", evidence=run2
        )

        self.assertEqual(deltas["previous_run_id"], "r1")
        self.assertEqual({e["url"] for e in deltas["new"]}, {"d"})
        self.assertEqual({e["url"] for e in deltas["recurring"]}, {"a", "b"})
        self.assertEqual({f["url"] for f in deltas["fading"]}, {"c"})
        changed = {rc["url"]: (rc["old_rank"], rc["new_rank"]) for rc in deltas["rank_changed"]}
        self.assertEqual(changed, {"b": (2, 5)})

    def test_save_run_is_idempotent_for_same_run_id(self):
        ev = [_ev("E001", "a", 1)]
        store.save_run(self.conn, run_id="r1", topic="agentic",
                       created_at="2026-06-01T00:00:00Z", days=30, evidence=ev)
        # Re-running the same run_id should replace, not duplicate.
        store.save_run(self.conn, run_id="r1", topic="agentic",
                       created_at="2026-06-02T00:00:00Z", days=30, evidence=ev)
        count = self.conn.execute(
            "SELECT COUNT(*) FROM evidence WHERE run_id='r1'"
        ).fetchone()[0]
        self.assertEqual(count, 1)

    def test_report_section_2_renders_delta_language(self):
        deltas = {
            "previous_run_id": "r1",
            "previous_created_at": "2026-06-01T00:00:00Z",
            "new": [_ev("E004", "d", 4, title="New Thing")],
            "recurring": [_ev("E001", "a", 1)],
            "fading": [{"url": "c", "title": "Old Thing", "serp_rank": 3}],
            "rank_changed": [{"url": "b", "title": "Mover", "old_rank": 2, "new_rank": 5}],
        }
        report = build_indexed_report(
            topic="agentic web scraping",
            competitors=["Apify"],
            seed_keywords=["MCP web scraping"],
            evidence=[_ev("E001", "a", 1)],
            date_range="2026-05-10 → 2026-06-09",
            run_id="r2",
            deltas=deltas,
        )
        section2 = report.split("## 2.")[1].split("## 3.")[0].lower()
        self.assertIn("new", section2)
        self.assertIn("recurring", section2)
        self.assertIn("fading", section2)
        self.assertIn("rank", section2)
        self.assertIn("r1", section2)  # references the previous run


if __name__ == "__main__":
    unittest.main()
