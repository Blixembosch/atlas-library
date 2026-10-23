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
    pct = lv.get("pct", 0)
    lvl_next = lv.get("level", 0) + 1
    to_next = lv.get("to_next", 0)
    return (
        f'<div class="xp-track"><div class="xp-fill" style="width:{pct}%"></div></div>'
        f'<div class="xp-text">Seviye {lvl_next}\'e {to_next} XP kaldı</div>'
    )


def lang_card_html(title: str, d: Optional[Dict[str, int]] = None) -> str:
    """Dillere göre okuma özet kartı HTML'i döner."""
    data = d or {"month": 0, "year": 0, "total": 0}
    return (
        f'<div class="lang-card"><div class="lang-title">{html.escape(title)}</div>'
        f'<div class="lang-row">'
        f'<div><b>{data["month"]}</b><span>Bu Ay</span></div>'
        f'<div><b>{data["year"]}</b><span>Bu Yıl</span></div>'
        f'<div><b>{data["total"]}</b><span>Toplam</span></div>'
        f'</div></div>'
    )


def show_table(df: pd.DataFrame, **kw: Any) -> None:
    """İçerik boyuna göre responsive tablo gösterimi."""
    n = len(df)
    h = int(min(max(38 + 35 * n, 110), 1450))
    st.dataframe(df, height=h, **kw)


def hero_welcome_html() -> str:
    """Hero alanının sol karşılama başlığı ve motivasyon metnini döner."""
    return "".join([
        '<div class="hero-welcome-dock">',
        '<div class="hero-heading">👋 Merhaba Atlas!</div>',
        '<div class="hero-subheading">Bugün yeni bir maceraya hazır mısın?</div>',
        '</div>',
    ])


def hero_mission_html(gs: Dict[str, Any]) -> str:
    """Hero alanının Günün Görevi cam kartı HTML'ini döner (Seviye kartı ile ikiz tasarım)."""
    goal = max(1, gs.get("goal", 2))
    done = gs.get("done", 0)
    pending = gs.get("pending", 0)
    remaining = gs.get("remaining", max(0, goal - done))
    streak = gs.get("streak", 0)

    pct = min(100, int((done / goal) * 100))

    if done >= goal:
        bonus = done - goal
        goal_msg = "🎉 Harikasın! Görev Tamam!" + (f" (+{bonus} bonus)" if bonus > 0 else "")
    elif pending > 0:
        goal_msg = "⏳ Okuma kaydedildi, onayda"
    else:
        goal_msg = f"✨ Hedefe {remaining} kitap kaldı"

    streak_badge = (
        f'<div class="achieve-xp-badge streak-badge">🔥 {streak} Gün Seri</div>'
        if streak > 0
        else '<div class="achieve-xp-badge streak-badge">✨ Günlük Hedef</div>'
    )

    if pending > 0:
        box2_emoji = "⏳"
        box2_num = pending
        box2_label = "Onay Bekliyor"
    elif remaining > 0:
        box2_emoji = "🎯"
        box2_num = remaining
        box2_label = "Kalan Hedef"
    else:
        box2_emoji = "🌟"
        box2_num = done - goal if done > goal else "✓"
        box2_label = "Bonus Macera" if done > goal else "Tamamlandı"

    return "".join([
        '<div class="hero-achievement-card hero-mission-card">',
        '<div class="achieve-header">',
        '<div class="achieve-level">🎯 Günün Görevi</div>',
        streak_badge,
        '</div>',
        f'<div class="achieve-title">{goal_msg}</div>',
        '<div class="hero-xp-track">',
        f'<div class="hero-xp-fill mission-fill" style="width:{pct}%"></div>',
        '</div>',
        '<div class="achieve-xp-info">',
        f'<span><b>{min(done, goal)} / {goal}</b> Kitap</span>',
        f'<b>%{pct} Tamamlandı</b>',
        '</div>',
        '<div class="achieve-stats-grid">',
        '<div class="achieve-stat-box">',
        '<span class="stat-emoji">📖</span>',
        '<div>',
        f'<div class="stat-num">{done}</div>',
        '<div class="stat-label">Bugün Okundu</div>',
        '</div>',
        '</div>',
        '<div class="achieve-stat-box">',
        f'<span class="stat-emoji">{box2_emoji}</span>',
        '<div>',
        f'<div class="stat-num">{box2_num}</div>',
        f'<div class="stat-label">{box2_label}</div>',
        '</div>',
        '</div>',
        '</div>',
        '</div>',
    ])


