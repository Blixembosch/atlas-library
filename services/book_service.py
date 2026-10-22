"""Atlas Library - Kitap Yönetim ve Arama Servisi."""

from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd

from core.config import TZ, BAD_COVER_MARKERS
from core.db import get_db, init_db, get_db_path
from services.classifier_service import looks_dutch, foreign_learning_language

try:
    import streamlit as st
    _has_st = True
except Exception:
    _has_st = False


def get_clean_cover(url: Any) -> Optional[str]:
    """Geçersiz, boş veya hatalı kapak adreslerini ayıklar."""
    if url is None:
        return None
    s = str(url).strip()
    if not s or s.lower() == "nan":
        return None
    if any(m in s for m in BAD_COVER_MARKERS):
        return None
    return s


def _load_books_dataframe(db_path_str: str) -> pd.DataFrame:
    """Doğrudan SQLite veritabanından kitapları okuyup DataFrame üretir."""
    with get_db(db_path_str) as con:
        df = pd.read_sql("SELECT * FROM books", con)

    if "read_count" not in df.columns:
        df["read_count"] = 0
    else:
        df["read_count"] = pd.to_numeric(df["read_count"], errors="coerce").fillna(0).astype(int)

    if "language" not in df.columns:
        df["language"] = "Türkçe"

    if "is_school" not in df.columns:
        df["is_school"] = 0
    else:
        df["is_school"] = pd.to_numeric(df["is_school"], errors="coerce").fillna(0).astype(int)

    df["pages"] = pd.to_numeric(df["pages"], errors="coerce")

    if "is_outgrown" not in df.columns:
        df["is_outgrown"] = 0
    else:
        df["is_outgrown"] = pd.to_numeric(df["is_outgrown"], errors="coerce").fillna(0).astype(int)

    return df


if _has_st:
    _cached_load = st.cache_data(ttl=600)(_load_books_dataframe)
else:
    _cached_load = _load_books_dataframe


def get_books_df(db_path: str | Path | None = None, force_refresh: bool = False) -> pd.DataFrame:
    """Tüm kitapları DataFrame olarak döner (önbellekli)."""
    init_db(db_path)
    path_str = str(db_path or get_db_path())
    if force_refresh:
        clear_books_cache()
    return _cached_load(path_str)


def clear_books_cache() -> None:
    """Streamlit kitap önbelleğini temizler."""
    if _has_st:
        try:
            _cached_load.clear()
        except Exception:
            pass


def add_book(
    title: str,
    author: str = "",
    publisher: str = "",
    isbn: str = "",
    category: str = "Hikaye",
    age: str = "5+",
    pages: Optional[int] = None,
    language: str = "Türkçe",
    cover_url: str = "",
    db_path: str | Path | None = None,
) -> str:
    """Kütüphaneye yeni bir ev kitabı ekler."""
    init_db(db_path)
    bid = "MAN-" + uuid.uuid4().hex[:8].upper()
    lang = language.strip()
    if lang.lower() in ("", "türkçe", "turkce"):
        if looks_dutch(title, publisher):
            lang = "Dutch"
        fl = foreign_learning_language(title)
        if fl:
            lang = fl

    clean_cov = get_clean_cover(cover_url) or ""
    now_iso = datetime.now(TZ).isoformat()

    with get_db(db_path) as con:
        con.execute(
            """
            INSERT INTO books (id, title, author, publisher, isbn, category, age, pages, language, cover_url, read_count, created_at, is_school, is_outgrown)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, 0, 0)
            """,
            (bid, title.strip(), author.strip(), publisher.strip(), isbn.strip(), category, age, pages, lang, clean_cov, now_iso),
        )

    clear_books_cache()
    return bid


def add_school_book(
    title: str,
    author: str = "De Vuurvlinder Okulu",
    publisher: str = "De Vuurvlinder",
    isbn: str = "",
    pages: Optional[int] = None,
    cover_url: str = "",
    read_dt: Optional[datetime] = None,
    by_atlas: bool = False,
    db_path: str | Path | None = None,
) -> str:
    """Okul kitabı ekler; okuma kaydını hemen oluşturup okundu sayar."""
    init_db(db_path)
    final_title = title.strip()
    read_iso = (read_dt or datetime.now(TZ)).isoformat()
    clean_cov = get_clean_cover(cover_url) or ""

    with get_db(db_path) as con:
        existing = con.execute(
            "SELECT id FROM books WHERE is_school = 1 AND lower(title) = lower(?)",
            (final_title,),
        ).fetchone()

        if existing:
            bid = existing["id"]
            con.execute("UPDATE books SET read_count = read_count + 1 WHERE id = ?", (bid,))
        else:
            bid = "SCH-" + uuid.uuid4().hex[:8].upper()
            con.execute(
                """
                INSERT INTO books (id, title, author, publisher, isbn, category, pages, cover_url, language, read_count, created_at, is_school, is_outgrown)
                VALUES (?, ?, ?, ?, ?, 'Hikaye', ?, ?, 'Dutch', 1, ?, 1, 0)
                """,
                (bid, final_title, author.strip(), publisher.strip(), isbn.strip(), pages, clean_cov, datetime.now(TZ).isoformat()),
            )

        con.execute(
            """
            INSERT INTO reading_log (book_id, status, read_at, cycle, by_atlas)
            VALUES (?, 'read', ?, 1, ?)
            """,
            (bid, read_iso, 1 if by_atlas else 0),
        )

    clear_books_cache()
    from services.reading_service import clear_logs_cache
    clear_logs_cache()
    return bid


