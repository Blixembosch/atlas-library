"""Tests for services/classifier_service.py."""

import unittest
import pandas as pd

from services.classifier_service import (
    tr_lower,
    looks_dutch,
    foreign_learning_language,
    akilli_kategori_belirle,
    load_category_reviews,
    auto_category_scan,
)


class TestClassifierService(unittest.TestCase):
    def test_tr_lower(self):
        self.assertEqual(tr_lower("İSTANBUL"), "istanbul")
        self.assertEqual(tr_lower("IŞIK"), "ışık")

    def test_looks_dutch(self):
        self.assertTrue(looks_dutch("Nijntje op de camping"))
        self.assertTrue(looks_dutch("Een grote boom"))
        self.assertTrue(looks_dutch("Türkçe Kitap", publisher="Kluitman"))
        self.assertFalse(looks_dutch("Keloğlan ve Sihirli Taş", publisher="Can Çocuk"))

    def test_foreign_learning_language(self):
        self.assertEqual(foreign_learning_language("Almanca İlk Kelimelerim"), "German")
        self.assertEqual(foreign_learning_language("My First Words İngilizce"), "English")
        self.assertIsNone(foreign_learning_language("Kırmızı Başlıklı Kız"))

    def test_akilli_kategori_belirle(self):
        self.assertEqual(akilli_kategori_belirle("Cin Ali Okulda"), "İlk Okuma")
        self.assertIsNone(akilli_kategori_belirle("Küçük Prens"))

    def test_load_category_reviews(self):
        revs = load_category_reviews()
        self.assertIsInstance(revs, dict)
        if revs:
            first_val = next(iter(revs.values()))
            self.assertEqual(len(first_val), 3)

    def test_auto_category_scan(self):
        df = pd.DataFrame([
            {"id": "K1", "title": "Çocuklar İçin Yoga", "category": "Hikaye", "is_school": 0},
            {"id": "K2", "title": "Büyük Uzay Yolculuğu", "category": "Hikaye", "is_school": 0},
            {"id": "K3", "title": "Normal Hikaye", "category": "Hikaye", "is_school": 0},
        ])
        scan_res = auto_category_scan(df)
        found_ids = {r["ID"] for r in scan_res}
        self.assertIn("K1", found_ids)
        self.assertIn("K2", found_ids)


if __name__ == "__main__":
    unittest.main()
