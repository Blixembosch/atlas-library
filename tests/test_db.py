"""Tests for core/db.py."""

import os
import tempfile
import unittest
from pathlib import Path

from core.db import (
    set_custom_db_path,
    get_db_path,
    get_db,
    init_db,
    get_setting,
    set_setting,
    sync_read_counts,
    summarize_db,
    inspect_backup,
    restore_db,
    rows,
)


class TestDB(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_db = Path(self.temp_dir.name) / "test_atlas.db"
        set_custom_db_path(self.test_db)
        init_db(self.test_db, force=True)

    def tearDown(self):
        set_custom_db_path(None)
        self.temp_dir.cleanup()

    def test_get_db_path(self):
        path = get_db_path()
        self.assertEqual(path, self.test_db)

    def test_init_and_get_db(self):
        with get_db(self.test_db) as con:
            tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
            self.assertIn("books", tables)
            self.assertIn("reading_log", tables)
            self.assertIn("settings", tables)
            self.assertIn("reading_memories", tables)

    def test_settings(self):
        set_setting("daily_goal", "5", db_path=self.test_db)
        val = get_setting("daily_goal", default="2", db_path=self.test_db)
        self.assertEqual(val, "5")

    def test_rows(self):
        with get_db(self.test_db) as con:
            con.execute("INSERT INTO books (id, title, category) VALUES ('T1', 'Test Kitap', 'Hikaye')")
        r = rows("books", where="id = ?", params=("T1",), db_path=self.test_db)
        self.assertEqual(len(r), 1)
        self.assertEqual(r[0]["title"], "Test Kitap")

    def test_sync_read_counts(self):
        with get_db(self.test_db) as con:
            con.execute("INSERT INTO books (id, title, read_count) VALUES ('B1', 'Kitap 1', 0)")
            con.execute("INSERT INTO reading_log (book_id, status, read_at) VALUES ('B1', 'read', '2026-10-23')")
            con.execute("INSERT INTO reading_log (book_id, status, read_at) VALUES ('B1', 'pending', '2026-10-23')")

        updated = sync_read_counts(db_path=self.test_db)
        self.assertEqual(updated, 1)

        with get_db(self.test_db) as con:
            rc = con.execute("SELECT read_count FROM books WHERE id = 'B1'").fetchone()[0]
            self.assertEqual(rc, 1)

    def test_summarize_and_backup(self):
        summary = summarize_db(self.test_db)
        self.assertIsNotNone(summary)
        self.assertIn("books", summary)

        raw_bytes = self.test_db.read_bytes()
        info, err = inspect_backup(raw_bytes)
        self.assertIsNone(err)
        self.assertIsNotNone(info)

        # Restore
        target_restore = Path(self.temp_dir.name) / "restored.db"
        restore_db(raw_bytes, target_path=target_restore)
        self.assertTrue(target_restore.exists())


if __name__ == "__main__":
    unittest.main()