def update_book(
    book_id: str,
    title: Optional[str] = None,
    author: Optional[str] = None,
    publisher: Optional[str] = None,
    pages: Optional[int] = None,
    language: Optional[str] = None,
    category: Optional[str] = None,
    is_outgrown: Optional[int] = None,
    cover_url: Optional[str] = None,
    db_path: str | Path | None = None,
) -> bool:
    """Kitap bilgilerini günceller."""
    init_db(db_path)
    updates: List[str] = []
    params: List[Any] = []

    if title is not None:
        updates.append("title = ?")
        params.append(title.strip())
    if author is not None:
        updates.append("author = ?")
        params.append(author.strip())
    if publisher is not None:
        updates.append("publisher = ?")
        params.append(publisher.strip())
    if pages is not None:
        updates.append("pages = ?")
        params.append(pages)
    if language is not None:
        updates.append("language = ?")
        params.append(language.strip())
    if category is not None:
        updates.append("category = ?")
        params.append(category.strip())
    if is_outgrown is not None:
        updates.append("is_outgrown = ?")
        params.append(int(is_outgrown))
    if cover_url is not None:
        updates.append("cover_url = ?")
        params.append(get_clean_cover(cover_url) or "")

    if not updates:
        return False

    params.append(book_id)
    with get_db(db_path) as con:
        cur = con.execute(f"UPDATE books SET {', '.join(updates)} WHERE id = ?", params)
        success = cur.rowcount > 0

    clear_books_cache()
    return success


def update_cover(book_id: str, cover_url: str, db_path: str | Path | None = None) -> bool:
    """Sadece kitap kapağını günceller."""
    return update_book(book_id, cover_url=cover_url, db_path=db_path)


def delete_book(book_id: str, db_path: str | Path | None = None) -> bool:
    """Kitabı ve varsa ilişkili okuma loglarını ve anılarını siler."""
    init_db(db_path)
    with get_db(db_path) as con:
        con.execute("DELETE FROM reading_log WHERE book_id = ?", (book_id,))
        con.execute("DELETE FROM reading_memories WHERE book_id = ?", (book_id,))
        cur = con.execute("DELETE FROM books WHERE id = ?", (book_id,))
        success = cur.rowcount > 0

    clear_books_cache()
    from services.reading_service import clear_logs_cache
    clear_logs_cache()
    return success


def batch_update_outgrown(pairs: List[Tuple[int, str]], db_path: str | Path | None = None) -> None:
    """pairs = [(is_outgrown, book_id), ...] toplu güncelleme yapar."""
    init_db(db_path)
    with get_db(db_path) as con:
        con.executemany("UPDATE books SET is_outgrown = ? WHERE id = ?", pairs)
    clear_books_cache()


def batch_update_categories(pairs: List[Tuple[str, str]], db_path: str | Path | None = None) -> None:
    """pairs = [(book_id, new_category), ...] toplu kategori güncellemesi yapar."""
    init_db(db_path)
    with get_db(db_path) as con:
        con.executemany("UPDATE books SET category = ? WHERE id = ?", [(cat, bid) for bid, cat in pairs])
    clear_books_cache()


def filter_books(
    df: pd.DataFrame,
    search_query: str = "",
    publisher: str = "Tümü",
    category: str = "Tümü",
    age_filter: str = "Uygun olanlar",
) -> pd.DataFrame:
    """Kütüphane arama ve filtreleme kurallarını uygular."""
    filtered = df.copy()

    if publisher != "Tümü":
        filtered = filtered[filtered["publisher"] == publisher]

    if category != "Tümü":
        filtered = filtered[filtered["category"] == category]

    if age_filter == "Uygun olanlar":
        filtered = filtered[filtered["is_outgrown"] == 0]
    elif age_filter == "Yaşı geçenler":
        filtered = filtered[filtered["is_outgrown"] == 1]

    if search_query:
        q = search_query.strip()
        filtered = filtered[
            filtered["title"].astype(str).str.contains(q, case=False, na=False)
            | filtered["author"].astype(str).str.contains(q, case=False, na=False)
        ]

    return filtered.sort_values(by="title", ascending=True)
