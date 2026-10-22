"""Atlas Library - Merkezi Veritabanı Yönetimi ve Bütünlük."""

from __future__ import annotations

import os
from pathlib import Path
import sqlite3
import tempfile
import threading
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Generator, Dict, List, Optional, Tuple

from core.config import BASE_DIR, DATA_DIR, SEED_FILE, TZ, BAD_COVER_MARKERS

_INIT_LOCK = threading.Lock()
_INITIALIZED = False
_CUSTOM_DB_PATH: Optional[Path] = None


def set_custom_db_path(path: Path | str | None) -> None:
    """Testler veya özel durumlar için veritabanı yolunu ayarlar."""
    global _CUSTOM_DB_PATH, _INITIALIZED
    _CUSTOM_DB_PATH = Path(path) if path else None
    _INITIALIZED = False


def get_db_path() -> Path:
    """Aktif veritabanı dosya yolunu döner (cloud_db aktifse onun yolunu alır)."""
    if _CUSTOM_DB_PATH is not None:
        return _CUSTOM_DB_PATH

    try:
        import cloud_db
        return Path(cloud_db.active_path())
    except Exception:
        # cloud_db başlatılmamışsa veya yoksa yerel DB'yi kullan
        local_db = BASE_DIR / "atlas_library.db"
        if not local_db.exists() and (DATA_DIR / "atlas_library.db").exists():
            return DATA_DIR / "atlas_library.db"
        return local_db


@contextmanager
def get_db(db_path: str | Path | None = None) -> Generator[sqlite3.Connection, None, None]:
    """Güvenli, otomatik commit/rollback ve bağlantı kapatma sağlayan context manager."""
    path = Path(db_path or get_db_path())
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(path), timeout=20.0, check_same_thread=False)
    con.row_factory = sqlite3.Row
    try:
        con.execute("PRAGMA journal_mode = WAL;")
    except sqlite3.Error:
        pass
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def init_db(db_path: str | Path | None = None, force: bool = False) -> None:
    """Veritabanı tablolarını, sütun göçlerini ve indekslerini güvenle başlatır."""
    global _INITIALIZED
    with _INIT_LOCK:
        if _INITIALIZED and not force:
            return

        with get_db(db_path) as con:
            # 1. Tabloların oluşturulması
            con.executescript("""
                CREATE TABLE IF NOT EXISTS books (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    publisher TEXT,
                    pages INTEGER,
                    author TEXT,
                    isbn TEXT,
                    age TEXT,
                    category TEXT,
                    subcategory TEXT,
                    cover_url TEXT,
                    language TEXT DEFAULT 'Türkçe',
                    read_count INTEGER DEFAULT 0,
                    created_at TEXT,
                    is_school INTEGER DEFAULT 0,
                    is_outgrown INTEGER DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS reading_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    book_id TEXT,
                    status TEXT,
                    read_at TEXT,
                    cycle INTEGER DEFAULT 1,
                    by_atlas INTEGER DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                );

                -- Anı Defteri Tablosu
                CREATE TABLE IF NOT EXISTS reading_memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    book_id TEXT NOT NULL,
                    note TEXT NOT NULL,
                    favorite_quote TEXT DEFAULT '',
                    photo_url TEXT DEFAULT '',
                    rating INTEGER DEFAULT 5,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE
                );
            """)

            # 2. Sütun göçleri (Eksik sütun varsa ekle)
            cursor = con.cursor()
            cursor.execute("PRAGMA table_info(books)")
            b_cols = {col["name"] for col in cursor.fetchall()}
            if "language" not in b_cols:
                cursor.execute("ALTER TABLE books ADD COLUMN language TEXT DEFAULT 'Türkçe'")
            if "is_school" not in b_cols:
                cursor.execute("ALTER TABLE books ADD COLUMN is_school INTEGER DEFAULT 0")
            if "is_outgrown" not in b_cols:
                cursor.execute("ALTER TABLE books ADD COLUMN is_outgrown INTEGER DEFAULT 0")

            cursor.execute("PRAGMA table_info(reading_log)")
            l_cols = {col["name"] for col in cursor.fetchall()}
            if "by_atlas" not in l_cols:
                cursor.execute("ALTER TABLE reading_log ADD COLUMN by_atlas INTEGER DEFAULT 0")
            if "status" not in l_cols:
                cursor.execute("ALTER TABLE reading_log ADD COLUMN status TEXT DEFAULT 'read'")

            # 3. Performans İndeksleri
            con.executescript("""
                CREATE INDEX IF NOT EXISTS idx_reading_log_book_id ON reading_log(book_id);
                CREATE INDEX IF NOT EXISTS idx_reading_log_read_at ON reading_log(read_at);
                CREATE INDEX IF NOT EXISTS idx_reading_log_status ON reading_log(status);
                CREATE INDEX IF NOT EXISTS idx_books_category ON books(category);
                CREATE INDEX IF NOT EXISTS idx_books_language ON books(language);
                CREATE INDEX IF NOT EXISTS idx_books_is_school ON books(is_school);
                CREATE INDEX IF NOT EXISTS idx_books_is_outgrown ON books(is_outgrown);
                CREATE INDEX IF NOT EXISTS idx_memories_book_id ON reading_memories(book_id);
            """)

            # 4. Bozuk kapak temizliği ve okul kitabı dil doğrulaması
            for marker in BAD_COVER_MARKERS:
                con.execute("UPDATE books SET cover_url = '' WHERE cover_url LIKE ?", (f"%{marker}%",))

            con.execute("""
                UPDATE books SET language = 'Dutch'
                WHERE is_school = 1 AND (language IS NULL OR language != 'Dutch')
            """)

            # 5. Boş kategori düzeltmesi
            con.execute("UPDATE books SET category = 'İlk Okuma' WHERE category IS NULL OR trim(category) = ''")

            # 6. Tohumlama (Eğer veritabanı tamamen boşsa)
            books_count = con.execute("SELECT count(*) FROM books").fetchone()[0]
            if books_count == 0 and SEED_FILE.exists():
                try:
                    import pandas as pd
                    df = pd.read_csv(SEED_FILE, dtype=str).fillna("")
                    df["created_at"] = datetime.now(TZ).isoformat()
                    df["read_count"] = 0
                    df["is_school"] = 0
                    df["is_outgrown"] = 0
                    if "language" not in df.columns:
                        df["language"] = "Türkçe"
                    if "cover_url" in df.columns:
                        df["cover_url"] = df["cover_url"].apply(
                            lambda x: "" if any(m in str(x) for m in BAD_COVER_MARKERS) else x
                        )
                    df.to_sql("books", con, if_exists="append", index=False)
                except Exception:
                    pass

        _INITIALIZED = True


