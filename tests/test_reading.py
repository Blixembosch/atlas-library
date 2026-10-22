"""Tests for services/reading_service.py."""

import tempfile
import unittest
from datetime import datetime
from pathlib import Path
import pandas as pd

from core.config import TZ
from core.db import set_custom_db_path, init_db, get_db
from services.reading_service import (
    get_all_logs,
    clear_logs_cache,
    is_pending,
    approved_logs,
    atlas_logs,
    period_counts,
    language_read_summary,
    daily_goal,
    goal_status,
    record_pending_read,
    record_manual_read,
    approve_reading,
    approve_all_pending,
    reject_reading,
    undo_last_read,
    reset_all_counters,
    calculate_level,
)


class TestReadingService(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_db = Path(self.temp_dir.name) / "test_reading.db"
        set_custom_db_path(self.test_db)
        init_db(self.test_db, force=True)

        with get_db(self.test_db) as con:
            con.execute("INSERT INTO books (id, title, category, read_count, language) VALUES ('B1', 'Masal', 'Hikaye', 0, 'Türkçe')")
            con.execute("INSERT INTO books (id, title, category, read_count, language) VALUES ('B2', 'Kikker', 'Hikaye', 0, 'Dutch')")

    def tearDown(self):
        clear_logs_cache()
        set_custom_db_path(None)
        self.temp_dir.cleanup()

    def test_level_calculation(self):
        lv0 = calculate_level(0)
        self.assertEqual(lv0["level"], 1)
        self.assertEqual(lv0["xp"], 0)

        lv15 = calculate_level(15)
        self.assertEqual(lv15["xp"], 150)
        self.assertEqual(lv15["level"], 2)
        self.assertEqual(lv15["pct"], 50)
        self.assertEqual(lv15["to_next"], 50)

    def test_record_pending_and_approve(self):
        # Kayıt ekle
        ok = record_pending_read("B1", db_path=self.test_db)
        self.assertTrue(ok)

        # Aynı gün tekrar eklenemez
        dup = record_pending_read("B1", db_path=self.test_db)
        self.assertFalse(dup)

        logs = get_all_logs(self.test_db, force_refresh=True)
        self.assertEqual(len(logs), 1)
        self.assertTrue(is_pending(logs[0]))

        # Onayla
        app_ok = approve_reading(logs[0]["id"], by_atlas=True, db_path=self.test_db)
        self.assertTrue(app_ok)

        logs_after = get_all_logs(self.test_db, force_refresh=True)
        self.assertFalse(is_pending(logs_after[0]))
        self.assertEqual(len(approved_logs(logs_after)), 1)
        self.assertEqual(len(atlas_logs(logs_after)), 1)

    def test_manual_read_and_undo(self):
        now_iso = datetime.now(TZ).isoformat()
        record_manual_read("B1", now_iso, by_atlas=False, db_path=self.test_db)

        logs = get_all_logs(self.test_db, force_refresh=True)
        self.assertEqual(len(logs), 1)

        # Geri al
        undo_ok = undo_last_read("B1", db_path=self.test_db)
        self.assertTrue(undo_ok)

        logs_after = get_all_logs(self.test_db, force_refresh=True)
        self.assertEqual(len(logs_after), 0)

    def test_approve_all_and_reject(self):
        record_pending_read("B1", db_path=self.test_db)
        record_pending_read("B2", db_path=self.test_db)

        logs = get_all_logs(self.test_db, force_refresh=True)
        self.assertEqual(len(logs), 2)

        # 1 tanesini reddet
        rej_ok = reject_reading(logs[0]["id"], db_path=self.test_db)
        self.assertTrue(rej_ok)

        # Kalanı toplu onayla
        n = approve_all_pending(db_path=self.test_db)
        self.assertEqual(n, 1)

    def test_period_counts_and_language_summary(self):
        now_iso = datetime.now(TZ).isoformat()
        record_manual_read("B1", now_iso, by_atlas=True, db_path=self.test_db)
        record_manual_read("B2", now_iso, by_atlas=False, db_path=self.test_db)

        logs = get_all_logs(self.test_db, force_refresh=True)
        counts = period_counts(logs)
        self.assertEqual(counts["total"], 2)
        self.assertEqual(counts["month"], 2)

        df_books = pd.DataFrame([
            {"id": "B1", "language": "Türkçe"},
            {"id": "B2", "language": "Dutch"},
        ])
        lang_sum = language_read_summary(logs, df_books)
        self.assertEqual(lang_sum["Türkçe"]["total"], 1)
        self.assertEqual(lang_sum["Dutch"]["total"], 1)

    def test_goal_status(self):
        self.assertEqual(daily_goal(self.test_db), 2)
        gs = goal_status(self.test_db)
        self.assertEqual(gs["goal"], 2)
        self.assertIn("streak", gs)
        self.assertIn("remaining", gs)

    def test_reset_all_counters(self):
        record_manual_read("B1", "2026-10-23T10:00:00", db_path=self.test_db)
        reset_all_counters(self.test_db)
        logs = get_all_logs(self.test_db, force_refresh=True)
        self.assertEqual(len(logs), 0)


if __name__ == "__main__":
    unittest.main()
