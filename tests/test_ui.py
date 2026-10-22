"""Tests for UI components, styles, covers, and audio."""

import unittest
from unittest.mock import patch
import pandas as pd

from ui.styles import get_app_css, get_admin_css
from ui.covers import get_cover_color, get_placeholder_cover_html
from ui.audio import play_chime, play_celebration
from ui.components import (
    level_bar_html,
    lang_card_html,
    hero_left_html,
    hero_right_html,
    show_table,
    render_hero,
    show_book_detail,
    book_card,
    render_memory_card,
)


class TestUI(unittest.TestCase):
    def test_styles(self):
        css = get_app_css()
        self.assertIn("--primary", css)
        self.assertIn(".book-card", css)

        admin_css = get_admin_css()
        self.assertIn(".admin-head", admin_css)

    def test_covers(self):
        bg, color = get_cover_color("Kitap Başlığı")
        self.assertTrue(bg.startswith("linear-gradient"))
        self.assertTrue(color.startswith("#"))

        html_cov = get_placeholder_cover_html("Uzay Yolculuğu", "Yazar Adı")
        self.assertIn("Uzay Yolculuğu", html_cov)
        self.assertIn("📖", html_cov)

        school_cov = get_placeholder_cover_html("Okul Kitabı", is_school=True)
        self.assertIn("🏫", school_cov)

    @patch("streamlit.components.v1.html")
    def test_audio(self, mock_html):
        play_chime()
        self.assertTrue(mock_html.called)

        play_celebration()
        self.assertEqual(mock_html.call_count, 2)

    def test_html_helpers(self):
        lv = {"xp": 100, "level": 2, "pct": 40, "to_next": 60}
        bar = level_bar_html(lv)
        self.assertIn("width:40%", bar)

        card = lang_card_html("Türkçe", {"month": 2, "year": 10, "total": 25})
        self.assertIn("Türkçe", card)
        self.assertIn("25", card)

        hl = hero_left_html({"goal": 2, "done": 1, "pending": 0, "remaining": 1, "streak": 3, "today_iso": "2026-10-23"})
        self.assertIn("Merhaba Atlas", hl)
        self.assertIn("Günün Görevi", hl)

        hr = hero_right_html({"xp": 50, "level": 1, "pct": 50, "to_next": 50}, {"total": 5, "month": 2, "year": 5})
        self.assertIn("Seviye 1", hr)
        self.assertIn("Kendim Okudum", hr)

        mem = {
            "book_title": "Minik Ayı",
            "rating": 5,
            "created_at": "2026-10-23T12:00:00",
            "note": "Çok sevdik",
            "favorite_quote": "Harika bir gün!",
        }
        mem_card = render_memory_card(mem)
        # render_memory_card uses st.markdown internally, so we test it calls cleanly

    @patch("streamlit.dataframe")
    def test_show_table(self, mock_df):
        df = pd.DataFrame([{"a": 1, "b": 2}])
        show_table(df)
        self.assertTrue(mock_df.called)

    @patch("streamlit.markdown")
    def test_render_hero(self, mock_md):
        gs = {"goal": 2, "done": 1, "pending": 0, "remaining": 1, "streak": 3, "today_iso": "2026-10-23"}
        lvl = {"xp": 50, "level": 1, "pct": 50, "to_next": 50}
        counts = {"total": 5, "month": 2, "year": 5}
        render_hero(gs, lvl, counts)
        self.assertTrue(mock_md.called)


if __name__ == "__main__":
    unittest.main()
