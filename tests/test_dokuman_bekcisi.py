"""Atlas Library - Doküman Bekçisi (Doc Guard).

Kural: Bu README.md her sayfayı, çekirdek modülü, aracı, workflow'u ve
Anı Defteri modülünü/sekmesini kapsamalı. Eksik varsa kırmızıya döner.
"""

from __future__ import annotations

import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
README_PATH = BASE_DIR / "README.md"


class TestDokumanBekcisi(unittest.TestCase):
    def test_dokuman_bekcisi_readme_kapsami(self):
        """README.md dosyasının tüm sayfa, modül, servis, workflow ve Anı Defterini kapsadığını doğrular."""
        self.assertTrue(README_PATH.exists(), "README.md dosyası bulunamadı!")
        content = README_PATH.read_text(encoding="utf-8")

        # 1. Sayfa Kapsamı
        required_pages = [
            "Ana Sayfa",
            "Kütüphane",
            "Okuma Yolculuğu",
            "Rozetler",
            "Anı Defteri",  # Kullanıcı kuralı
            "Yönetici Paneli",
        ]

        # 2. Çekirdek Modüller ve Servisler
        required_modules = [
            "core/config.py",
            "core/db.py",
            "cloud_db.py",
            "book_service",
            "reading_service",
            "recommendation_service",
            "classifier_service",
            "isbn_service",
            "memory_service",
        ]

        # 3. Kullanıcı Arayüzü ve Araçlar
        required_ui = [
            "ui/components.py",
            "ui/covers.py",
            "ui/audio.py",
            "ui/styles.py",
        ]

        # 4. İş Akışları (Workflows)
        required_workflows = [
            "Kurulum",
            "Okuma Akışı",
            "Onay Mekanizması",
            "Öneri Mantığı",
            "Senkronizasyon",
        ]

        # 5. Bekçi Sistemleri
        required_guards = [
            "Kapsam Bekçisi",
            "Doküman Bekçisi",
        ]

        missing_items = []

        all_checks = {
            "Sayfalar": required_pages,
            "Modüller & Servisler": required_modules,
            "Arayüz & Araçlar": required_ui,
            "İş Akışları (Workflows)": required_workflows,
            "Bekçi Sistemleri": required_guards,
        }

        for category, items in all_checks.items():
            for item in items:
                if item.lower() not in content.lower():
                    missing_items.append(f"[{category}] -> {item}")

        error_message = (
            "\n❌ Doküman Bekçisi: README.md içerisinde eksik kalan bölümler tespit edildi!\n"
            "Kural: README.md her sayfayı, çekirdek modülü, aracı, workflow'u ve Anı Defteri modülünü/sekmesini kapsamalıdır.\n\n"
            + "\n".join(f"  • {m}" for m in missing_items)
            + f"\n\nEksik öğe sayısı: {len(missing_items)}"
        )

        self.assertEqual(len(missing_items), 0, error_message)


if __name__ == "__main__":
    unittest.main()
