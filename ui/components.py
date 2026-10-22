"""Atlas Library - Yeniden Kullanılabilir UI Bileşenleri."""

from __future__ import annotations

import html
from datetime import datetime
from typing import Any, Dict, Optional
import pandas as pd
import streamlit as st

from core.config import TZ
from services.book_service import get_books_df, get_clean_cover
from services.reading_service import (
    get_all_logs,
    approved_logs,
    is_pending,
    record_pending_read,
    record_manual_read,
)
from services.memory_service import add_memory, get_memories
from ui.covers import get_placeholder_cover_html
from ui.audio import play_chime


def level_bar_html(lv: Dict[str, int]) -> str:
    """XP ilerleme çubuğu HTML'i döner."""
    return f"""
    <div class="xp-track"><div class="xp-fill" style="width:{lv['pct']}%"></div></div>
    <div class="xp-text">Seviye {lv['level'] + 1}'e {lv['to_next']} XP kaldı</div>
    """


def lang_card_html(title: str, d: Optional[Dict[str, int]] = None) -> str:
    """Dillere göre okuma özet kartı HTML'i döner."""
    data = d or {"month": 0, "year": 0, "total": 0}
    return f"""
    <div class="lang-card">
        <div class="lang-title">{html.escape(title)}</div>
        <div class="lang-row">
            <div><b>{data['month']}</b><span>Bu Ay</span></div>
            <div><b>{data['year']}</b><span>Bu Yıl</span></div>
            <div><b>{data['total']}</b><span>Toplam</span></div>
        </div>
    </div>
    """


def show_table(df: pd.DataFrame, **kw: Any) -> None:
    """İçerik boyuna göre responsive tablo gösterimi."""
    n = len(df)
    h = int(min(max(38 + 35 * n, 110), 1450))
    st.dataframe(df, height=h, **kw)


def render_hero(gs: Dict[str, Any], lvl: Dict[str, int], own_counts: Dict[str, int]) -> None:
    """Ana sayfa için renkli tebrik, hedef ve seviye kutusunu çizer."""
    slots = "".join(
        '<div class="goal-slot done">✅</div>'
        if i < gs["done"]
        else (
            '<div class="goal-slot wait">⏳</div>'
            if i < gs["done"] + gs["pending"]
            else '<div class="goal-slot"></div>'
        )
        for i in range(gs["goal"])
    )

    if gs["done"] >= gs["goal"]:
        goal_msg = "🎉 Bugünkü görevi tamamladın!"
        if gs["done"] > gs["goal"]:
            goal_msg += f" (+{gs['done'] - gs['goal']} bonus)"
    elif gs["pending"] > 0:
        goal_msg = "⏳ Onay bekleniyor, annen ya da baban onaylayınca yuva dolar."
    else:
        goal_msg = f"Bugün {gs['remaining']} kitap daha oku!"

    streak_html = (
        f'<span class="goal-streak">🔥 {gs["streak"]} gün üst üste</span>'
        if gs["streak"] > 0
        else ""
    )

    hero_html = f"""
    <div class="hero-box">
        <div class="hero-top">
            <div class="hero-left">
                <div class="hero-title">👋 Merhaba Atlas</div>
                <div class="hero-goalline">
                    <span>🎯</span>
                    <div class="goal-slots">{slots}</div>
                    <b>{min(gs['done'], gs['goal'])}/{gs['goal']}</b>
                    {streak_html}
                </div>
                <div class="goal-msg">{goal_msg}</div>
            </div>
            <div class="hero-right">
                <b>⭐ Seviye {lvl['level']}</b>
                {level_bar_html(lvl)}
                <div class="hero-own">👦 Kendi okuduklarım: <b>{own_counts['total']}</b> · bu ay <b>{own_counts['month']}</b></div>
            </div>
        </div>
    </div>
    """
    st.markdown(hero_html, unsafe_allow_html=True)


