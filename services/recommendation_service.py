"""Atlas Library - Akıllı Kitap Öneri ve Çark Servisi."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import pandas as pd

from core.config import DEFAULT_REC_LANGS, PRIORITY_MODES, TZ
from core.db import get_setting
from services.book_service import get_books_df
from services.reading_service import get_all_logs, is_pending, goal_status
from services.classifier_service import tr_lower

try:
    import streamlit as st
    _has_st = True
except Exception:
    _has_st = False


def rec_languages(db_path: str | Path | None = None) -> List[str]:
    """Önerilecek dillerin listesi (varsayılan: Türkçe, Dutch)."""
    raw = get_setting("rec_languages", ",".join(DEFAULT_REC_LANGS), db_path=db_path)
    langs = [x.strip() for x in str(raw).split(",") if x.strip()]
    return langs or DEFAULT_REC_LANGS


def evening_no_dutch(db_path: str | Path | None = None) -> bool:
    """Akşam okumalarında (19:00+) Dutch kitaplar filtrelensin mi?"""
    return str(get_setting("evening_no_dutch", "1", db_path=db_path)) == "1"


def priority_mode(db_path: str | Path | None = None) -> str:
    """Eski öncelik modu (off, ilk_okuma, okuma_becerisi)."""
    m = str(get_setting("priority_mode", "ilk_okuma", db_path=db_path))
    return m if m in PRIORITY_MODES else "ilk_okuma"


def priority_keys(db_path: str | Path | None = None) -> List[str]:
    """Öncelikli serilerin anahtarları (örn: 'cat:İlk Okuma', 'title:Cin Ali')."""
    raw = get_setting("priority_series", "__legacy__", db_path=db_path)
    if raw == "__legacy__":
        return {
            "off": [],
            "ilk_okuma": ["cat:İlk Okuma"],
            "okuma_becerisi": ["sub:Okuma Becerisi"],
        }[priority_mode(db_path)]
    try:
        v = json.loads(raw)
        return [str(x) for x in v] if isinstance(v, list) else []
    except Exception:
        return []


def priority_custom(db_path: str | Path | None = None) -> List[str]:
    """Kullanıcının elle eklediği özel öncelikli seriler."""
    try:
        v = json.loads(get_setting("priority_custom", "[]", db_path=db_path))
        return [str(x) for x in v] if isinstance(v, list) else []
    except Exception:
        return []


def series_mask(df: pd.DataFrame, key: str) -> pd.Series:
    """Seri anahtarına göre DataFrame üzerinde eşleşme maskesi üretir."""
    kind, _, val = str(key).partition(":")
    if kind == "title":
        v = tr_lower(val)
        return df["title"].map(lambda t: tr_lower(t).startswith(v))
    if kind == "pub":
        return df["publisher"].fillna("") == val
    if kind == "cat":
        return df["category"] == val
    if kind == "sub":
        return df["subcategory"].astype(str) == val
    return pd.Series(False, index=df.index)


def series_label(key: str) -> str:
    """Seri anahtarının insan tarafından okunabilir etiketi."""
    kind, _, val = str(key).partition(":")
    return {
        "title": f"📖 {val}",
        "pub": f"🏢 {val} (yayınevi)",
        "cat": f"📂 {val} (kategori)",
        "sub": f"🏷️ {val} (alt tür)",
    }.get(kind, str(key))


def series_options(df: pd.DataFrame, db_path: str | Path | None = None) -> Dict[str, Tuple[str, int]]:
    """Katalogdaki kitaplardan otomatik çıkarılan seri seçenekleri."""
    ev_df = df[df["is_school"] == 0]
    found: Dict[str, int] = {}
    prefixes = ev_df["title"].map(lambda t: str(t).split(":")[0].strip() if ":" in str(t) else "")

    for p, n in prefixes[prefixes != ""].value_counts().items():
        if n >= 3:
            found[f"title:{p}"] = int(n)
    for p, n in ev_df["publisher"].fillna("").value_counts().items():
        if p and n >= 3:
            found[f"pub:{p}"] = int(n)
    for p, n in ev_df["category"].fillna("").value_counts().items():
        if p and n >= 3:
            found[f"cat:{p}"] = int(n)
    for p, n in ev_df["subcategory"].fillna("").value_counts().items():
        if p and n >= 3:
            found[f"sub:{p}"] = int(n)

    for k in priority_custom(db_path) + priority_keys(db_path):
        if k not in found:
            found[k] = int(series_mask(ev_df, k).sum())

    return {k: (series_label(k), n) for k, n in found.items()}


def priority_books(df: pd.DataFrame, db_path: str | Path | None = None) -> pd.DataFrame:
    """Öncelikli serilere uyan kitapları filtreler."""
    keys = priority_keys(db_path)
    if not keys:
        return df.iloc[0:0]
    m = pd.Series(False, index=df.index)
    for k in keys:
        m = m | series_mask(df, k)
    return df[m]


def priority_progress(db_path: str | Path | None = None) -> Optional[Tuple[int, int]]:
    """(okunan, toplam) öncelikli seriler için ilerleme; kapalıysa None döner."""
    if not priority_keys(db_path):
        return None
    df = get_pool_df(evening_filters=False, db_path=db_path)
    pri = priority_books(df, db_path=db_path)
    if len(pri) == 0:
        return None
    return int((pri["read_count"] > 0).sum()), len(pri)


def get_pool_df(evening_filters: bool = True, db_path: str | Path | None = None) -> pd.DataFrame:
    """Öneri havuzundaki uygun ev kitaplarını kurallara göre filtreler."""
    df = get_books_df(db_path)
    df = df[df["is_school"] == 0]
    df = df[df["is_outgrown"] == 0]
    df = df[df["language"].fillna("Türkçe").isin(rec_languages(db_path))]

    if evening_filters and datetime.now(TZ).hour >= 19:
        df = df[df["category"] != "Aktivite"]
        if evening_no_dutch(db_path):
            df = df[df["language"].fillna("Türkçe") != "Dutch"]

    return df


def get_unread_pool(cat: Optional[str] = None, db_path: str | Path | None = None) -> pd.DataFrame:
    """Henüz hiç okunmamış ve onay beklemeyen kitap havuzu."""
    df = get_pool_df(db_path=db_path)
    all_logs = get_all_logs(db_path)
    pending_ids = {l["book_id"] for l in all_logs if is_pending(l)}

    if cat and cat != "Tümü":
        df = df[df["category"] == cat]

    unread = df[(df["read_count"] == 0) & (~df["id"].isin(pending_ids))]
    return unread if len(unread) > 0 else df


def priority_per_day(db_path: str | Path | None = None) -> int:
    """Günde en fazla kaç öncelikli kitap önerileceği (varsayılan: 1)."""
    try:
        return max(0, int(get_setting("priority_per_day", "1", db_path=db_path)))
    except (TypeError, ValueError):
        return 1


def priority_quota_left(db_path: str | Path | None = None) -> int:
    """Bugün öncelikli seriden henüz okunmamış/kullanılmamış kota miktarı."""
    if not priority_keys(db_path):
        return 0
    books = get_books_df(db_path)
    books = books[books["is_school"] == 0]
    ids = set(priority_books(books, db_path=db_path)["id"])
    today = datetime.now(TZ).date().isoformat()
    all_logs = get_all_logs(db_path)

    used = sum(
        1 for l in all_logs
        if l.get("book_id") in ids and (l.get("read_at") or "")[:10] == today
    )
    return max(priority_per_day(db_path) - used, 0)


def sample_books(pool: pd.DataFrame, n: int, exclude_ids: Optional[Set[str]] = None) -> List[Dict[str, Any]]:
    """Havuzdan tekrarsız rastgele n kitap seçer."""
    if len(pool) == 0 or n <= 0:
        return []

    excludes = exclude_ids or set()
    if _has_st and not exclude_ids and "current_featured_books" in st.session_state:
        excludes = {b["id"] for b in st.session_state.current_featured_books}

    fresh = pool[~pool["id"].isin(excludes)]
    src = fresh if len(fresh) >= n else pool
    selected = src.sample(n=min(n, len(src)))
    return selected.to_dict(orient="records")


def recommend_books(
    n: int,
    cat: Optional[str] = None,
    exclude_ids: Optional[Set[str]] = None,
    db_path: str | Path | None = None,
) -> List[Dict[str, Any]]:
    """Kategori, öncelikli seri kotası ve akşam kurallarına göre n kitap önerir."""
    if cat and cat != "Tümü":
        pool = get_unread_pool(cat, db_path=db_path)
        return sample_books(pool, n, exclude_ids) if len(pool) > 0 else []

    base = get_pool_df(db_path=db_path)
    if len(base) == 0:
        return []

    all_logs = get_all_logs(db_path)
    pending_ids = {l["book_id"] for l in all_logs if is_pending(l)}
    unread = base[(base["read_count"] == 0) & (~base["id"].isin(pending_ids))]
    pri = priority_books(base, db_path=db_path)
    pri_unread = pri[(pri["read_count"] == 0) & (~pri["id"].isin(pending_ids))]

    if not priority_keys(db_path) or len(pri_unread) == 0:
        pool = unread if len(unread) > 0 else base
        return sample_books(pool, n, exclude_ids)

    k = min(priority_quota_left(db_path), n, len(pri_unread))
    picks = sample_books(pri_unread, k, exclude_ids) if k > 0 else []
    rest = unread[~unread["id"].isin(pri_unread["id"])]
    if len(rest) == 0:
        rest = base[~base["id"].isin(pri_unread["id"])]

    if n - k > 0 and len(rest) > 0:
        picks += sample_books(rest, n - k, exclude_ids)

    return picks


def spin_wheel(db_path: str | Path | None = None) -> List[Dict[str, Any]]:
    """Sihirli Çark: bugünün kalan hedefi kadar kitap seçer (hedef bittiyse 1 bonus)."""
    gs = goal_status(db_path)
    n = gs["remaining"] if gs["remaining"] > 0 else 1
    picks = recommend_books(n, db_path=db_path)
    return picks


def random_pick(n: int = 4, db_path: str | Path | None = None) -> List[Dict[str, Any]]:
    """Rastgele öneri: 4 kitap seçer."""
    return recommend_books(n, db_path=db_path)
