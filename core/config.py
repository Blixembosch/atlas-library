"""Atlas Library - Merkezi Yapılandırma ve Sabitler."""

from __future__ import annotations

import hmac
from pathlib import Path
from zoneinfo import ZoneInfo
try:
    import streamlit as st
except ImportError:
    st = None

# Dizin Yolları
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
SEED_FILE = DATA_DIR / "books.csv"
CATEGORY_REVIEW_FILE = BASE_DIR / "category_review.csv"

# Uygulama Bilgileri
APP_TITLE = "Atlas'ın Sihirli Kütüphanesi"
APP_ICON = "🏰"
APP_VERSION = "v2.0.2"
TZ = ZoneInfo("Europe/Amsterdam")

# Standart Kitap Kategorileri
CATEGORIES = [
    "Hikaye",
    "Bilgi & Keşif",
    "Aktivite",
    "İlk Okuma",
    "Doğa & Hayvanlar",
    "Bilim",
    "Değerler",
]

# Öneri ve Dil Ayarları
DEFAULT_REC_LANGS = ["Türkçe", "Dutch"]
PRIORITY_MODES = {
    "off": "Kapalı (öncelik yok)",
    "ilk_okuma": "İlk Okuma kategorisi (Cin Ali serisi)",
    "okuma_becerisi": "Okuma becerisi serileri (Cin Ali + İlk Okuma Kitabım Elif/Çağlar)",
}

# Kapak olarak kullanılmaması gereken logo/bozuk işaretler
BAD_COVER_MARKERS = ("longitood.com", "deneyap-logo")

# Hollandaca Otomatik Tespit Sözlüğü
NL_WORDS = {
    "een", "het", "naar", "voor", "mijn", "groot", "zoek", "gaat", "verstopt",
    "kleine", "kamperen", "camping", "slaapmuisjes", "beertjes", "tijd", "staan",
    "school", "samen", "vrienden", "dapper", "willewete", "nijntje", "mama",
    "opa", "oma", "niet", "jij", "drie", "olifant",
}
NL_PUBLISHERS = {
    "kluitman", "studio 100", "borre educatief", "de vuurvlinder", "zwijsen",
    "lemniscaat", "gottmer", "querido", "clavis", "ploegsma", "leopold",
    "mercis", "van holkema & warendorf", "deltas", "veltman",
}

# Otomatik Kategori Tarama Anahtar Kelimeleri
SCAN_KW_STRONG = ["satranç", "yoga", "boyama", "çıkartma", "bulmaca", "etkinlik", "labirent", "hamur"]
SCAN_KW = {
    "Bilim": [
        "uzay", "gezegen", "roket", "bilim", "deney", "robot", "atom", "elektrik",
        "enerji", "teknoloji", "fizik", "kimya", "geometri", "bilgisayar", "mühendis", "icat",
    ],
    "Doğa & Hayvanlar": [
        "hayvan", "orman", "kuş", "kedi", "köpek", "balık", "kelebek", "dinozor",
        "ağaç", "böcek", "penguen", "doğa",
    ],
    "Değerler": [
        "sevgi", "dostluk", "paylaş", "cesaret", "saygı", "dürüst", "nezaket", "kıskanç", "öfke",
    ],
}
SCAN_RANK = {"yüksek": 3, "orta": 2, "düşük": 1}

# Okuma Yolculuğu Durakları (Milestones)
MILESTONES = [
    ("🏠 Ev", 0),
    ("✈ Havalimanı", 5),
    ("🚂 Tren İstasyonu", 10),
    ("🏰 Şato", 20),
    ("🌳 Doğa", 35),
    ("🚀 Uzay", 50),
    ("🪐 Galaksi", 75),
]

# Rozet Tanımları (Genel & Kendi Başına Okuma)
GENERAL_BADGES = [
    ("🥉", "İlk Adım", "İlk kitabını okudun!", 1),
    ("🥈", "Kitap Kurdu", "5 kitap okumayı başardın!", 5),
    ("🥇", "Macera Uzmanı", "10 kitap okudun!", 10),
    ("👑", "Kütüphane Kralı", "25 kitap okudun!", 25),
    ("🌟", "Sihirli Kaşif", "50 kitaba ulaştın!", 50),
    ("🏰", "Efsane Okur", "Tüm kütüphaneyi fethettin!", 100),
]

OWN_READING_BADGES = [
    ("📘", "Kendi Kitabım", "İlk kitabını kendin okudun!", 1),
    ("🚀", "Bağımsız Okur", "5 kitabı kendin okudun!", 5),
    ("🦸", "Okuma Kahramanı", "10 kitabı kendin okudun!", 10),
    ("🏅", "Süper Okur", "25 kitabı kendin okudun!", 25),
]


def get_secret(key: str, default: str = "") -> str:
    """Streamlit secrets üzerinden güvenli değer okur."""
    try:
        val = st.secrets.get(key, default)
        return str(val) if val is not None else default
    except Exception:
        return default


def safe_compare(a: str, b: str) -> bool:
    """Timing-attack korumalı güvenli metin karşılaştırması."""
    return hmac.compare_digest(str(a).encode("utf-8"), str(b).encode("utf-8"))
