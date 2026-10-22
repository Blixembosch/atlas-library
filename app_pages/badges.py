"""Atlas Library - 4. Başarı Rozetleri."""

import streamlit as st

from core.config import GENERAL_BADGES, OWN_READING_BADGES
from services.book_service import get_books_df
from services.reading_service import (
    get_all_logs,
    atlas_logs,
    period_counts,
    calculate_level,
)
from ui.components import level_bar_html


def render_page() -> None:
    st.markdown("### 🎖️ Atlas'ın Başarı Rozetleri")
    st.markdown("Okuduğun kitap sayısına göre kazandığın sihirli rozetler burada listelenir!")

    books_df = get_books_df()
    total_read = len(books_df[books_df["read_count"] > 0])
    lvl = calculate_level(total_read)

    all_logs = get_all_logs()
    own_counts = period_counts(atlas_logs(all_logs))
    own_total = own_counts["total"]

    c1, c2, c3 = st.columns(3)
    c1.markdown(f'<div class="stat-card"><small>LEVEL</small><div class="stat-val">⭐ {lvl["level"]}</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="stat-card"><small>XP</small><div class="stat-val">{lvl["xp"]}</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="stat-card"><small>İLERLEME</small>{level_bar_html(lvl)}</div>', unsafe_allow_html=True)

    # Genel Rozetler
    st.markdown("#### 🌟 Genel Okuma Rozetleri")
    r_cols = st.columns(3)
    for idx, (icon, title, desc, req) in enumerate(GENERAL_BADGES):
        with r_cols[idx % 3]:
            unlocked = total_read >= req
            bg = "#f0fdf4" if unlocked else "#f8fafc"
            border_c = "#bbf7d0" if unlocked else "#e2e8f0"
            status_txt = "✅ KAZANILDI!" if unlocked else f"🔒 {req} Kitap Gerekli"

            st.markdown(
                f"""
                <div style="background: {bg}; border: 1px solid {border_c}; border-radius: 20px; padding: 20px; text-align: center; margin-bottom: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.02);">
                    <div style="font-size: 3.5rem; margin-bottom: 5px;">{icon}</div>
                    <h4 style="color: #1e293b; margin: 5px 0; font-weight: 800;">{title}</h4>
                    <p style="color: #64748b; font-size: 0.85rem; margin-bottom: 10px;">{desc}</p>
                    <b style="font-size: 0.85rem; color: {'#15803d' if unlocked else '#94a3b8'};">{status_txt}</b>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # Kendi Başına Okuma Rozetleri
    st.markdown("---")
    st.markdown("#### 👦 Kendi Başına Okuyan Rozetleri")
    ob_cols = st.columns(4)
    for idx, (icon, title, desc, req) in enumerate(OWN_READING_BADGES):
        with ob_cols[idx % 4]:
            unlocked = own_total >= req
            bg = "#eff6ff" if unlocked else "#f8fafc"
            border_c = "#bfdbfe" if unlocked else "#e2e8f0"
            status_txt = "✅ KAZANILDI!" if unlocked else f"🔒 {req} kendi okuma"

            st.markdown(
                f"""
                <div style="background: {bg}; border: 1px solid {border_c}; border-radius: 20px; padding: 16px; text-align: center; margin-bottom: 15px;">
                    <div style="font-size: 2.8rem;">{icon}</div>
                    <h4 style="color: #1e293b; margin: 5px 0; font-weight: 800;">{title}</h4>
                    <p style="color: #64748b; font-size: 0.8rem; margin-bottom: 8px;">{desc}</p>
                    <b style="font-size: 0.8rem; color: {'#1d4ed8' if unlocked else '#94a3b8'};">{status_txt}</b>
                </div>
                """,
                unsafe_allow_html=True,
            )


if __name__ == "__main__":
    render_page()
