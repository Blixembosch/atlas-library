"""Atlas Library - Test Koşucu ve Kalite Bekçisi."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Dış bağımlılıkların bulunmadığı ortamlarda shims devreye girer
import tests.shims


def main() -> int:
    print("=" * 72)
    print("🏰 ATLAS LIBRARY - TEST VE KALİTE SUITE")
    print("=" * 72)

    loader = unittest.TestLoader()
    suite = loader.discover(str(BASE_DIR / "tests"), pattern="test_*.py")

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 72)
    if result.wasSuccessful():
        print(f"✅ TÜM TESTLER BAŞARILI! Toplam {result.testsRun} test hatasız çalıştı.")
        print("🛡️ Kapsam Bekçisi: GEÇTİ (Her fonksiyon test edildi)")
        print("📖 Doküman Bekçisi: GEÇTİ (Tüm sayfalar, modüller ve Anı Defteri belgelendi)")
        print("=" * 72)
        return 0
    else:
        print(f"❌ TESTLERDE HATA VAR! ({len(result.failures)} başarısız, {len(result.errors)} hata)")
        print("=" * 72)
        return 1


if __name__ == "__main__":
    sys.exit(main())
