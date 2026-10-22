"""Tests for cloud_db.py."""

import sqlite3
import tempfile
import unittest
from pathlib import Path

import cloud_db


class TestCloudDB(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_db = Path(self.temp_dir.name) / "test_cloud.db"
        con = sqlite3.connect(str(self.test_db))
        con.execute("CREATE TABLE books (id TEXT PRIMARY KEY, title TEXT);")
        con.execute("INSERT INTO books VALUES ('1', 'Bulut Kitap');")
        con.commit()
        con.close()

    def tearDown(self):
        cloud_db.reset_for_tests()
        self.temp_dir.cleanup()

    def test_dump_and_restore(self):
        dump_txt = cloud_db.dump_db(self.test_db)
        self.assertTrue(cloud_db.dump_has_records(dump_txt))
        self.assertEqual(cloud_db.main_table_rows(self.test_db), 1)

        restored_db = Path(self.temp_dir.name) / "restored.db"
        cloud_db.restore_dump(dump_txt, restored_db)
        self.assertEqual(cloud_db.main_table_rows(restored_db), 1)

    def test_cloud_db_lifecycle(self):
        # cloud_db ensure_started yerel modda
        cloud_db.reset_for_tests()
        cloud_db.ensure_started(cfg={"db_sync": False}, local_db=self.test_db, start_thread=False)
        self.assertEqual(cloud_db.active_path(), self.test_db)
        sync_on, desc = cloud_db.describe()
        self.assertFalse(sync_on)
        self.assertIsNone(cloud_db.status())


if __name__ == "__main__":
    unittest.main()
