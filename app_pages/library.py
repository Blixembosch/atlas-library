"""Atlas Library - 2. Kütüphane Arşivi."""

import streamlit as st

from core.config import CATEGORIES
from services.book_service import get_books_df, filter_books
from ui.components import book_card


def render_library_page() -> None:
    st.markdown("### 📖 Kütüphane Arşivi")

    books_df = get_books_df()
    home_df = books_df[books_df["is_school"] == 0]

    all_publishers = sorted(
        {str(p).strip() for p in home_df["publisher"].dropna() if str(p).strip() != ""}
    )

    col_s1, col_s2, col_s3, col_s4 = st.columns([2, 1, 1, 1])
    with col_s1:
        search_query = st.text_input(
            "Kitap veya Yazar Ara",
            placeholder="Kelime yazın...",
            key="lib_search",
        )
    with col_s2:
        pub_filter = st.selectbox(
            "Yayınevi Filtrele",
            ["Tümü"] + all_publishers,
            key="lib_pub_select",
        )
    with col_s3:
        cat_options = ["Tümü"] + CATEGORIES
        cat_filter = st.selectbox(
            "Kategori Filtrele",
            cat_options,
            key="lib_cat",
        )
    with col_s4:
        age_filter = st.selectbox(
            "Yaş Uygunluğu",
            ["Uygun olanlar", "Tümü", "Yaşı geçenler"],
            key="lib_age",
        )

    filtered_lib = filter_books(
        home_df,
        search_query=search_query,
        publisher=pub_filter,
        category=cat_filter,
        age_filter=age_filter,
    )

    st.write(f"📚 Toplam **{len(filtered_lib)}** kitap listeleniyor.")

    # 4 Kolonlu Grid Gösterimi
    for start in range(0, len(filtered_lib), 4):
        cols = st.columns(4)
        for c_idx, (_, b) in enumerate(filtered_lib.iloc[start : start + 4].iterrows()):
            with cols[c_idx]:
                book_card(b, "lib_page", 210)

render_page = render_library_page


if __name__ == "__main__":
    render_page()