def hero_left_html(gs: Dict[str, Any]) -> str:
    """Hero alanının sol karşılama, hedef ve görev çubuğu HTML'ini döner."""
    done = gs.get("done", 0)
    goal = gs.get("goal", 2)
    pending = gs.get("pending", 0)
    remaining = gs.get("remaining", max(0, goal - done))
    streak = gs.get("streak", 0)

    slots = "".join(
        '<div class="goal-slot done">⭐</div>'
        if i < done
        else (
            '<div class="goal-slot wait">⏳</div>'
            if i < done + pending
            else '<div class="goal-slot"></div>'
        )
        for i in range(goal)
    )

    if done >= goal:
        bonus = done - goal
        goal_msg = "🎉 Süpersin! Bugünkü hedefini tamamladın!" + (f" (+{bonus} bonus)" if bonus > 0 else "")
    elif pending > 0:
        goal_msg = "⏳ Okuman kaydedildi, ebeveyn onayı bekleniyor."
    else:
        goal_msg = f"✨ Bugün {remaining} kitap daha okuyarak hedefini tamamla!"

    streak_html = (
        f'<span class="goal-streak">🔥 {streak} gün seri</span>'
        if streak > 0
        else ""
    )

    return "".join([
        '<div class="hero-left-zone">',
        '<div class="hero-heading-row">',
        '<div class="hero-heading">👋 Merhaba Atlas!</div>',
        streak_html,
        '</div>',
        '<div class="hero-mission-bar">',
        '<span class="mission-title">🎯 Günün Görevi:</span>',
        f'<div class="mission-slots">{slots}</div>',
        f'<span class="mission-count"><b>{min(done, goal)} / {goal}</b> Kitap</span>',
        '<span class="mission-sep">•</span>',
        f'<span class="hero-subheading">{goal_msg}</span>',
        '</div>',
        '</div>',
    ])


def hero_right_html(lvl: Dict[str, int], own_counts: Dict[str, int]) -> str:
    """Hero alanının sağ oyunlaştırma ve başarı kartı HTML'ini döner."""
    level = lvl.get("level", 1)
    xp = lvl.get("xp", 0)
    pct = lvl.get("pct", 0)
    to_next = lvl.get("to_next", 0)

    titles = {
        1: "Kitap Kaşifi",
        2: "Macera Avcısı",
        3: "Hikaye Ustası",
        4: "Bilgi Büyücüsü",
        5: "Efsanevi Okur",
    }
    level_title = titles.get(level, "Sihirli Okur")

    return "".join([
        '<div class="hero-achievement-card">',
        '<div class="achieve-header">',
        f'<div class="achieve-level">⭐ Seviye {level}</div>',
        f'<div class="achieve-xp-badge">{xp} XP</div>',
        '</div>',
        f'<div class="achieve-title">{level_title}</div>',
        '<div class="hero-xp-track">',
        f'<div class="hero-xp-fill" style="width:{pct}%"></div>',
        '</div>',
        '<div class="achieve-xp-info">',
        f'<span>Seviye {level + 1} için</span>',
        f'<b>{to_next} XP kaldı</b>',
        '</div>',
        '<div class="achieve-stats-grid">',
        '<div class="achieve-stat-box">',
        '<span class="stat-emoji">👦</span>',
        '<div>',
        f'<div class="stat-num">{own_counts.get("total", 0)}</div>',
        '<div class="stat-label">Kendim Okudum</div>',
        '</div>',
        '</div>',
        '<div class="achieve-stat-box">',
        '<span class="stat-emoji">📅</span>',
        '<div>',
        f'<div class="stat-num">{own_counts.get("month", 0)}</div>',
        '<div class="stat-label">Bu Ay Toplam</div>',
        '</div>',
        '</div>',
        '</div>',
        '</div>',
    ])


def render_hero(gs: Dict[str, Any], lvl: Dict[str, int], own_counts: Dict[str, int]) -> None:
    """Ana sayfa için renkli tebrik, görev ve seviye kutularını çizer."""
    col_l, col_m, col_r = st.columns([1.3, 1.0, 1.0], gap="medium")
    with col_l:
        st.markdown(hero_welcome_html(), unsafe_allow_html=True)
    with col_m:
        st.markdown(hero_mission_html(gs), unsafe_allow_html=True)
    with col_r:
        st.markdown(hero_right_html(lvl, own_counts), unsafe_allow_html=True)


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
    if st.button("📖 Hemen Oku", key=f"{prefix}_{b_dict['id']}", use_container_width=True):
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
