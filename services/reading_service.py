"""Atlas Library - Okuma Kayıtları, Onaylar ve Hedef Servisi."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd

from core.config import TZ
from core.db import get_db, init_db, get_setting, get_db_path

try:
    import streamlit as st
    _has_st = True
except Exception:
    _has_st = False


def _load_all_logs(db_path_str: str) -> List[Dict[str, Any]]:
    """Tüm okuma loglarını doğrudan veritabanından çeker."""
    with get_db(db_path_str) as con:
        rows = con.execute("SELECT * FROM reading_log ORDER BY id DESC").fetchall()
        return [dict(r) for r in rows]


if _has_st:
    _cached_logs = st.cache_data(ttl=60)(_load_all_logs)
else:
    _cached_logs = _load_all_logs


def get_all_logs(db_path: str | Path | None = None, force_refresh: bool = False) -> List[Dict[str, Any]]:
    """Tüm okuma loglarını döner (önbellekli)."""
    init_db(db_path)
    path_str = str(db_path or get_db_path())
    if force_refresh:
        clear_logs_cache()
    return _cached_logs(path_str)


def clear_logs_cache() -> None:
    """Okuma logları önbelleğini temizler."""
    if _has_st:
        try:
            _cached_logs.clear()
        except Exception:
            pass


def is_pending(log: Dict[str, Any]) -> bool:
    """Okuma kaydı ebeveyn onayı bekliyor mu?"""
    return log.get("status") == "pending"


def approved_logs(logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Yalnızca onaylanmış okuma kayıtlarını filtreler."""
    return [l for l in logs if not is_pending(l)]


