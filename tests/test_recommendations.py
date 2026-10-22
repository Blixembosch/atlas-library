"""Tests for services/recommendation_service.py."""

import json
import tempfile
import unittest
from pathlib import Path
import pandas as pd

from core.db import set_custom_db_path, init_db, set_setting, get_db
from services.book_service import clear_books_cache
from services.reading_service import clear_logs_cache
from services.recommendation_service import (
    rec_languages,
    evening_no_dutch,
    priority_mode,
    priority_keys,
    priority_custom,
    series_mask,
    series_label,
    series_options,
    priority_books,
    priority_progress,
    get_pool_df,
    get_unread_pool,
    priority_per_day,
    priority_quota_left,
    sample_books,
    recommend_books,
    spin_wheel,
    random_pick,
)


class TestRecommendationService(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_db = Path(self.temp_dir.name) / "test_rec.db"
        set_custom_db_path(self.test_db)
        init_db(self.test_db, force=True)

        with get_db(self.test_db) as con:
            con.execute("INSERT INTO books (id, title, category, language, read_count, is_school, is_outgrown) VALUES ('C1', 'Cin Ali Okulda', 'İlk Okuma', 'Türkçe', 0, 0, 0)")
            con.execute("INSERT INTO books (id, title, category, language, read_count, is_school, is_outgrown) VALUES ('C2', 'Cin Ali Top Oynuyor', 'İlk Okuma', 'Türkçe', 0, 0, 0)")
            con.execute("INSERT INTO books (id, title, category, language, read_count, is_school, is_outgrown) VALUES ('B1', 'Uzay Rehberi', 'Bilim', 'Türkçe', 0, 0, 0)")
            con.execute("INSERT INTO books (id, title, category, language, read_count, is_school, is_outgrown) VALUES ('D1', 'Kikker is verliefd', 'Hikaye', 'Dutch', 0, 0, 0)")
            con.execute("INSERT INTO books (id, title, category, language, read_count, is_school, is_outgrown) VALUES ('O1', 'Eski Bebek Masalı', 'Hikaye', 'Türkçe', 0, 0, 1)")

    def tearDown(self):
        clear_books_cache()
        clear_logs_cache()
        set_custom_db_path(None)
        self.temp_dir.cleanup()

    def test_settings_and_labels(self):
        self.assertEqual(priority_mode(self.test_db), "ilk_okuma")
        self.assertEqual(rec_languages(self.test_db), ["Türkçe", "Dutch"])
        self.assertTrue(evening_no_dutch(self.test_db))
        self.assertEqual(priority_per_day(self.test_db), 1)

        lbl = series_label("title:Cin Ali")
        self.assertIn("Cin Ali", lbl)

    def test_series_mask_and_options(self):
        df = pd.DataFrame([
            {"id": "1", "title": "Cin Ali: 1", "publisher": "P1", "category": "İlk Okuma", "subcategory": "", "is_school": 0},
            {"id": "2", "title": "Cin Ali: 2", "publisher": "P1", "category": "İlk Okuma", "subcategory": "", "is_school": 0},
            {"id": "3", "title": "Cin Ali: 3", "publisher": "P1", "category": "İlk Okuma", "subcategory": "", "is_school": 0},
        ])
        mask = series_mask(df, "title:Cin Ali")
        self.assertEqual(int(mask.sum()), 3)

        opts = series_options(df, db_path=self.test_db)
        self.assertIn("title:Cin Ali", opts)

    def test_priority_books_and_progress(self):
        set_setting("priority_series", json.dumps(["title:Cin Ali"]), db_path=self.test_db)
        keys = priority_keys(self.test_db)
        self.assertEqual(keys, ["title:Cin Ali"])

        custom = priority_custom(self.test_db)
        self.assertEqual(custom, [])

        prog = priority_progress(self.test_db)
        self.assertIsNotNone(prog)
        self.assertEqual(prog[1], 2)  # 2 Cin Ali kitabı

        quota = priority_quota_left(self.test_db)
        self.assertEqual(quota, 1)

    def test_pools_and_recommendations(self):
        pool = get_pool_df(evening_filters=False, db_path=self.test_db)
        # Yaşı geçen O1 olmamalı
        self.assertNotIn("O1", pool["id"].values)

        unread = get_unread_pool(cat="Bilim", db_path=self.test_db)
        self.assertEqual(len(unread), 1)
        self.assertEqual(unread.iloc[0]["id"], "B1")

        sampled = sample_books(pool, 2)
        self.assertEqual(len(sampled), 2)

        recs = recommend_books(2, db_path=self.test_db)
        self.assertGreaterEqual(len(recs), 1)

        wheel_picks = spin_wheel(self.test_db)
        self.assertIsNotNone(wheel_picks)

        rnd_picks = random_pick(n=2, db_path=self.test_db)
        self.assertIsNotNone(rnd_picks)


if __name__ == "__main__":
    unittest.main()