def get_setting(key: str, default: str = "", db_path: str | Path | None = None) -> str:
    """Settings tablosundan bir anahtarın değerini çeker."""
    init_db(db_path)
    with get_db(db_path) as con:
        r = con.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return r["value"] if r and r["value"] is not None else default


def set_setting(key: str, value: Any, db_path: str | Path | None = None) -> None:
    """Settings tablosuna bir anahtarı kaydeder veya günceller."""
    init_db(db_path)
    with get_db(db_path) as con:
        con.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))


def sync_read_counts(db_path: str | Path | None = None) -> int:
    """reading_log tablosundaki onaylı okumalara göre books.read_count alanını senkronize eder."""
    init_db(db_path)
    with get_db(db_path) as con:
        # Tüm sayaçları 0 yapıp onaylı okuma kayıtlarından yeniden hesapla
        con.execute("UPDATE books SET read_count = 0")
        con.execute("""
            UPDATE books
            SET read_count = (
                SELECT count(*)
                FROM reading_log
                WHERE reading_log.book_id = books.id
                  AND COALESCE(reading_log.status, '') != 'pending'
            )
        """)
        updated = con.execute("SELECT count(*) FROM books WHERE read_count > 0").fetchone()[0]
        return updated


def summarize_db(path: str | Path) -> Optional[Dict[str, int]]:
    """Verilen SQLite dosyasının geçerliliğini ve özet istatistiklerini döner."""
    try:
        con = sqlite3.connect(str(path))
        try:
            if con.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                return None
            tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if not {"books", "reading_log"} <= tables:
                return None
            b_cnt = con.execute("SELECT count(*) FROM books").fetchone()[0]
            l_cnt = con.execute("SELECT count(*) FROM reading_log").fetchone()[0]
            p_cnt = 0
            if "status" in {r[1] for r in con.execute("PRAGMA table_info(reading_log)")}:
                p_cnt = con.execute("SELECT count(*) FROM reading_log WHERE status = 'pending'").fetchone()[0]
            m_cnt = 0
            if "reading_memories" in tables:
                m_cnt = con.execute("SELECT count(*) FROM reading_memories").fetchone()[0]
            return {"books": b_cnt, "logs": l_cnt, "pending": p_cnt, "memories": m_cnt}
        finally:
            con.close()
    except Exception:
        return None


def inspect_backup(data_bytes: bytes) -> Tuple[Optional[Dict[str, int]], Optional[str]]:
    """Yüklenen yedek dosyasını geçici alanda analiz eder."""
    if not data_bytes:
        return None, "Yedek dosyası boş."
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp.write(data_bytes)
        tmp_path = Path(tmp.name)
    try:
        summary = summarize_db(tmp_path)
        if not summary:
            return None, "Dosya geçerli bir Atlas Kütüphanesi veritabanı değil veya bozuk."
        return summary, None
    finally:
        if tmp_path.exists():
            os.remove(tmp_path)


def restore_db(data_bytes: bytes, target_path: str | Path | None = None) -> None:
    """Mevcut veritabanının yedeğini alıp yüklenen veritabanını yerine koyar."""
    target = Path(target_path or get_db_path())
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    # Mevcut DB'yi yedekle
    if target.exists():
        backup_path = DATA_DIR / f"pre_restore_{datetime.now(TZ).strftime('%Y%m%d_%H%M%S')}.db"
        try:
            src = sqlite3.connect(str(target))
            dst = sqlite3.connect(str(backup_path))
            src.backup(dst)
            dst.close()
            src.close()
        except Exception:
            pass

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp.write(data_bytes)
        tmp_path = Path(tmp.name)

    try:
        src = sqlite3.connect(str(tmp_path))
        dst = sqlite3.connect(str(target))
        src.backup(dst)
        dst.close()
        src.close()
    finally:
        if tmp_path.exists():
            os.remove(tmp_path)

    # Şema eksikleri varsa tamamla
    init_db(target, force=True)


def rows(table: str, where: str = "", params: Tuple[Any, ...] = (), db_path: str | Path | None = None) -> List[Dict[str, Any]]:
    """Belirtilen tablodaki kayıtları dict listesi olarak döner."""
    init_db(db_path)
    with get_db(db_path) as con:
        sql = f"SELECT * FROM {table}"
        if where:
            sql += f" WHERE {where}"
        cursor = con.execute(sql, params)
        return [dict(r) for r in cursor.fetchall()]
