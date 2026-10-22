"""Atlas Library - Ana Uygulama ve Navigasyon."""

from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime
import streamlit as st

# Proje kök dizinini Python yoluna ekle
BASE = Path(__file__).resolve().parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from core.config import (
    APP_TITLE,
    APP_ICON,
    APP_VERSION,
    TZ,
    get_secret,
    safe_compare,
)
from core.db import init_db
from services.book_service import get_books_df
from services.reading_service import get_all_logs, approved_logs, period_counts
from ui.styles import get_app_css

# Sayfa Fonksiyonları
from app_pages.home import render_page as render_home
from app_pages.library import render_page as render_lib
from app_pages.journey import render_page as render_journey
from app_pages.badges import render_page as render_badges
from app_pages.memories import render_page as render_memories
from app_pages.admin import render_page as render_admin

# 1. Streamlit Sayfa Yapılandırması
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
)

# 2. Bulut Veritabanı ve Şema Başlatma
try:
    import cloud_db
    cloud_db.ensure_started()
except Exception as _e:
    pass

init_db()

# 3. CSS Stillerinin Yüklenmesi
st.markdown(get_app_css(), unsafe_allow_html=True)

# 4. Uygulama Giriş Şifresi Kontrolü
app_password = get_secret("APP_PASSWORD")
if "app_unlocked" not in st.session_state:
    st.session_state.app_unlocked = False

if app_password and not st.session_state.app_unlocked:
    _l1, _l2, _l3 = st.columns([1, 1.2, 1])
    with _l2:
        st.markdown(
            '<div style="text-align:center;margin-top:12vh"><div style="font-size:4rem">🏰</div>'
            '<h2>Atlas\'ın Sihirli Kütüphanesi</h2></div>',
            unsafe_allow_html=True,
        )
        with st.form("app_login_form"):
            _pw = st.text_input("Giriş şifresi", type="password", key="app_pw_input")
            _go = st.form_submit_button("Giriş", use_container_width=True)
        if _go:
            if safe_compare(_pw, app_password):
                st.session_state.app_unlocked = True
                st.rerun()
            else:
                st.error("Şifre hatalı.")
    st.stop()

# 5. Modern Sayfa Navigasyonu (st.navigation & st.Page)
p_home = st.Page(render_home, title="Ana Sayfa", icon="🏠", default=True)
p_lib = st.Page(render_lib, title="Kütüphane", icon="📖")
p_journey = st.Page(render_journey, title="Okuma Yolculuğu", icon="🏆")
p_badges = st.Page(render_badges, title="Rozetler", icon="🎖️")
p_memories = st.Page(render_memories, title="Anı Defteri", icon="✨")
p_admin = st.Page(render_admin, title="Yönetici Paneli", icon="⚙️")

nav = st.navigation([p_home, p_lib, p_journey, p_badges, p_memories, p_admin])

# 6. Sol Kenar Çubuğu (Sidebar)
with st.sidebar:
    st.markdown(
        f"""
        <div class="side-logo">
            <div class="side-logo-emoji">{APP_ICON}</div>
            <div class="side-logo-title">{APP_TITLE}</div>
            <div class="side-logo-sub">Keşfet • Oku • Hayal Et</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    books_df = get_books_df()
    home_df = books_df[books_df["is_school"] == 0]
    all_logs = get_all_logs()
    logs_data = approved_logs(all_logs)
    counts = period_counts(logs_data)

    turkce_aylar = {
        1: "Ocak", 2: "Şubat", 3: "Mart", 4: "Nisan", 5: "Mayıs", 6: "Haziran",
        7: "Temmuz", 8: "Ağustos", 9: "Eylül", 10: "Ekim", 11: "Kasım", 12: "Aralık",
    }
    cur_month_name = turkce_aylar.get(datetime.now(TZ).month, "")
    cur_year = datetime.now(TZ).year

    st.markdown(
        f"""
        <div class="side-label">OKUMA DURUMUM</div>
        <div class="side-card"><span>📚 Toplam Kitap</span><b>{len(home_df)}</b></div>
        <div class="side-card"><span>🔥 Bu Ay ({cur_month_name})</span><b>{counts['month']}</b></div>
        <div class="side-card"><span>⭐ Bu Yıl ({cur_year})</span><b>{counts['year']}</b></div>
        <div class="side-ver">Atlas {APP_VERSION}</div>
        """,
        unsafe_allow_html=True,
    )

    try:
        import cloud_db
        cs = cloud_db.status()
        if cs:
            lvl, txt = cs
            (st.caption if lvl != "warn" else st.warning)(txt)
    except Exception:
        pass

    if app_password and st.button("🔒 Kilitle", key="lock_app_sidebar", use_container_width=True):
        st.session_state.app_unlocked = False
        st.session_state.admin_logged_in = False
        st.rerun()

# 7. Aktif Sayfayı Çalıştır
nav.run()
