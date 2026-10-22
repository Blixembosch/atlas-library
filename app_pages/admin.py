"""Atlas Library - 6. Yönetici Paneli."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
import pandas as pd
import streamlit as st

from core.config import (
    CATEGORIES,
    DEFAULT_REC_LANGS,
    TZ,
    get_secret,
    safe_compare,
)
from core.db import (
    get_db_path,
    summarize_db,
    inspect_backup,
    restore_db,
    set_setting,
    sync_read_counts,
)
from services.book_service import (
    get_books_df,
    add_book,
    add_school_book,
    update_book,
    update_cover,
    delete_book,
    batch_update_outgrown,
    batch_update_categories,
)
from services.reading_service import (
    get_all_logs,
    approved_logs,
    atlas_logs,
    is_pending,
    daily_goal,
    approve_reading,
    approve_all_pending,
    reject_reading,
    undo_last_read,
    reset_all_counters,
    period_counts,
)
from services.recommendation_service import (
    rec_languages,
    evening_no_dutch,
    priority_keys,
    priority_custom,
    priority_per_day,
    series_options,
    series_mask,
)
from services.classifier_service import (
    load_category_reviews,
    auto_category_scan,
)
from services.isbn_service import fetch_book_by_isbn
from ui.styles import get_admin_css
from ui.components import show_table


def render_admin_page() -> None:
    st.markdown(get_admin_css(), unsafe_allow_html=True)
    st.markdown(
        '<div class="admin-head"><h2>Yönetim Paneli</h2>'
        '<p>Katalog, kapak, onaylar ve sistem yönetimi</p></div>',
        unsafe_allow_html=True,
    )

    if "admin_logged_in" not in st.session_state:
        st.session_state.admin_logged_in = False

    if not st.session_state.admin_logged_in:
        expected_pin = get_secret("ADMIN_PIN")
        if not expected_pin:
            st.error(
                "Yönetici PIN'i tanımlı değil. Streamlit Cloud > Settings > Secrets içine "
                '`ADMIN_PIN = "seçtiğin-pin"` satırını ekleyin (yerelde .streamlit/secrets.toml).'
            )
            return

        with st.form("admin_login_form"):
            entered_pin = st.text_input("Yönetici Giriş PIN Kodu", type="password", key="admin_pin_input")
            go_admin = st.form_submit_button("Giriş")

        if go_admin:
            if safe_compare(entered_pin, expected_pin):
                st.session_state.admin_logged_in = True
                st.rerun()
            else:
                st.error("PIN kodu hatalı!")
        return

    # Oturum Başlığı ve Çıkış
    try:
        import cloud_db
        sync_on, sync_txt = cloud_db.describe()
    except Exception:
        sync_on, sync_txt = False, "Yerel SQLite modu"

    hdr_l, hdr_r = st.columns([6, 1])
    hdr_l.markdown(
        '🔐 **Yönetici oturumu açık** &nbsp; '
        + ('<span class="adm-pill ok">☁️ ' + sync_txt + '</span>' if sync_on else f'<span class="adm-pill">📁 {sync_txt}</span>'),
        unsafe_allow_html=True,
    )
    with hdr_r:
        if st.button("Çıkış Yap", key="admin_logout", use_container_width=True):
            st.session_state.admin_logged_in = False
            st.rerun()

    # Genel Metrikler
    books_df = get_books_df()
    home_df = books_df[books_df["is_school"] == 0]
    eligible_df = home_df[home_df["is_outgrown"] == 0]
    all_logs = get_all_logs()
    pending_logs = [l for l in all_logs if is_pending(l)]
    logs_data = approved_logs(all_logs)
    counts = period_counts(logs_data)
    own_counts = period_counts(atlas_logs(all_logs))
    missing_n = int((books_df["cover_url"].isna() | (books_df["cover_url"] == "")).sum())

    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("Toplam Kitap", len(home_df))
    k2.metric("Okuma Kaydı", len(logs_data))
    k3.metric("Bu Ay", counts["month"])
    k4.metric("Onay Bekleyen", len(pending_logs))
    k5.metric("Kapağı Eksik", missing_n)
    k6.metric("Atlas'ın Okuduğu", own_counts["total"])

    st.markdown("---")

    # 5 Gruplu Sekme Yapısı
    g_onay, g_kitap, g_kapak, g_duzen, g_sistem = st.tabs([
        f"⏳ Onaylar ({len(pending_logs)})",
        "📚 Kitaplar",
        f"🎨 Kapaklar{f' ({missing_n})' if missing_n else ''}",
        "🧭 Öneri & Düzen",
        "⚙️ Sistem",
    ])

    # 1. SEKME: ONAYLAR
    with g_onay:
        adm_tab_pending, adm_tab_undo = st.tabs(["Bekleyenler", "↩ Son okumayı geri al"])

        with adm_tab_pending:
            st.subheader("⏳ Onay Bekleyen Okumalar")
            if not pending_logs:
                st.success("Bekleyen okuma yok 🎉")
            else:
                st.caption(
                    "Her okuma için **Atlas okudu** kutusunu işaretleyebilirsiniz. "
                    "İşaretlemezseniz ebeveyn okudu sayılır; ikisi de toplam XP'ye eklenir."
                )
                if st.button("✅ Hepsini Onayla", key="approve_all_btn"):
                    flags = {
                        pl["id"]: bool(st.session_state.get(f"atlas_chk_{pl['id']}", False))
                        for pl in pending_logs
                    }
                    n_app = approve_all_pending(flags)
                    st.toast(f"{n_app} okuma onaylandı.", icon="✅")
                    st.rerun()

                pend_titles = dict(zip(books_df["id"], books_df["title"]))
                for pl in sorted(pending_logs, key=lambda x: x.get("read_at") or ""):
                    pc1, pc_a, pc2, pc3 = st.columns([4, 1.7, 1.2, 1.2])
                    pc1.write(
                        f"📖 **{pend_titles.get(pl['book_id'], '(silinmiş kitap)')}** — "
                        f"{(pl.get('read_at') or '')[:16].replace('T', ' ')}"
                    )
                    atlas_flag = pc_a.checkbox("👦 Atlas okudu", key=f"atlas_chk_{pl['id']}")
                    if pc2.button("✅ Onayla", key=f"approve_{pl['id']}"):
                        approve_reading(pl["id"], by_atlas=atlas_flag)
                        st.rerun()
                    if pc3.button("✖ Reddet", key=f"reject_{pl['id']}"):
                        reject_reading(pl["id"])
                        st.rerun()

        with adm_tab_undo:
            st.subheader("↩ En Son Okumayı Geri Al")
            read_books_adm = books_df[books_df["read_count"] > 0]
            for _, rb in read_books_adm.iterrows():
                col_rb1, col_rb2 = st.columns([3, 1])
                col_rb1.write(f"📖 **{rb['title']}** (Okunma: {int(rb['read_count'])})")
                if col_rb2.button("Geri Al", key=f"undo_{rb['id']}"):
                    undo_last_read(rb["id"])
                    st.toast("Okuma geri alındı.", icon="↩")
                    st.rerun()

    # 2. SEKME: KİTAPLAR
    with g_kitap:
        adm_tab_new, adm_tab_school, adm_tab_edit, adm_tab_del = st.tabs(
            ["➕ Yeni kitap", "🏫 Okul kitabı", "✏️ Düzenle", "🗑️ Sil"]
        )

        with adm_tab_new:
            with st.form("admin_add_form"):
                st.subheader("Yeni Kitap Ekle")
                new_t = st.text_input("Kitap Adı")
                new_a = st.text_input("Yazar")
                new_p = st.text_input("Yayınevi")
                new_isbn = st.text_input("ISBN Numarası")
                new_c = st.selectbox("Kategori", CATEGORIES)
                new_ag = st.text_input("Yaş Grubu", "5+")
                new_pg = st.number_input("Sayfa Sayısı", min_value=1, value=None, step=1, placeholder="Boş bırakılabilir")
                new_lang = st.text_input("Kitap Dili", "Türkçe")
                new_cv = st.text_input("Kapak Görsel URL")

                if st.form_submit_button("Kütüphaneye Kaydet"):
                    if new_t.strip():
                        add_book(
                            title=new_t,
                            author=new_a,
                            publisher=new_p,
                            isbn=new_isbn,
                            category=new_c,
                            age=new_ag,
                            pages=int(new_pg) if new_pg else None,
                            language=new_lang,
                            cover_url=new_cv,
                        )
                        st.success(f"'{new_t}' başarıyla eklendi!")
                        st.rerun()
                    else:
                        st.error("Kitap adı zorunludur.")

        with adm_tab_school:
            st.subheader("🏫 De Vuurvlinder Okul Kitabı Ekle")
            st.caption("Okul kitapları kütüphanede listelenmez. Eklediğin an Dutch olarak okunmuş sayılır.")
            with st.form("admin_school_form"):
                sch_isbn = st.text_input("ISBN Numarası (Otomatik bulma için)", placeholder="Örn: 97890258... (İsteğe bağlı)")
                quick_title = st.text_input("Kitap Adı (ISBN boşsa zorunlu)", placeholder="Örn: Nijntje op school")
                quick_pages = st.number_input("Sayfa Sayısı", min_value=1, value=None, step=1, placeholder="Boş bırakılabilir")
                sch_date = st.date_input("Okunduğu Tarih", value=datetime.now(TZ).date())
                sch_time = st.time_input("Okunduğu Saat", value=datetime.now(TZ).time())
                sch_atlas = st.checkbox("👦 Atlas kendisi okudu", key="sch_atlas")

                if st.form_submit_button("Okul Kitabını Ekle"):
                    f_title = quick_title.strip()
                    f_author = "De Vuurvlinder Okulu"
                    f_pub = "De Vuurvlinder"
                    f_pages = quick_pages
                    f_cover = ""
                    f_isbn = sch_isbn.strip()

                    if f_isbn:
                        with st.spinner("ISBN ile kitap bilgileri aranıyor... 🔍"):
                            data = fetch_book_by_isbn(f_isbn)
                            if data:
                                f_title = data["title"] or f_title
                                f_author = data["author"]
                                f_pub = data["publisher"]
                                f_pages = data["pages"]
                                f_cover = data["cover_url"]
                                st.success("Kitap bilgileri bulundu! ✨")

                    if f_title:
                        read_dt = datetime.combine(sch_date, sch_time)
                        add_school_book(
                            title=f_title,
                            author=f_author,
                            publisher=f_pub,
                            isbn=f_isbn,
                            pages=int(f_pages) if f_pages else None,
                            cover_url=f_cover,
                            read_dt=read_dt,
                            by_atlas=sch_atlas,
                        )
                        st.toast(f"'{f_title}' kaydedildi! 🎒", icon="✅")
                        st.rerun()
                    else:
                        st.error("Lütfen en azından kitap adını girin.")

        with adm_tab_edit:
            st.subheader("✏️ Kitap Künyesini Düzenle")
            edit_search_q = st.text_input("🔍 Düzenlenecek Kitabı Ara", placeholder="Kitap adı...", key="edit_book_search")
            matched_edit = (
                books_df[books_df["title"].astype(str).str.contains(edit_search_q.strip(), case=False, na=False)]
                if edit_search_q.strip()
                else pd.DataFrame()
            )

            for _, eb in matched_edit.iterrows():
                with st.form(f"edit_form_{eb['id']}"):
                    up_t = st.text_input("Kitap Adı", value=eb["title"])
                    up_a = st.text_input("Yazar", value=str(eb.get("author", "")))
                    up_p = st.text_input("Yayınevi", value=str(eb.get("publisher", "")))
                    up_pg = st.number_input(
                        "Sayfa Sayısı", min_value=1, step=1,
                        value=int(eb["pages"]) if pd.notna(eb.get("pages")) else None,
                        placeholder="Bilinmiyor",
                    )
                    up_lang = st.text_input("Dil", value=str(eb.get("language", "Türkçe")))
                    cur_cat = eb.get("category")
                    cat_choices = CATEGORIES if cur_cat in CATEGORIES else [cur_cat] + CATEGORIES
                    up_cat = st.selectbox("Kategori", cat_choices, index=cat_choices.index(cur_cat) if cur_cat in cat_choices else 0)
                    up_out = st.checkbox("🎒 Yaşı geçti (öneri listelerine girmez)", value=bool(int(eb.get("is_outgrown", 0))))

                    if st.form_submit_button("Güncelle"):
                        update_book(
                            eb["id"],
                            title=up_t,
                            author=up_a,
                            publisher=up_p,
                            pages=int(up_pg) if up_pg else None,
                            language=up_lang,
                            category=up_cat,
                            is_outgrown=int(up_out),
                        )
                        st.success("Kitap güncellendi!")
                        st.rerun()

        with adm_tab_del:
            st.subheader("🗑️ Kitap Sil")
            del_q = st.text_input("🔍 Silinecek Kitabı Ara", placeholder="Kitap adı...", key="del_book_search")
            matched_del = (
                books_df[books_df["title"].astype(str).str.contains(del_q.strip(), case=False, na=False)]
                if del_q.strip()
                else pd.DataFrame()
            )

            for _, db_item in matched_del.iterrows():
                with st.form(f"del_form_{db_item['id']}"):
                    st.error(f"📖 **{db_item['title']}** — *{db_item.get('author', 'Bilinmiyor')}*")
                    confirm_del = st.checkbox("Bu kitabı ve tüm okuma geçmişini kalıcı olarak silmeyi onaylıyorum.", key=f"chk_del_{db_item['id']}")
                    if st.form_submit_button("Kitabı Kalıcı Olarak Sil"):
                        if confirm_del:
                            delete_book(db_item["id"])
                            st.toast(f"'{db_item['title']}' silindi.", icon="🗑️")
                            st.rerun()
                        else:
                            st.warning("Lütfen silme onay kutucuğunu işaretleyin.")

    # 3. SEKME: KAPAKLAR
    with g_kapak:
        adm_tab_cov_edit, adm_tab_cov_miss = st.tabs(["Kapak düzenle", f"Eksik görseller ({missing_n})"])

        with adm_tab_cov_edit:
            st.subheader("🎨 Kapak Düzenle")
            cov_q = st.text_input("🔍 Kitap Ara", key="cov_search_input")
            cov_matches = (
                books_df[books_df["title"].astype(str).str.contains(cov_q.strip(), case=False, na=False)]
                if cov_q.strip()
                else books_df[books_df["cover_url"].isna() | (books_df["cover_url"] == "")]
            )

            for _, b in cov_matches.iterrows():
                with st.form(f"cov_form_{b['id']}"):
                    st.write(f"📖 {b['title']}")
                    new_cov = st.text_input("Kapak URL", value=str(b.get("cover_url", "")), key=f"url_{b['id']}")
                    if st.form_submit_button("Kaydet"):
                        update_cover(b["id"], new_cov)
                        st.toast("Kapak kaydedildi.", icon="🎨")
                        st.rerun()

        with adm_tab_cov_miss:
            st.subheader(f"🖼 Görseli Eksik Olan Kitaplar ({missing_n})")
            missing_df = books_df[books_df["cover_url"].isna() | (books_df["cover_url"] == "")]
            if len(missing_df) > 0:
                for _, mb in missing_df.iterrows():
                    with st.form(f"miss_cov_{mb['id']}"):
                        st.write(f"📖 **{mb['title']}** — *{mb.get('author', 'Bilinmiyor')}*")
                        new_u = st.text_input("Kapak URL", key=f"miss_u_{mb['id']}")
                        if st.form_submit_button("Kapak Ekle"):
                            update_cover(mb["id"], new_u)
                            st.toast("Kapak eklendi.", icon="🖼️")
                            st.rerun()
            else:
                st.success("Tebrikler! Kütüphanenizde görseli eksik olan kitap kalmamış! 🎉")

    # 4. SEKME: ÖNERİ VE DÜZEN
    with g_duzen:
        adm_settings, adm_catrev, adm_lang, adm_outgrown = st.tabs(
            ["🎛️ Ayarlar", "🔎 Kategori incelemesi", "🌐 Dil & Tür", "🎒 Yaşı geçti"]
        )

        with adm_settings:
            st.markdown("##### 🎯 Günlük hedef")
            goal_input = st.number_input("Günde kaç kitap?", min_value=1, max_value=10, value=daily_goal(), step=1)
            if st.button("Hedefi Kaydet", key="save_goal_btn"):
                set_setting("daily_goal", int(goal_input))
                st.toast(f"Günlük hedef {int(goal_input)} kitap yapıldı.", icon="🎯")
                st.rerun()

            st.markdown("---")
            st.markdown("##### 🎛️ Öneri ayarları")
            lang_opts = sorted({str(x) for x in books_df["language"].fillna("Türkçe") if str(x).strip()} | set(DEFAULT_REC_LANGS))
            sel_langs = st.multiselect("Hangi dillerdeki kitaplar önerilsin?", options=lang_opts, default=[x for x in rec_languages() if x in lang_opts])
            sel_evening = st.checkbox("Akşam (19:00 sonrası) Dutch kitaplar önerilmesin", value=evening_no_dutch())

            st.markdown("**Bir tur bitene kadar önce önerilecek seriler**")
            _opts = series_options(books_df)
            _cur = [k for k in priority_keys() if k in _opts]
            sel_series = st.multiselect(
                "Seriler", options=list(_opts.keys()), default=_cur,
                format_func=lambda k: f"{_opts[k][0]} · {_opts[k][1]} kitap",
            )
            ns1, ns2 = st.columns([3, 1])
            new_series = ns1.text_input("Yeni seri ekle (kitap adı şununla başlasın):", placeholder="Örn: Cin Ali")
            _ns = str(new_series or "").strip()
            if _ns:
                _n_match = int(series_mask(home_df, f"title:{_ns}").sum())
                ns1.caption(f"{_n_match} kitap eşleşiyor.")
            with ns2:
                if st.button("➕ Seriyi ekle", key="add_series_btn"):
                    if _ns:
                        _k = f"title:{_ns}"
                        if int(series_mask(home_df, _k).sum()) == 0:
                            st.error("Bu başlıkla başlayan kitap bulunamadı.")
                        else:
                            _cust = priority_custom()
                            if _k not in _cust:
                                set_setting("priority_custom", json.dumps(_cust + [_k], ensure_ascii=False))
                            set_setting("priority_series", json.dumps(list(dict.fromkeys(priority_keys() + [_k])), ensure_ascii=False))
                            st.toast("Seri eklendi.", icon="➕")
                            st.rerun()

            sel_quota = st.number_input("Tur bitene kadar günde en fazla kaç kitap bu serilerden önerilsin?", min_value=0, max_value=5, value=priority_per_day(), step=1)
            if st.button("Ayarları Kaydet", key="save_rec_settings_btn"):
                set_setting("priority_per_day", int(sel_quota))
                set_setting("rec_languages", ",".join(sel_langs) if sel_langs else ",".join(DEFAULT_REC_LANGS))
                set_setting("evening_no_dutch", "1" if sel_evening else "0")
                set_setting("priority_series", json.dumps(list(sel_series), ensure_ascii=False))
                st.toast("Ayarlar kaydedildi.", icon="🎛️")
                st.rerun()

        with adm_catrev:
            st.subheader("🔎 Kategori İncelemesi ve Otomatik Tarama")
            cur_cats = dict(zip(books_df["id"], books_df["category"]))
            title_of = dict(zip(books_df["id"], books_df["title"]))
            rev_map = load_category_reviews()

            diff_rows = [
                {"ID": k, "Kitap": title_of.get(k, "?"), "Şimdi": cur_cats.get(k), "Önerilen": v[0], "Gerekçe": v[1], "Güven": v[2]}
                for k, v in rev_map.items()
                if k in cur_cats and cur_cats[k] != v[0]
            ]

            if diff_rows:
                diff_df = pd.DataFrame(diff_rows)
                st.write(f"**{len(diff_df)}** kitapta değişiklik önerisi var.")
                show_table(diff_df, hide_index=True)
                if st.button("✅ İnceleme Önerilerini Uygula", key="apply_rev_btn"):
                    batch_update_categories([(r["ID"], r["Önerilen"]) for _, r in diff_df.iterrows()])
                    st.success("Kategoriler güncellendi!")
                    st.rerun()
            else:
                st.success("Tüm kitaplar inceleme önerileriyle uyumlu.")

            st.markdown("---")
            st.markdown("##### 🤖 Ücretsiz Otomatik Tarama")
            if st.button("🔍 Otomatik Tara", key="run_scan_btn"):
                st.session_state["catscan_rows"] = auto_category_scan(books_df)

            _scan = st.session_state.get("catscan_rows")
            if _scan:
                sdf = pd.DataFrame(_scan)
                sdf.insert(0, "Uygula", sdf["Güven"] == "yüksek")
                edited = st.data_editor(sdf, hide_index=True, key="scan_editor")
                chosen = edited[edited["Uygula"]]
                if st.button(f"İşaretli {len(chosen)} öneriyi uygula", key="apply_scan_btn", disabled=len(chosen) == 0):
                    batch_update_categories([(r["ID"], r["Önerilen"]) for _, r in chosen.iterrows()])
                    st.session_state["catscan_rows"] = None
                    st.success("Kategoriler güncellendi!")
                    st.rerun()

        with adm_lang:
            st.subheader("🌐 Dil ve Tür Dağılımı")
            lt = home_df.copy()
            lt["language"] = lt["language"].fillna("Türkçe")
            recl = set(rec_languages())
            lt["Önerilir mi"] = lt.apply(
                lambda r: "Hayır (yaşı geçti)" if int(r["is_outgrown"]) == 1
                else ("Hayır (dil kapalı)" if r["language"] not in recl else "Evet"),
                axis=1,
            )
            pivot = pd.crosstab(lt["language"], lt["category"], margins=True, margins_name="Toplam")
            show_table(pivot)

        with adm_outgrown:
            st.subheader("🎒 Yaşı Geçen Kitaplar")
            og_n = int((home_df["is_outgrown"] == 1).sum())
            st.info(f"Şu an yaşı geçen: **{og_n}** kitap · Öneri havuzunda: **{len(eligible_df)}** kitap")

            og_table = pd.DataFrame({
                "ID": home_df["id"].values,
                "Kitap": home_df["title"].values,
                "Yaş": home_df["age"].astype(str).values,
                "Kategori": home_df["category"].values,
                "🎒 Yaşı geçti": home_df["is_outgrown"].astype(bool).values,
            })
            edited_og = st.data_editor(
                og_table,
                hide_index=True,
                disabled=["ID", "Kitap", "Yaş", "Kategori"],
                key="og_editor_table",
            )
            changed_og = edited_og[edited_og["🎒 Yaşı geçti"] != og_table["🎒 Yaşı geçti"]]
            if len(changed_og) > 0:
                st.warning(f"{len(changed_og)} kitapta değişiklik yapıldı.")
            if st.button("💾 Yaşı Geçti Değişikliklerini Kaydet", disabled=len(changed_og) == 0):
                batch_update_outgrown([(int(r["🎒 Yaşı geçti"]), r["ID"]) for _, r in changed_og.iterrows()])
                st.success("Kaydedildi!")
                st.rerun()

    # 5. SEKME: SİSTEM
    with g_sistem:
        adm_summary, adm_logs, adm_backup, adm_reset = st.tabs(
            ["📊 Özet", "📝 Loglar", "💾 Yedek & Geri yükle", "🧹 Sıfırla"]
        )

        with adm_summary:
            st.subheader("📊 Okuma Geçmişi Özeti")
            if logs_data:
                summary_map: dict = {}
                for l in logs_data:
                    bid = l.get("book_id")
                    rat = l.get("read_at", "")
                    if bid not in summary_map:
                        summary_map[bid] = {"count": 0, "last_read": ""}
                    summary_map[bid]["count"] += 1
                    if rat > summary_map[bid]["last_read"]:
                        summary_map[bid]["last_read"] = rat

                b_map = {b["id"]: b for b in books_df.to_dict("records")}
                s_data = [
                    {
                        "Kitap Adı": b_map.get(k, {}).get("title", ""),
                        "Yazar": b_map.get(k, {}).get("author", ""),
                        "Toplam Okunma": v["count"],
                        "En Son Okunma": v["last_read"][:19].replace("T", " "),
                    }
                    for k, v in summary_map.items()
                ]
                show_table(pd.DataFrame(s_data))

            st.markdown("---")
            st.markdown("##### 🔄 Okuma Sayaçlarını Doğrula & Senkronize Et")
            st.caption(
                "`reading_log` tablosundaki onaylı kayıtları sayarak `books.read_count` sütununu "
                "birebir eşitler. Sayım uyuşmazlığı şüphesi olduğunda güvenle çalıştırabilirsiniz."
            )
            if st.button("Sayaçları Doğrula ve Eşitle", key="sync_counts_btn"):
                n_up = sync_read_counts()
                st.success(f"{n_up} kitabın sayacı okuma loglarıyla başarıyla eşitlendi.")
                st.rerun()

        with adm_logs:
            st.subheader("📝 Ham Okuma Logları")
            show_table(pd.DataFrame(all_logs))

        with adm_backup:
            st.subheader("💾 Veritabanı Yedek İndir")
            db_file = get_db_path()
            if db_file.exists():
                with open(db_file, "rb") as f:
                    st.download_button(
                        label="📥 atlas_library.db İndir",
                        data=f,
                        file_name="atlas_library.db",
                        mime="application/x-sqlite3",
                    )

            st.markdown("---")
            st.subheader("♻️ Veritabanını Geri Yükle")
            restore_file = st.file_uploader("Yedek dosyası seçin (.db, .sqlite)", type=["db", "sqlite", "sqlite3"])
            if restore_file:
                raw_bytes = restore_file.getvalue()
                info, err = inspect_backup(raw_bytes)
                if err:
                    st.error(err)
                else:
                    cur_info = summarize_db(db_file) or {"books": 0, "logs": 0}
                    c_b1, c_b2 = st.columns(2)
                    c_b1.metric("Şu anki veritabanı", f"{cur_info['books']} kitap / {cur_info['logs']} okuma")
                    c_b2.metric("Yüklenen yedek", f"{info['books']} kitap / {info['logs']} okuma")
                    confirm_res = st.checkbox("Mevcut verinin bu yedekle değiştirilmesini onaylıyorum.")
                    if st.button("♻️ Geri Yükle", disabled=not confirm_res):
                        restore_db(raw_bytes)
                        st.toast("Veritabanı geri yüklendi.", icon="✅")
                        st.rerun()

        with adm_reset:
            st.subheader("🧹 Tüm Sayaçları Sıfırla")
            st.warning("Bu işlem tüm okuma kayıtlarını kalıcı olarak siler ve kitap sayaçlarını 0 yapar!")
            confirm_reset = st.checkbox("Evet, tüm okuma kayıtlarını sıfırlamak istiyorum.")
            if st.button("Sayaçları Sıfırla", disabled=not confirm_reset):
                reset_all_counters()
                st.success("Tüm sayaçlar sıfırlandı.")
                st.rerun()

render_page = render_admin_page


if __name__ == "__main__":
    render_page()
