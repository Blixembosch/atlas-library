"""Atlas Library - 1. Ana Sayfa."""

import streamlit as st

from services.book_service import get_books_df
from services.reading_service import (
    get_all_logs,
    approved_logs,
    atlas_logs,
    period_counts,
    goal_status,
    calculate_level,
)
from services.recommendation_service import (
    priority_progress,
    series_label,
    priority_keys,
    priority_per_day,
    evening_no_dutch,
    recommend_books,
    spin_wheel,
    random_pick,
)
from ui.components import render_hero, book_card
from ui.audio import play_celebration


def render_home_page() -> None:
    books_df = get_books_df()
    home_df = books_df[books_df["is_school"] == 0]
    eligible_df = home_df[home_df["is_outgrown"] == 0]

    all_logs = get_all_logs()
    logs_data = approved_logs(all_logs)
    own_counts = period_counts(atlas_logs(all_logs))

    total_read_books = int((books_df["read_count"] > 0).sum())
    lvl = calculate_level(total_read_books)
    gs = goal_status()

    # Session state başlangıçları
    if "home_active_category" not in st.session_state:
        st.session_state.home_active_category = "Tümü"
    if "current_featured_books" not in st.session_state:
        st.session_state.current_featured_books = []
    if "featured_note" not in st.session_state:
        st.session_state.featured_note = ""
    if "goal_celebrated" not in st.session_state:
        st.session_state.goal_celebrated = ""

    # Hero Kutusu
    render_hero(gs, lvl, own_counts)

    # Hedef tamamlanınca günde bir kez kutlama
    if gs["done"] >= gs["goal"] and st.session_state.goal_celebrated != gs["today_iso"]:
        st.session_state.goal_celebrated = gs["today_iso"]
        play_celebration()
        st.balloons()

    # Çark ve Rastgele Butonları
    hb1, hb2, _sp = st.columns([1, 1, 3])
    if hb1.button("🎡 Sihirli Çark", key="btn_hero_wheel"):
        picks = spin_wheel()
        if picks:
            st.session_state.current_featured_books = picks
            st.session_state.featured_note = (
                f"🎡 Çark bugün için {len(picks)} kitap seçti!"
                if gs["remaining"] > 0
                else "🎉 Bugünkü hedef tamam! Çark sana 1 bonus kitap seçti."
            )
            st.rerun()

    if hb2.button("📚 Rastgele Öner", key="btn_hero_random"):
        picks = random_pick()
        if picks:
            st.session_state.current_featured_books = picks
            st.session_state.featured_note = "📚 Senin için 4 macera seçtik!"
            st.rerun()

    # Bilgilendirme Notları
    pp = priority_progress()
    if pp and pp[0] < pp[1]:
        pkeys_str = ", ".join(series_label(k).split(" ", 1)[-1] for k in priority_keys())
        st.caption(
            f"🔤 **Öncelikli seri turu ({pkeys_str}):** {pp[0]}/{pp[1]} kitap okundu. "
            f"Tur bitene kadar çark ve öneriler günde {priority_per_day()} kitap bu serilerden önerir."
        )

    st.caption(
        "🌙 Saat 19:00’dan sonra uyku öncesi huzur için Aktivite"
        + (" ve Dutch kitaplar" if evening_no_dutch() else "")
        + " haricindeki kitaplar seçilir."
    )

    st.markdown("#### ✨ Keşfetmek İstediğin Dünyayı Seç")
    categories = [
        ("🌟", "Tümü"),
        ("🐉", "Hikaye"),
        ("🚀", "Bilgi & Keşif"),
        ("💡", "İlk Okuma"),
        ("🌍", "Doğa & Hayvanlar"),
        ("🔬", "Bilim"),
        ("💛", "Değerler"),
    ]

    cat_cols = st.columns(len(categories))
    for idx, (icon, cat_name) in enumerate(categories):
        with cat_cols[idx]:
            is_active = st.session_state.home_active_category == cat_name
            label = f"{icon} {cat_name}"
            btn_type = "primary" if is_active else "secondary"
            if st.button(label, key=f"cat_btn_{cat_name}", type=btn_type):
                st.session_state.home_active_category = cat_name
                st.session_state.current_featured_books = recommend_books(4, cat=cat_name)
                st.session_state.featured_note = f"📂 '{cat_name}' dünyasından kitaplar:"
                st.rerun()

    st.markdown("---")

    # Önerilen Kitaplar
    note = st.session_state.featured_note or "⭐ Senin İçin Seçtiklerimiz"
    st.markdown(f"#### {note}")

    featured = st.session_state.current_featured_books
    if not featured:
        featured = recommend_books(gs["goal"], cat=st.session_state.home_active_category)
        st.session_state.current_featured_books = featured

    if featured:
        f_cols = st.columns(4)
        for idx, b_item in enumerate(featured[:4]):
            with f_cols[idx]:
                live = books_df[books_df["id"] == b_item["id"]]
                book_card(live.iloc[0] if len(live) else b_item, "home_feat", 170)

    # Son Okunanlar
    st.markdown("#### 📖 Son Maceraların")
    title_map = dict(zip(books_df["id"], books_df["title"]))
    school_ids = set(books_df.loc[books_df["is_school"] == 1, "id"])
    recent, seen = [], set()

    for l in sorted(logs_data, key=lambda x: x.get("read_at") or "", reverse=True):
        bid = l.get("book_id")
        if bid in title_map and bid not in seen:
            seen.add(bid)
            recent.append((
                title_map[bid],
                (l.get("read_at") or "")[:10],
                bid in school_ids,
                int(l.get("by_atlas") or 0) == 1,
            ))
        if len(recent) == 5:
            break

    if recent:
        for t, d, sch, own in recent:
            icon = "🏫" if sch else "📖"
            own_str = " &nbsp;👦 (Kendim okudum)" if own else ""
            st.markdown(
                f'<div class="recent-item"><div>{icon} <b>{t}</b>{own_str}</div><span>{d}</span></div>',
                unsafe_allow_html=True,
            )
    else:
        st.info("Henüz okunan kitap yok. İlk maceranı başlat! 🚀")

render_page = render_home_page


if __name__ == "__main__":
    render_page()
