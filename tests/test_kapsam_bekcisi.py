"""Atlas Library - Kapsam Bekçisi (Scope Guard).

Kural: Her fonksiyon en az bir testte çalışmalı; yeni fonksiyon testsiz eklenince kırmızıya döner.
"""

from __future__ import annotations

import ast
import glob
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class TestKapsamBekcisi(unittest.TestCase):
    def test_kapsam_bekcisi_her_fonksiyon_test_edilmeli(self):
        """Tüm çekirdek ve servis fonksiyonlarının test dosyalarında yer aldığını doğrular."""
        target_patterns = [
            "core/*.py",
            "services/*.py",
            "ui/*.py",
            "cloud_db.py",
        ]

        target_files = []
        for pat in target_patterns:
            for p in glob.glob(str(BASE_DIR / pat)):
                if "__init__" not in p:
                    target_files.append(Path(p))

        # 1. Projedeki tüm public fonksiyonları topla
        defined_functions = {}  # "modul:fonksiyon" -> dosya
        for file_path in target_files:
            rel_name = file_path.relative_to(BASE_DIR).as_posix()
            with open(file_path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=str(file_path))

            for node in tree.body:
                if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                    key = f"{rel_name} -> {node.name}"
                    defined_functions[key] = node.name

        # 2. Test dosyalarında çağrılan veya referans verilen sembolleri topla
        test_files = [
            Path(p) for p in glob.glob(str(BASE_DIR / "tests" / "test_*.py"))
            if "test_kapsam_bekcisi.py" not in p
        ]

        tested_symbols = set()
        for t_path in test_files:
            with open(t_path, "r", encoding="utf-8") as f:
                t_content = f.read()
                t_tree = ast.parse(t_content, filename=str(t_path))

            # AST seviyesinde isimleri ve nitelikleri topla
            for node in ast.walk(t_tree):
                if isinstance(node, ast.Name):
                    tested_symbols.add(node.id)
                elif isinstance(node, ast.Attribute):
                    tested_symbols.add(node.attr)
                elif isinstance(node, ast.alias):
                    tested_symbols.add(node.name)

        # 3. Kapsam kontrolü
        untested = []
        for func_key, func_name in defined_functions.items():
            if func_name not in tested_symbols:
                untested.append(func_key)

        error_message = (
            "\n❌ Kapsam Bekçisi: Aşağıdaki fonksiyonlar için test bulunamadı!\n"
            "Kural: Her fonksiyon en az bir testte çalışmalı; yeni fonksiyon testsiz eklenince kırmızıya döner.\n\n"
            + "\n".join(f"  • {u}" for u in untested)
            + f"\n\nToplam incelenen fonksiyon: {len(defined_functions)} | Testsiz: {len(untested)}"
        )

        self.assertEqual(len(untested), 0, error_message)


if __name__ == "__main__":
    unittest.main()
