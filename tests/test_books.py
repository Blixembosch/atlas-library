"""Tests for services/book_service.py."""

import tempfile
import unittest
from pathlib import Path
import pandas as pd

from core.db import set_custom_db_path, init_db
from services.book_service import (
    get_clean_cover,
    get_books_df,
    clear_books_cache,
    add_book,
    add_school_book,
    update_book,
    update_cover,
    delete_book,
    batch_update_outgrown,
    batch_update_categories,
    filter_books,
)


class TestBookService(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_db = Path(self.temp_dir.name) / "test_books.db"
        set_custom_db_path(self.test_db)
        init_db(self.test_db, force=True)

    def tearDown(self):
        clear_books_cache()
        set_custom_db_path(None)
        self.temp_dir.cleanup()

    def test_clean_cover(self):
        self.assertIsNone(get_clean_cover(None))
        self.assertIsNone(get_clean_cover(""))
        self.assertIsNone(get_clean_cover("nan"))
        self.assertIsNone(get_clean_cover("https://longitood.com/dummy.jpg"))
        self.assertIsNone(get_clean_cover("https://site.com/deneyap-logo.png"))
        self.assertEqual(get_clean_cover("https://covers.com/b1.jpg"), "https://covers.com/b1.jpg")

    def test_add_and_get_book(self):
        bid = add_book(
            title="Uzay Maceraları",
            author="Ali Bilir",
            publisher="Bilim Yayınları",
            category="Bilim",
            db_path=self.test_db,
        )
        self.assertTrue(bid.startswith("MAN-"))

        df = get_books_df(self.test_db, force_refresh=True)
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]["title"], "Uzay Maceraları")

    def test_add_school_book(self):
        s_id = add_school_book(
            title="Nijntje op school",
            publisher="Mercis",
            by_atlas=True,
            db_path=self.test_db,
        )
        self.assertTrue(s_id.startswith("SCH-"))
        df = get_books_df(self.test_db, force_refresh=True)
        sch_book = df[df["id"] == s_id].iloc[0]
        self.assertEqual(sch_book["language"], "Dutch")
        self.assertEqual(sch_book["is_school"], 1)
        self.assertEqual(sch_book["read_count"], 1)

    def test_update_book_and_cover(self):
        bid = add_book(title="Eski Başlık", db_path=self.test_db)
        success = update_book(bid, title="Yeni Başlık", pages=42, db_path=self.test_db)
        self.assertTrue(success)

        cov_success = update_cover(bid, "https://example.com/c.jpg", db_path=self.test_db)
        self.assertTrue(cov_success)

        df = get_books_df(self.test_db, force_refresh=True)
        updated = df[df["id"] == bid].iloc[0]
        self.assertEqual(updated["title"], "Yeni Başlık")
        self.assertEqual(updated["pages"], 42)
        self.assertEqual(updated["cover_url"], "https://example.com/c.jpg")

    def test_delete_book(self):
        bid = add_book(title="Silinecek Kitap", db_path=self.test_db)
        self.assertTrue(delete_book(bid, db_path=self.test_db))
        df = get_books_df(self.test_db, force_refresh=True)
        self.assertEqual(len(df[df["id"] == bid]), 0)

    def test_batch_updates(self):
        b1 = add_book(title="Kitap 1", category="Hikaye", db_path=self.test_db)
        b2 = add_book(title="Kitap 2", category="Hikaye", db_path=self.test_db)

        batch_update_outgrown([(1, b1)], db_path=self.test_db)
        batch_update_categories([(b2, "Bilim")], db_path=self.test_db)

        df = get_books_df(self.test_db, force_refresh=True)
        self.assertEqual(df[df["id"] == b1].iloc[0]["is_outgrown"], 1)
        self.assertEqual(df[df["id"] == b2].iloc[0]["category"], "Bilim")

    def test_filter_books(self):
        b1 = add_book(title="Cin Ali Tatilde", author="Rasim Kaygusuz", publisher="Cin Ali", category="İlk Okuma", db_path=self.test_db)
        b2 = add_book(title="Dinozorlar Çağı", author="Mehmet", publisher="TÜBİTAK", category="Bilim", db_path=self.test_db)

        df = get_books_df(self.test_db, force_refresh=True)
        res = filter_books(df, search_query="Cin Ali")
        self.assertEqual(len(res), 1)

        res_cat = filter_books(df, category="Bilim")
        self.assertEqual(len(res_cat), 1)
        self.assertEqual(res_cat.iloc[0]["title"], "Dinozorlar Çağı")


if __name__ == "__main__":
    unittest.main()
