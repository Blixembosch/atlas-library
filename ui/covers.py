"""Atlas Library - Görseli Olmayan Kitaplar İçin Akıllı Dinamik Kapak Üretici."""

from __future__ import annotations

import hashlib
import html

# Çocuk kitaplarına uygun neşeli pastel renk paletleri
PASTEL_PALETTES = [
    ("linear-gradient(135deg, #FF9A9E 0%, #FECFEF 99%)", "#8B1E3F"),
    ("linear-gradient(135deg, #a1c4fd 0%, #c2e9fb 100%)", "#1E3A8A"),
    ("linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%)", "#9A3412"),
    ("linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%)", "#065F46"),
    ("linear-gradient(135deg, #e0c3fc 0%, #8ec5fc 100%)", "#5B21B6"),
    ("linear-gradient(135deg, #f093fb 0%, #f5576c 100%)", "#831843"),
    ("linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)", "#075985"),
    ("linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)", "#047857"),
    ("linear-gradient(135deg, #fa709a 0%, #fee140 100%)", "#9D174D"),
]


def get_cover_color(text: str) -> tuple[str, str]:
    """Kitap adı veya ID'sinden deterministik olarak tutarlı bir renk paleti seçer."""
    idx = int(hashlib.md5(str(text).encode("utf-8")).hexdigest(), 16) % len(PASTEL_PALETTES)
    return PASTEL_PALETTES[idx]


def get_placeholder_cover_html(
    title: str,
    author: str = "",
    is_school: bool = False,
    height: int = 170,
) -> str:
    """Kapağı olmayan kitaplar için şık, renkli ve kitap şeklinde HTML kart döner."""
    clean_title = html.escape(str(title))
    clean_author = html.escape(str(author or "Bilinmiyor"))

    if is_school:
        bg = "linear-gradient(135deg, #FDE68A 0%, #F59E0B 100%)"
        text_color = "#78350F"
        icon = "🏫"
    else:
        bg, text_color = get_cover_color(title)
        icon = "📖"

    return f"""
    <div style="
        width: 100%;
        height: {height}px;
        background: {bg};
        border-radius: 14px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        align-items: center;
        padding: 14px 10px;
        text-align: center;
        box-sizing: border-box;
        border: 2px solid rgba(255, 255, 255, 0.6);
        box-shadow: inset 0 0 10px rgba(0, 0, 0, 0.05);
    ">
        <div style="font-size: 2.2rem; line-height: 1;">{icon}</div>
        <div style="
            font-size: 0.85rem;
            font-weight: 800;
            color: {text_color};
            line-height: 1.2;
            max-height: 3.6em;
            overflow: hidden;
            display: -webkit-box;
            -webkit-line-clamp: 3;
            -webkit-box-orient: vertical;
        ">{clean_title}</div>
        <div style="
            font-size: 0.7rem;
            font-weight: 600;
            color: {text_color};
            opacity: 0.85;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 90%;
        ">{clean_author}</div>
    </div>
    """