@st.dialog("📖 Kitap Detayları ve Okuma İşlemleri", width="large")
def show_book_detail(b_id: str) -> None:
    """Kitap detaylarını, okuma onayını ve anı ekleme bölümünü gösteren modal."""
    fresh_df = get_books_df()
    b_row = fresh_df[fresh_df["id"] == b_id]
    if len(b_row) == 0:
        st.error("Kitap bulunamadı.")
        return

    b = b_row.iloc[0]
    c_img = get_clean_cover(b.get("cover_url"))
    is_sch = int(b.get("is_school", 0)) == 1

    all_logs = get_all_logs()
    all_book_logs = [l for l in all_logs if l.get("book_id") == b_id]
    book_logs = approved_logs(all_book_logs)
    today_iso = datetime.now(TZ).date().isoformat()
    has_pending = any(is_pending(l) for l in all_book_logs)
    read_today = any((l.get("read_at") or "")[:10] == today_iso for l in book_logs)

    last_read_time = "Henüz okunmadı"
    if book_logs:
        sorted_logs = sorted(book_logs, key=lambda x: x.get("read_at") or "", reverse=True)
        rat = sorted_logs[0].get("read_at")
        if rat:
            last_read_time = rat[:19].replace("T", " ")

    col_d1, col_d2 = st.columns([1, 2])
    with col_d1:
        if c_img:
            st.image(c_img)
        else:
            st.markdown(
                get_placeholder_cover_html(
                    b["title"], b.get("author", ""), is_school=is_sch, height=260
                ),
                unsafe_allow_html=True,
            )

    with col_d2:
        st.markdown(f"### {b['title']}")
        st.markdown(f"✍️ **Yazar:** {b.get('author', 'Bilinmiyor')}")
        st.markdown(f"🏢 **Yayınevi:** {b.get('publisher', 'Bilinmiyor')}")
        st.markdown(f"📌 **ISBN Numarası:** {b.get('isbn', 'Bulunmuyor')}")
        if pd.notna(b.get("pages")):
            st.markdown(f"📄 **Sayfa Sayısı:** {int(b['pages'])}")
        st.markdown(f"📂 **Kategori:** {b.get('category', '-')} &nbsp;|&nbsp; 🎯 **Yaş:** {b.get('age', '-')}")
        st.markdown(f"🌍 **Kitap Dili:** {b.get('language', 'Türkçe')}")
        st.markdown(f"🔄 **Toplam Okunma Sayısı:** {int(b.get('read_count', 0))}")
        st.markdown(f"⏱️ **En Son Okunma Tarihi:** {last_read_time}")

    st.markdown("---")

    # Çocuğun okudum butonu
    if has_pending:
        st.info("⏳ Okuman kaydedildi! Annen ya da baban onaylayınca XP kazanacaksın.")
    elif read_today:
        st.success("✅ Bu kitabı bugün zaten okudun. Yarın tekrar okuyabilirsin!")
    else:
        if st.button("✅ Okudum! 🎉", key=f"mark_read_{b_id}", type="primary"):
            success = record_pending_read(b_id)
            if success:
                play_chime()
                st.toast("Harika! Onay bekliyor ⏳", icon="🎉")
                st.rerun()

    # Anı Defteri Bölümü
    with st.expander("✨ Bu Kitap İçin Bir Anı / Not Ekle"):
        with st.form(f"mem_form_{b_id}"):
            m_note = st.text_area("Atlas'ın veya ebeveynin notu", placeholder="Bu kitapta en çok neyi sevdin?")
            m_quote = st.text_input("Unutulmaz Cümle / Alıntı", placeholder="Kitaptan güzel bir söz...")
            m_rating = st.slider("Kitap Puanı", min_value=1, max_value=5, value=5)
            if st.form_submit_button("📝 Anı Defterine Kaydet"):
                if m_note.strip():
                    add_memory(b_id, m_note, favorite_quote=m_quote, rating=m_rating)
                    st.toast("Anı Defterine eklendi! ✨", icon="📖")
                    st.rerun()
                else:
                    st.warning("Lütfen bir not yazın.")

    # Yönetici geçmiş tarihli ekleme
    if st.session_state.get("admin_logged_in", False):
        with st.expander("🔐 Yönetici: geçmiş tarihli okuma ekle"):
            with st.form(f"manual_read_form_{b_id}"):
                sel_date = st.date_input("Okunan Tarih Seçin", value=datetime.now(TZ).date())
                sel_time = st.time_input("Okunan Saat Seçin", value=datetime.now(TZ).time())
                manual_atlas = st.checkbox("👦 Atlas kendisi okudu", key=f"manual_atlas_{b_id}")
                if st.form_submit_button("📝 Bu Tarihle Okundu Olarak Kaydet"):
                    combined_dt = datetime.combine(sel_date, sel_time).isoformat()
                    record_manual_read(b_id, combined_dt, by_atlas=manual_atlas)
                    st.toast(f"'{b['title']}' {sel_date} tarihiyle kaydedildi! 🎉", icon="✅")
                    st.rerun()

    if st.button("Kapat", key=f"close_dialog_{b_id}"):
        st.rerun()


