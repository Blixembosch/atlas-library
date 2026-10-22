"""Atlas Library - Anı Defteri (Reading Memories) Servisi."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.config import TZ
from core.db import get_db, init_db


def add_memory(
    book_id: str,
    note: str,
    favorite_quote: str = "",
    photo_url: str = "",
    rating: int = 5,
    created_at: Optional[str] = None,
    db_path: str | Path | None = None,
) -> int:
    """Yeni bir okuma anısı veya notu ekler."""
    init_db(db_path)
    now_iso = created_at or datetime.now(TZ).isoformat(timespec="seconds")
    with get_db(db_path) as con:
        cur = con.execute(
            """
            INSERT INTO reading_memories (book_id, note, favorite_quote, photo_url, rating, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (book_id, note.strip(), favorite_quote.strip(), photo_url.strip(), int(rating), now_iso),
        )
        return cur.lastrowid


def get_memories(
    book_id: Optional[str] = None,
    db_path: str | Path | None = None,
) -> List[Dict[str, Any]]:
    """Tüm anıları veya belirli bir kitaba ait anıları kitap detaylarıyla birlikte döner."""
    init_db(db_path)
    with get_db(db_path) as con:
        if book_id:
            sql = """
                SELECT m.*, b.title as book_title, b.author as book_author, b.cover_url as book_cover
                FROM reading_memories m
                LEFT JOIN books b ON m.book_id = b.id
                WHERE m.book_id = ?
                ORDER BY m.created_at DESC
            """
            rows = con.execute(sql, (book_id,)).fetchall()
        else:
            sql = """
                SELECT m.*, b.title as book_title, b.author as book_author, b.cover_url as book_cover
                FROM reading_memories m
                LEFT JOIN books b ON m.book_id = b.id
                ORDER BY m.created_at DESC
            """
            rows = con.execute(sql).fetchall()
        return [dict(r) for r in rows]


def update_memory(
    memory_id: int,
    note: str,
    favorite_quote: str = "",
    photo_url: str = "",
    rating: int = 5,
    db_path: str | Path | None = None,
) -> bool:
    """Var olan anıyı günceller."""
    init_db(db_path)
    with get_db(db_path) as con:
        cur = con.execute(
            """
            UPDATE reading_memories
            SET note = ?, favorite_quote = ?, photo_url = ?, rating = ?
            WHERE id = ?
            """,
            (note.strip(), favorite_quote.strip(), photo_url.strip(), int(rating), memory_id),
        )
        return cur.rowcount > 0


def delete_memory(memory_id: int, db_path: str | Path | None = None) -> bool:
    """Anıyı veritabanından siler."""
    init_db(db_path)
    with get_db(db_path) as con:
        cur = con.execute("DELETE FROM reading_memories WHERE id = ?", (memory_id,))
        return cur.rowcount > 0


def get_memory_stats(db_path: str | Path | None = None) -> Dict[str, Any]:
    """Anı Defteri için özet istatistikleri döner."""
    init_db(db_path)
    with get_db(db_path) as con:
        total = con.execute("SELECT count(*) FROM reading_memories").fetchone()[0]
        with_quote = con.execute("SELECT count(*) FROM reading_memories WHERE favorite_quote != ''").fetchone()[0]
        avg_rating_row = con.execute("SELECT avg(rating) FROM reading_memories").fetchone()[0]
        avg_rating = round(avg_rating_row, 1) if avg_rating_row else 5.0
        return {
            "total_memories": total,
            "quotes_count": with_quote,
            "avg_rating": avg_rating,
        }
