"""Atlas Library - 5. Anı Defteri (Reading Memories)."""

import streamlit as st

from services.book_service import get_books_df
from services.memory_service import (
    add_memory,
    get_memories,
    delete_memory,
    get_memory_stats,
)
from ui.components import render_memory_card


def render_memories_page() -> None:
    st.markdown("### ✨ Atlas'ın Sihirli Anı Defteri")
    st.markdown(
        "Birlikte okuduğumuz kitaplardan kalan unutulmaz anılar, sevilen karakterler, "
        "Atlas'ın komik/özel yorumları ve favori alıntılar burada saklanır."
    )

    stats = get_memory_stats()
    s1, s2, s3 = st.columns(3)
    s1.metric("Toplam Anı", stats["total_memories"])
    s2.metric("Unutulmaz Alıntı", stats["quotes_count"])
    s3.metric("Ortalama Puan", f"⭐ {stats['avg_rating']}")

    st.markdown("---")

    # Yeni Anı Ekleme Formu
    with st.expander("➕ Yeni Bir Okuma Anısı Ekle", expanded=False):
        books_df = get_books_df()
        book_options = {
            f"{r['title']} ({r.get('author', 'Bilinmiyor')})": r["id"]
            for _, r in books_df.sort_values("title").iterrows()
        }

        with st.form("add_memory_form"):
            selected_label = st.selectbox("Hangi kitap hakkında?", list(book_options.keys()))
            b_id = book_options[selected_label]
            note = st.text_area(
                "Atlas'ın Yorumu / Birlikte Yaşanan Anı",
                placeholder="Örn: Bu kitabı okurken ejderhanın sesini taklit edip çok güldük...",
            )
            quote = st.text_input(
                "Favori Cümle / Alıntı (İsteğe bağlı)",
                placeholder="Örn: 'En büyük güç sevgiyle başlar.'",
            )
            rating = st.slider("Atlas'ın Puanı", min_value=1, max_value=5, value=5)

            if st.form_submit_button("✨ Anıyı Kaydet"):
                if note.strip():
                    add_memory(b_id, note, favorite_quote=quote, rating=rating)
                    st.toast("Anı başarıyla deftere eklendi! 🎉", icon="📖")
                    st.rerun()
                else:
                    st.warning("Lütfen bir anı veya not yazın.")

    # Kayıtlı Anılar
    memories = get_memories()
    if not memories:
        st.info("Henüz eklenmiş bir okuma anısı yok. Yukarıdaki formdan ilk anınızı kaydedin! 🎈")
        return

    st.markdown(f"#### 📚 Biriken Anılar ({len(memories)})")

    # Filtreleme
    f1, f2 = st.columns([2, 1])
    search_q = f1.text_input("🔍 Anılarda ara", placeholder="Kitap veya anı metni...", key="mem_search")
    min_rating = f2.selectbox("Yıldız Filtresi", ["Tümü", "5 Yıldızlılar", "4+ Yıldızlılar"], key="mem_stars")

    filtered = memories
    if search_q.strip():
        sq = search_q.strip().lower()
        filtered = [
            m for m in filtered
            if sq in m.get("note", "").lower()
            or sq in m.get("favorite_quote", "").lower()
            or sq in m.get("book_title", "").lower()
        ]

    if min_rating == "5 Yıldızlılar":
        filtered = [m for m in filtered if int(m.get("rating", 0)) == 5]
    elif min_rating == "4+ Yıldızlılar":
        filtered = [m for m in filtered if int(m.get("rating", 0)) >= 4]

    st.write(f"**{len(filtered)}** anı listeleniyor.")

    for m in filtered:
        c_left, c_right = st.columns([9, 1])
        with c_left:
            render_memory_card(m)
        with c_right:
            if st.button("🗑️", key=f"del_mem_{m['id']}", help="Bu anıyı sil"):
                delete_memory(m["id"])
                st.toast("Anı silindi.", icon="🗑️")
                st.rerun()

render_page = render_memories_page


if __name__ == "__main__":
    render_page()
