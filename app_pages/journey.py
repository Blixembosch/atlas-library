"""Atlas Library - 3. Okuma Yolculuğu ve Detaylı İstatistikler."""

import pandas as pd
import streamlit as st

from core.config import MILESTONES
from services.book_service import get_books_df
from services.reading_service import (
    get_all_logs,
    approved_logs,
    atlas_logs,
    period_counts,
    language_read_summary,
)
from ui.components import lang_card_html


def render_journey_page() -> None:
    st.markdown("### 🏆 Okuma Karnesi ve Detaylı İstatistikler")

    books_df = get_books_df()
    home_df = books_df[books_df["is_school"] == 0]
    total_read_books = int((books_df["read_count"] > 0).sum())

    all_logs = get_all_logs()
    logs_data = approved_logs(all_logs)
    own_counts = period_counts(atlas_logs(all_logs))

    # Milestones (Duraklar)
    cur_idx = max(i for i, (_, req) in enumerate(MILESTONES) if total_read_books >= req)
    stops = []
    for i, (label, req) in enumerate(MILESTONES):
        state = "done" if i < cur_idx else ("now" if i == cur_idx else "lock")
        icon, name = label.split(" ", 1)
        sub = {"done": "✅ Tamamlandı", "now": "📍 Buradasın", "lock": f"🔒 {req} kitap"}[state]
        stops.append(
            f'<div class="stop {state}"><div class="stop-icon">{icon}</div>{name}<small>{sub}</small></div>'
        )
    st.markdown(f'<div class="journey">{"".join(stops)}</div>', unsafe_allow_html=True)

    if cur_idx < len(MILESTONES) - 1:
        nxt_label, nxt_req = MILESTONES[cur_idx + 1]
        prev_req = MILESTONES[cur_idx][1]
        st.progress(
            min((total_read_books - prev_req) / (nxt_req - prev_req), 1.0),
            text=f"{nxt_label} durağına {nxt_req - total_read_books} kitap kaldı",
        )
    else:
        st.success("🪐 Tüm durakları tamamladın!")

    st.markdown("---")

    # Metrikler
    total_books_count = len(home_df)
    read_books_df = books_df[books_df["read_count"] > 0]
    total_read_count = len(read_books_df)
    home_read_count = int((home_df["read_count"] > 0).sum())
    school_read_count = total_read_count - home_read_count
    total_pages_read = int((read_books_df["pages"].fillna(0) * read_books_df["read_count"]).sum())

    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        st.metric(label="Toplam Okunan Kitap", value=f"{total_read_count}")
        st.caption(f"🏡 {home_read_count} ev · 🏫 {school_read_count} okul")
        home_pct = home_read_count / max(total_books_count, 1)
        st.progress(home_pct, text=f"Ev kütüphanesi %{round(home_pct * 100, 1)}")

    with col_m2:
        st.metric(label="Toplam Okunan Sayfa", value=f"{total_pages_read} Sayfa 📄")

    with col_m3:
        stories = home_df[home_df["category"] == "Hikaye"]
        story_done = len(stories[stories["read_count"] > 0])
        st.metric(label="Tamamlanan Hikâyeler", value=f"{story_done} / {len(stories)}")
        st.progress(
            story_done / max(len(stories), 1),
            text=f"%{round((story_done / max(len(stories), 1)) * 100, 1)}",
        )

    # Dil Dağılımı
    st.markdown("---")
    st.markdown("#### 🌍 Hangi Dilde Okudum?")
    lang_sum = language_read_summary(logs_data, books_df)
    lang_cols = st.columns(3 if "Diğer" in lang_sum else 2)
    lang_cols[0].markdown(lang_card_html("🇹🇷 Türkçe", lang_sum.get("Türkçe")), unsafe_allow_html=True)
    lang_cols[1].markdown(lang_card_html("🇳🇱 Dutch", lang_sum.get("Dutch")), unsafe_allow_html=True)
    if "Diğer" in lang_sum:
        lang_cols[2].markdown(lang_card_html("🌍 Diğer", lang_sum["Diğer"]), unsafe_allow_html=True)
    st.caption("Her okuma kaydı bir kez sayılır (aynı kitabı tekrar okumak da dahil).")

    # Kendi Başıma Okuduklarım
    st.markdown("---")
    st.markdown("#### 👦 Kendi Başıma Okuduklarım")
    own_c1, own_c2 = st.columns(2)
    own_c1.markdown(lang_card_html("👦 Atlas okudu", own_counts), unsafe_allow_html=True)
    own_share = own_counts["total"] / max(len(logs_data), 1)
    own_c2.progress(
        min(own_share, 1.0),
        text=f"Tüm okumaların %{round(own_share * 100)}'ini kendim okudum",
    )
    own_c2.caption("Anne/baba onaylarken 'Atlas okudu' işaretlediği kitaplar. Toplam okumaya da dahildir.")

    # Kategori Dağılımı
    st.markdown("---")
    st.markdown("#### 📊 Kategoriye Göre Okuma Dağılımı")
    cat_groups = (
        home_df.groupby("category")
        .agg(Toplam=("id", "count"), Okunan=("read_count", lambda x: (x > 0).sum()))
        .reset_index()
    )

    cat_cols = st.columns(len(cat_groups) if len(cat_groups) > 0 else 1)
    for idx, row in cat_groups.iterrows():
        c_name = row["category"]
        c_tot = row["Toplam"]
        c_done = row["Okunan"]
        c_perc = c_done / c_tot if c_tot > 0 else 0
        with cat_cols[idx % len(cat_cols)]:
            st.markdown(
                f"""
                <div class="cat-box">
                    <h4 style="color: #4f46e5; margin-bottom: 5px; font-weight: 800;">📂 {c_name}</h4>
                    <p style="font-size: 0.9rem; color: #64748b; margin-bottom: 10px;">Okunan: <b>{c_done}</b> / Toplam: <b>{c_tot}</b></p>
                    <div style="background: #e2e8f0; border-radius: 99px; height: 10px; width: 100%; overflow: hidden;">
                        <div style="background: #6366f1; height: 100%; width: {c_perc * 100}%;"></div>
                    </div>
                    <p style="font-size: 0.8rem; color: #94a3b8; margin-top: 5px;">%{round(c_perc * 100, 1)} Tamamlandı</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

render_page = render_journey_page


if __name__ == "__main__":
    render_page()