def atlas_logs(logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Atlas'ın kendi başına okuduğu onaylı kayıtları filtreler."""
    return [l for l in approved_logs(logs) if int(l.get("by_atlas") or 0) == 1]


def period_counts(logs: List[Dict[str, Any]]) -> Dict[str, int]:
    """Toplam, bu yıl ve bu ay okunan kitap sayılarını hesaplar."""
    now = datetime.now(TZ)
    out = {"total": 0, "year": 0, "month": 0}
    for l in logs:
        out["total"] += 1
        rat = l.get("read_at")
        if not rat:
            continue
        try:
            dt = datetime.fromisoformat(rat)
            if dt.year == now.year:
                out["year"] += 1
                if dt.month == now.month:
                    out["month"] += 1
        except (TypeError, ValueError):
            continue
    return out


def language_read_summary(logs: List[Dict[str, Any]], books_df: pd.DataFrame) -> Dict[str, Dict[str, int]]:
    """Dillere göre (Türkçe, Dutch, Diğer) okuma istatistiklerini gruplar."""
    lang_of = dict(zip(books_df["id"], books_df["language"].fillna("Türkçe")))
    now = datetime.now(TZ)
    out: Dict[str, Dict[str, int]] = {}

    for l in logs:
        bid = l.get("book_id")
        lang = lang_of.get(bid)
        if lang is None:
            continue
        group = lang if lang in ("Türkçe", "Dutch") else "Diğer"
        row = out.setdefault(group, {"total": 0, "year": 0, "month": 0})
        row["total"] += 1
        rat = l.get("read_at")
        if not rat:
            continue
        try:
            dt = datetime.fromisoformat(rat)
            if dt.year == now.year:
                row["year"] += 1
                if dt.month == now.month:
                    row["month"] += 1
        except (TypeError, ValueError):
            continue

    return out


def daily_goal(db_path: str | Path | None = None) -> int:
    """Günlük kitap okuma hedefini döner (varsayılan: 2)."""
    try:
        val = get_setting("daily_goal", "2", db_path=db_path)
        return max(1, int(val))
    except (TypeError, ValueError):
        return 2


def goal_status(db_path: str | Path | None = None) -> Dict[str, Any]:
    """Bugünün okuma hedefi durumu ve kesintisiz seri (streak) bilgisini hesaplar."""
    goal = daily_goal(db_path)
    today = datetime.now(TZ).date()
    today_iso = today.isoformat()
    per_day: Dict[str, int] = {}
    pending = 0

    all_logs = get_all_logs(db_path)
    for l in all_logs:
        day = (l.get("read_at") or "")[:10]
        if is_pending(l):
            if day == today_iso:
                pending += 1
        else:
            per_day[day] = per_day.get(day, 0) + 1

    done = per_day.get(today_iso, 0)

    # Streak hesaplama
    streak = 0
    d = today if done >= goal else today - timedelta(days=1)
    while per_day.get(d.isoformat(), 0) >= goal:
        streak += 1
        d -= timedelta(days=1)

    return {
        "goal": goal,
        "done": done,
        "pending": pending,
        "remaining": max(goal - done - pending, 0),
        "streak": streak,
        "today_iso": today_iso,
    }


def record_pending_read(book_id: str, db_path: str | Path | None = None) -> bool:
    """Çocuk 'Okudum' dediğinde onay bekleyen kayıt oluşturur (aynı gün tekrarı önler)."""
    init_db(db_path)
    today_iso = datetime.now(TZ).date().isoformat()
    now_iso = datetime.now(TZ).replace(tzinfo=None).isoformat(timespec="seconds")

    with get_db(db_path) as con:
        dup = con.execute(
            """
            SELECT 1 FROM reading_log
            WHERE book_id = ? AND (status = 'pending' OR substr(read_at, 1, 10) = ?)
            """,
            (book_id, today_iso),
        ).fetchone()

        if dup:
            return False

        con.execute(
            "INSERT INTO reading_log (book_id, status, read_at, cycle, by_atlas) VALUES (?, 'pending', ?, 1, 0)",
            (book_id, now_iso),
        )

    clear_logs_cache()
    return True


def record_manual_read(
    book_id: str,
    read_iso: str,
    by_atlas: bool = False,
    db_path: str | Path | None = None,
) -> None:
    """Yönetici tarafından geçmiş tarihli doğrudan onaylı okuma ekler."""
    init_db(db_path)
    with get_db(db_path) as con:
        con.execute(
            "INSERT INTO reading_log (book_id, status, read_at, cycle, by_atlas) VALUES (?, 'read', ?, 1, ?)",
            (book_id, read_iso, 1 if by_atlas else 0),
        )
        con.execute("UPDATE books SET read_count = read_count + 1 WHERE id = ?", (book_id,))

    clear_logs_cache()
    from services.book_service import clear_books_cache
    clear_books_cache()


def approve_reading(log_id: int, by_atlas: bool = False, db_path: str | Path | None = None) -> bool:
    """Bekleyen okuma kaydını onaylar ve kitabın sayacını artırır."""
    init_db(db_path)
    with get_db(db_path) as con:
        row = con.execute("SELECT book_id, status FROM reading_log WHERE id = ?", (log_id,)).fetchone()
        if not row or row["status"] != "pending":
            return False

        con.execute(
            "UPDATE reading_log SET status = 'read', by_atlas = ? WHERE id = ?",
            (1 if by_atlas else 0, log_id),
        )
        con.execute("UPDATE books SET read_count = read_count + 1 WHERE id = ?", (row["book_id"],))

    clear_logs_cache()
    from services.book_service import clear_books_cache
    clear_books_cache()
    return True


def approve_all_pending(atlas_flags_map: Optional[Dict[int, bool]] = None, db_path: str | Path | None = None) -> int:
    """Tüm bekleyen okumaları onaylar."""
    init_db(db_path)
    flags = atlas_flags_map or {}
    count = 0
    with get_db(db_path) as con:
        pending = con.execute("SELECT id, book_id FROM reading_log WHERE status = 'pending'").fetchall()
        for p in pending:
            by_atlas = 1 if flags.get(p["id"], False) else 0
            con.execute("UPDATE reading_log SET status = 'read', by_atlas = ? WHERE id = ?", (by_atlas, p["id"]))
            con.execute("UPDATE books SET read_count = read_count + 1 WHERE id = ?", (p["book_id"],))
            count += 1

    clear_logs_cache()
    from services.book_service import clear_books_cache
    clear_books_cache()
    return count


def reject_reading(log_id: int, db_path: str | Path | None = None) -> bool:
    """Bekleyen okuma kaydını reddeder ve siler."""
    init_db(db_path)
    with get_db(db_path) as con:
        cur = con.execute("DELETE FROM reading_log WHERE id = ? AND status = 'pending'", (log_id,))
        success = cur.rowcount > 0

    clear_logs_cache()
    return success


def undo_last_read(book_id: str, db_path: str | Path | None = None) -> bool:
    """Kitaba ait son onaylı okumayı geri alır."""
    init_db(db_path)
    with get_db(db_path) as con:
        last_log = con.execute(
            """
            SELECT id FROM reading_log
            WHERE book_id = ? AND COALESCE(status, '') != 'pending'
            ORDER BY read_at DESC LIMIT 1
            """,
            (book_id,),
        ).fetchone()

        if not last_log:
            return False

        con.execute("DELETE FROM reading_log WHERE id = ?", (last_log["id"],))
        con.execute("UPDATE books SET read_count = MAX(0, read_count - 1) WHERE id = ?", (book_id,))

    clear_logs_cache()
    from services.book_service import clear_books_cache
    clear_books_cache()
    return True


def reset_all_counters(db_path: str | Path | None = None) -> None:
    """Tüm okuma geçmişini ve sayaçları sıfırlar."""
    init_db(db_path)
    with get_db(db_path) as con:
        con.execute("UPDATE books SET read_count = 0")
        con.execute("DELETE FROM reading_log")

    clear_logs_cache()
    from services.book_service import clear_books_cache
    clear_books_cache()


def calculate_level(total_read_books: int) -> Dict[str, int]:
    """Okunan kitap sayısına göre XP ve Seviye hesaplar."""
    xp = total_read_books * 10
    level = xp // 100 + 1
    in_level = xp % 100
    return {"xp": xp, "level": level, "pct": in_level, "to_next": 100 - in_level}
