"""Tests for services/memory_service.py."""

import tempfile
import unittest
from pathlib import Path

from core.db import set_custom_db_path, init_db, get_db
from services.memory_service import (
    add_memory,
    get_memories,
    update_memory,
    delete_memory,
    get_memory_stats,
)


class TestMemoryService(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_db = Path(self.temp_dir.name) / "test_mem.db"
        set_custom_db_path(self.test_db)
        init_db(self.test_db, force=True)

        with get_db(self.test_db) as con:
            con.execute("INSERT INTO books (id, title) VALUES ('M1', 'Ejderhalar Diyarı')")

    def tearDown(self):
        set_custom_db_path(None)
        self.temp_dir.cleanup()

    def test_memory_crud(self):
        mid = add_memory("M1", "Ejderha sesini çok sevdik", favorite_quote="Korkusuz Ejderha!", rating=5, db_path=self.test_db)
        self.assertGreater(mid, 0)

        mems = get_memories(db_path=self.test_db)
        self.assertEqual(len(mems), 1)
        self.assertEqual(mems[0]["book_title"], "Ejderhalar Diyarı")
        self.assertEqual(mems[0]["note"], "Ejderha sesini çok sevdik")

        # Update
        up_ok = update_memory(mid, "Güncellenmiş not", rating=4, db_path=self.test_db)
        self.assertTrue(up_ok)

        # Stats
        stats = get_memory_stats(self.test_db)
        self.assertEqual(stats["total_memories"], 1)
        self.assertEqual(stats["avg_rating"], 4.0)

        # Delete
        del_ok = delete_memory(mid, db_path=self.test_db)
        self.assertTrue(del_ok)
        self.assertEqual(len(get_memories(db_path=self.test_db)), 0)


if __name__ == "__main__":
    unittest.main()
