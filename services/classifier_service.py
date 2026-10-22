"""Atlas Library - Dil, Kategori ve Seri Sınıflandırma Servisi."""

from __future__ import annotations

import csv
import re
from typing import Dict, List, Optional, Tuple, Any

from core.config import (
    CATEGORY_REVIEW_FILE,
    NL_WORDS,
    NL_PUBLISHERS,
    SCAN_KW_STRONG,
    SCAN_KW,
    SCAN_RANK,
)


def tr_lower(text: Any) -> str:
    """Türkçe karakterlere (İ/ı) duyarlı küçük harfe çevirme."""
    return str(text).replace("İ", "i").replace("I", "ı").lower()


def looks_dutch(title: str, publisher: str = "") -> bool:
    """Başlık veya yayınevine bakarak kitabın Hollandaca olup olmadığını tespit eder."""
    words = set(re.findall(r"[a-zçğıöşü']+", str(title).lower()))
    is_word_match = bool(words & NL_WORDS)
    is_pub_match = str(publisher).strip().lower() in NL_PUBLISHERS
    return is_word_match or is_pub_match


def foreign_learning_language(title: str) -> Optional[str]:
    """Yabancı dil öğreten kitaplar (Almanca / İngilizce) için dil adını tespit eder."""
    t = str(title).lower()
    if "almanca" in t or "deutsch" in t:
        return "German"
    if "first words" in t or "i̇ngilizce" in t or "ingilizce" in t:
        return "English"
    return None


def akilli_kategori_belirle(title: str, author: str = "", subcategory: str = "") -> Optional[str]:
    """Kitap bilgilerine göre temel kategori tahmini yapar (Cin Ali serisi İlk Okuma)."""
    combined = f"{str(title).lower()} {str(author).lower()} {str(subcategory).lower()}"
    if "çin ali" in combined or "cin ali" in combined:
        return "İlk Okuma"
    return None


def load_category_reviews() -> Dict[str, Tuple[str, str, str]]:
    """category_review.csv dosyasından incelenmiş kitapları sözlük olarak yükler."""
    reviews: Dict[str, Tuple[str, str, str]] = {}
    if not CATEGORY_REVIEW_FILE.exists():
        return reviews

    try:
        with open(CATEGORY_REVIEW_FILE, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                b_id = row.get("id") or row.get("ID")
                new_cat = row.get("new_category") or row.get("Önerilen")
                reason = row.get("reason") or row.get("Gerekçe", "")
                conf = row.get("confidence") or row.get("Güven", "orta")
                if b_id and new_cat:
                    reviews[b_id.strip()] = (new_cat.strip(), reason.strip(), conf.strip())
    except Exception:
        pass
    return reviews


def auto_category_scan(df: Any) -> List[Dict[str, Any]]:
    """Seri tutarlılığı ve başlık sözcüklerine göre ücretsiz kategori taraması yapar."""
    # Sadece ev kitapları
    d = df[df["is_school"] == 0] if "is_school" in df.columns else df
    out: Dict[str, Dict[str, Any]] = {}
    reviewed_ids = set(load_category_reviews().keys())

    def add(r: Any, cat: str, why: str, conf: str) -> None:
        if cat == r["category"] or cat == "İlk Okuma" or r["category"] == "İlk Okuma":
            return
        old = out.get(r["id"])
        if old is None or SCAN_RANK.get(conf, 1) > SCAN_RANK.get(old.get("Güven", "düşük"), 1):
            out[r["id"]] = {
                "ID": r["id"],
                "Kitap": r["title"],
                "Şimdi": r["category"],
                "Önerilen": cat,
                "Gerekçe": why,
                "Güven": conf,
            }

    # Seri tutarlılığı: ":" öncesi ön ek taşıyan >= 4 kitapta %75+ çoğunluk kategori
    pref = d["title"].map(lambda t: str(t).split(":")[0].strip() if ":" in str(t) else "")
    maj: Dict[str, str] = {}
    for p, g in d[pref != ""].groupby(pref[pref != ""]):
        if len(g) >= 4:
            top = g["category"].value_counts()
            if top.iloc[0] / len(g) >= 0.75:
                maj[p] = top.index[0]

    for _, r in d.iterrows():
        b_id = str(r["id"])
        if b_id in reviewed_ids:
            continue

        t = tr_lower(r["title"])
        if any(w in t for w in SCAN_KW_STRONG):
            add(r, "Aktivite", "Başlıkta etkinlik/oyun sözcüğü var", "yüksek")

        p = str(r["title"]).split(":")[0].strip() if ":" in str(r["title"]) else ""
        if p in maj:
            add(r, maj[p], f"'{p}' serisinin çoğu {maj[p]}", "orta")
            continue

        toks = re.findall(r"[a-zçğıöşü]+", t)
        for cat, ws in SCAN_KW.items():
            hit = [w for w in ws if any(k.startswith(w) and len(k) <= len(w) + 3 for k in toks)]
            if hit:
                add(r, cat, f"Başlıkta '{hit[0]}' geçiyor", "düşük")
                break

    res = sorted(out.values(), key=lambda x: (-SCAN_RANK.get(x["Güven"], 1), x["Kitap"]))
    return res