def book_card(b: pd.Series | Dict[str, Any], prefix: str, cover_h: int = 170) -> None:
    """Ortak kitap kartı bileşeni."""
    b_dict = b.to_dict() if hasattr(b, "to_dict") else dict(b)
    rc = int(b_dict.get("read_count", 0) or 0)
    img = get_clean_cover(b_dict.get("cover_url"))
    is_sch = int(b_dict.get("is_school", 0)) == 1

    if img:
        cover_html = f'<img src="{html.escape(img)}" alt="Kapak">'
    else:
        cover_html = get_placeholder_cover_html(
            b_dict["title"], b_dict.get("author", ""), is_school=is_sch, height=cover_h
        )

    badge = "⭐ Çok Sevildi" if rc >= 3 else ("🏷️ Yeni" if rc == 0 else "")
    if int(b_dict.get("is_outgrown", 0) or 0) == 1:
        badge = "🎒 Yaşı Geçti"

    badge_html = f'<div class="book-badge">{badge}</div>' if badge else ""
    school_badge_html = '<div class="school-badge">🏫 Okul Kitabı</div>' if is_sch else ""

    try:
        pages_num = float(b_dict.get("pages"))
        pages_line = "" if pd.isna(pages_num) else f"<br>📄 {int(pages_num)} Sayfa"
    except (TypeError, ValueError):
        pages_line = ""

    card_html = f"""
    <div class="book-card" style="height:{cover_h + 155}px">
        {badge_html}{school_badge_html}
        <div class="book-cover" style="height:{cover_h}px">{cover_html}</div>
        <div class="book-title">{html.escape(str(b_dict["title"]))}</div>
        <div class="book-meta">👶 {html.escape(str(b_dict.get("age", "-")))}{pages_line}<br>🔄 {rc} Kez Okundu</div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)
    if st.button("📖 Hemen Oku", key=f"{prefix}_{b_dict['id']}"):
        show_book_detail(b_dict["id"])


def render_memory_card(memory: Dict[str, Any]) -> None:
    """Anı Defteri kartını çizer."""
    stars = "⭐" * int(memory.get("rating", 5))
    dt_str = (memory.get("created_at") or "")[:10]
    b_title = memory.get("book_title") or "Bilinmeyen Kitap"
    quote = memory.get("favorite_quote", "")

    quote_html = f'<div class="memory-quote">“{html.escape(quote)}”</div>' if quote else ""

    card_html = f"""
    <div class="memory-card">
        <div class="memory-header">
            <div><b>📖 {html.escape(b_title)}</b> &nbsp; <span style="font-size:0.85rem;">{stars}</span></div>
            <span style="font-size:0.8rem; color:#94a3b8;">📅 {dt_str}</span>
        </div>
        <p style="margin: 6px 0; color:#334155; font-size:0.95rem;">{html.escape(memory.get('note', ''))}</p>
        {quote_html}
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)
