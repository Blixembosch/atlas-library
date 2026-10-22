"""Atlas Library - Open Library API ile ISBN Kitap Bilgisi Servisi."""

from __future__ import annotations

from typing import Any, Dict, Optional
try:
    import requests
except ImportError:
    requests = None

try:
    import streamlit as st
    cache_fn = st.cache_data(ttl=3600)
except Exception:
    def cache_fn(f):
        return f


@cache_fn
def fetch_book_by_isbn(isbn: str) -> Optional[Dict[str, Any]]:
    """Open Library API kullanarak ISBN ile kitap bilgilerini çeker (1 saat önbellekli)."""
    clean_isbn = "".join(filter(str.isalnum, str(isbn)))
    if not clean_isbn:
        return None

    try:
        url = f"https://openlibrary.org/isbn/{clean_isbn}.json"
        res = requests.get(url, timeout=6)
        if res.status_code == 200:
            data = res.json()
            title = data.get("title", "")
            pages = data.get("number_of_pages")

            # Yazar bilgisi
            author = "Bilinmiyor"
            authors_data = data.get("authors", [])
            if authors_data:
                author_key = authors_data[0].get("key")
                if author_key:
                    try:
                        author_res = requests.get(f"https://openlibrary.org{author_key}.json", timeout=4)
                        if author_res.status_code == 200:
                            author = author_res.json().get("name", "Bilinmiyor")
                    except Exception:
                        pass

            # Yayınevi
            publishers = data.get("publishers", ["De Vuurvlinder"])
            publisher = publishers[0] if publishers else "De Vuurvlinder"

            # Kapak resmi
            covers = data.get("covers", [])
            cover_url = f"https://covers.openlibrary.org/b/id/{covers[0]}-L.jpg" if covers else ""

            return {
                "title": title,
                "author": author,
                "publisher": publisher,
                "pages": int(pages) if pages else None,
                "cover_url": cover_url,
                "isbn": clean_isbn,
            }
    except Exception:
        pass
    return None
