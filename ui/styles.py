"""Atlas Library - Merkezi CSS ve Tema Stilleri."""

from __future__ import annotations


def get_app_css() -> str:
    """Ana uygulama için modern, çocuk dostu ve responsive CSS stilleri."""
    return """
<style>
:root {
  --primary: #4F7CFF;
  --secondary: #7C4DFF;
  --r-card: 24px;
  --r-btn: 14px;
  --shadow: 0 4px 20px rgba(0, 0, 0, .06);
}

header[data-testid="stHeader"] {
  background: transparent !important;
  height: 0 !important;
}

.block-container {
  padding: .8rem 1.2rem 1.5rem !important;
  max-width: 1400px;
}

.stApp {
  background: #F8FAFC !important;
  color: #1e293b;
}

/* Genel Butonlar */
div.stButton > button {
  border-radius: var(--r-btn);
  font-weight: 700;
  color: #fff !important;
  border: none;
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  box-shadow: 0 4px 14px rgba(79, 124, 255, .25);
  padding: .55rem .8rem;
  transition: all .2s ease-in-out;
}

div.stButton > button:hover {
  transform: translateY(-2px);
  filter: brightness(1.07);
}

/* Sol Kenar Çubuğu (Sidebar) */
section[data-testid="stSidebar"] {
  background: #fff !important;
  border-right: 1px solid #e2e8f0;
}

.side-logo {
  text-align: center;
  padding: 10px 0 4px;
}

.side-logo-emoji {
  font-size: 2.2rem;
  line-height: 1.1;
}

.side-logo-title {
  font-weight: 800;
  font-size: .95rem;
  color: #1e293b;
}

.side-logo-sub {
  font-size: .7rem;
  color: #64748b;
}

.side-label {
  font-size: .68rem;
  letter-spacing: .12em;
  color: #94a3b8;
  font-weight: 800;
  margin: 16px 0 6px;
}

.side-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #F8FAFC;
  border-radius: var(--r-btn);
  padding: 9px 14px;
  margin-bottom: 6px;
  font-size: .85rem;
  font-weight: 700;
  color: #475569;
}

.side-card b {
  font-size: 1.1rem;
  color: #1e293b;
}

.side-ver {
  text-align: center;
  font-size: .65rem;
  color: #94a3b8;
  margin-top: 8px;
}

/* Hero Bölümü (Modern Ergonomik Kart) */
.st-key-hero_box, .hero-box {
  background: linear-gradient(135deg, #4361EE 0%, #7209B7 60%, #3A0CA3 100%);
  border-radius: 20px;
  padding: 14px 18px 12px;
  box-shadow: 0 8px 24px rgba(67, 97, 238, 0.25);
  margin-bottom: 14px;
  color: #fff;
}

/* Hero Aksiyon Butonları */
.st-key-hero_box div.stButton > button {
  background: #ffffff !important;
  color: #3A0CA3 !important;
  border: 1px solid rgba(255, 255, 255, 0.9) !important;
  border-radius: 12px !important;
  font-weight: 800 !important;
  font-size: 0.86rem !important;
  padding: 7px 10px !important;
  box-shadow: 0 3px 10px rgba(0, 0, 0, 0.1) !important;
  transition: all 0.2s ease !important;
  width: 100% !important;
}

.st-key-hero_box div.stButton > button:hover {
  background: #f8fafc !important;
  color: #4361EE !important;
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.15) !important;
}

/* Sol Alan: Karşılama ve Görev */
.hero-heading {
  font-size: 1.45rem;
  font-weight: 900;
  color: #ffffff;
  margin: 0 0 2px 0;
  line-height: 1.15;
}

.hero-subheading {
  font-size: 0.84rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.92);
  margin: 0 0 7px 0;
  line-height: 1.3;
}

.hero-mission-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  background: rgba(255, 255, 255, 0.14);
  border-radius: 14px;
  padding: 4px 10px;
  margin-bottom: 8px;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.mission-title {
  font-size: 0.78rem;
  font-weight: 800;
  color: #fff;
}

.mission-slots {
  display: flex;
  gap: 4px;
  align-items: center;
}

.goal-slot {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  border: 2px dashed rgba(255, 255, 255, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.78rem;
}

.goal-slot.done {
  background: #ffffff;
  border: 2px solid #ffffff;
}

.goal-slot.wait {
  background: rgba(255, 255, 255, 0.35);
  border: 2px solid rgba(255, 255, 255, 0.9);
}

.mission-count {
  font-size: 0.82rem;
  color: #fff;
}

.mission-count b {
  font-size: 0.95rem;
}

.goal-streak {
  display: inline-block;
  background: #ffffff;
  color: #ea580c;
  border-radius: 99px;
  padding: 1px 9px;
  font-weight: 800;
  font-size: 0.75rem;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}

/* Sağ Alan: Glassmorphic Başarı & Oyunlaştırma Kartı */
.hero-achievement-card {
  background: rgba(255, 255, 255, 0.16);
  border: 1px solid rgba(255, 255, 255, 0.28);
  border-radius: 18px;
  padding: 10px 14px;
  color: #ffffff;
  backdrop-filter: blur(8px);
}

.achieve-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.achieve-level {
  font-size: 1.15rem;
  font-weight: 900;
  color: #ffffff;
}

.achieve-xp-badge {
  background: rgba(255, 255, 255, 0.25);
  border-radius: 99px;
  padding: 1px 9px;
  font-size: 0.72rem;
  font-weight: 800;
  color: #ffffff;
}

.achieve-title {
  font-size: 0.76rem;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.85);
  margin-bottom: 4px;
}

.hero-xp-track {
  height: 8px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 99px;
  overflow: hidden;
  margin: 5px 0 3px;
}

.hero-xp-fill {
  background: linear-gradient(90deg, #FFD166, #FFFFFF);
  height: 100%;
  border-radius: 99px;
  transition: width 0.3s ease;
}

.achieve-xp-info {
  display: flex;
  justify-content: space-between;
  font-size: 0.72rem;
  color: rgba(255, 255, 255, 0.88);
  margin-bottom: 8px;
}

.achieve-stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-top: 4px;
}

.achieve-stat-box {
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  padding: 5px 8px;
  display: flex;
  align-items: center;
  gap: 7px;
}

.stat-emoji {
  font-size: 1.15rem;
}

.stat-num {
  font-size: 0.95rem;
  font-weight: 900;
  line-height: 1.1;
  color: #ffffff;
}

.stat-label {
  font-size: 0.65rem;
  color: rgba(255, 255, 255, 0.82);
  font-weight: 600;
}

/* XP İlerleme Çubuğu (Genel) */
.xp-track {
  background: #e2e8f0;
  border-radius: 99px;
  height: 12px;
  overflow: hidden;
  margin: 6px 0 4px;
}

.xp-fill {
  background: linear-gradient(90deg, #4F7CFF, #7C4DFF);
  height: 100%;
  border-radius: 99px;
}

.xp-text {
  font-size: .8rem;
  font-weight: 600;
}

/* Category cards */
div[class*="st-key-cat_"] button, div[class*="st-key-catON_"] button {
  background: #fff;
  color: #1e293b !important;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  box-shadow: var(--shadow);
  min-height: 64px;
  padding: 6px 8px !important;
  white-space: normal;
}

div[class*="st-key-cat_"] button p, div[class*="st-key-catON_"] button p {
  margin: 0;
  line-height: 1.2;
  font-size: 0.82rem;
}

div[class*="st-key-catON_"] button {
  border: 2px solid #4F7CFF !important;
  background: #eff6ff !important;
}

/* Kitap Kartları */
.book-card {
  background: #fff;
  border-radius: var(--r-card);
  padding: 12px;
  box-shadow: var(--shadow);
  border: 1px solid #eef2f7;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  overflow: hidden;
  position: relative;
  margin-bottom: 8px;
  transition: transform .2s ease;
}

.book-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, .09);
}

.book-cover {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #F1F5F9;
  border-radius: 18px;
  overflow: hidden;
}

.book-cover img {
  height: 100%;
  max-width: 100%;
  object-fit: contain;
}

.book-badge {
  position: absolute;
  top: 18px;
  left: 18px;
  background: #fff;
  border-radius: 99px;
  padding: 3px 10px;
  font-size: .72rem;
  font-weight: 800;
  color: #7C4DFF;
  box-shadow: 0 2px 8px rgba(0, 0, 0, .12);
  z-index: 2;
}

.school-badge {
  position: absolute;
  top: 18px;
  right: 18px;
  background: #FEF3C7;
  border-radius: 99px;
  padding: 3px 10px;
  font-size: .7rem;
  font-weight: 800;
  color: #D97706;
  box-shadow: 0 2px 8px rgba(0, 0, 0, .08);
  z-index: 2;
}

.book-title {
  font-weight: 800;
  font-size: .98rem;
  line-height: 1.25;
  margin: 10px 0 6px;
  height: 2.5em;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.book-meta {
  font-size: .8rem;
  color: #64748b;
  line-height: 1.6;
}

/* Kitap Altı 'Hemen Oku' Butonunu Ortalama */
div[data-testid="stColumn"] div.stButton {
  display: flex !important;
  justify-content: center !important;
  align-items: center !important;
  width: 100% !important;
  margin-top: 4px !important;
}

div[data-testid="stColumn"] div.stButton > button {
  display: inline-flex !important;
  justify-content: center !important;
  align-items: center !important;
  text-align: center !important;
  margin: 0 auto !important;
  border-radius: 99px !important;
  font-weight: 700 !important;
  padding: 8px 18px !important;
  width: 100% !important;
  max-width: 200px !important;
  box-shadow: 0 2px 8px rgba(79, 124, 255, 0.15) !important;
  transition: transform 0.15s ease, box-shadow 0.15s ease !important;
}

div[data-testid="stColumn"] div.stButton > button:hover {
  transform: translateY(-2px) !important;
  box-shadow: 0 4px 14px rgba(79, 124, 255, 0.25) !important;
}

/* Son Okunanlar */
.recent-item {
  background: #fff;
  border-radius: 18px;
  padding: 12px 18px;
  margin-bottom: 8px;
  box-shadow: var(--shadow);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.recent-item span {
  color: #94a3b8;
  font-size: .8rem;
}

/* Okuma Yolculuğu Durakları */
.journey {
  display: flex;
  gap: 10px;
  overflow-x: auto;
  padding: 6px 2px 14px;
}

.stop {
  flex: 1;
  min-width: 112px;
  border-radius: 20px;
  padding: 14px 8px;
  text-align: center;
  font-weight: 800;
  border: 2px solid;
  background: #fff;
}

.stop-icon {
  font-size: 2rem;
}

.stop small {
  display: block;
  font-weight: 600;
  font-size: .7rem;
  margin-top: 4px;
}

.stop.done {
  background: #ECFDF5;
  border-color: #22C55E;
  color: #15803D;
}

.stop.now {
  background: #EEF3FF;
  border-color: #4F7CFF;
  color: #4F7CFF;
  box-shadow: 0 0 0 4px rgba(79, 124, 255, .15);
}

.stop.lock {
  background: #F1F5F9;
  border-color: #E2E8F0;
  color: #94A3B8;
}

/* İstatistik ve Dil Kartları */
.stat-card {
  background: #fff;
  border-radius: var(--r-card);
  padding: 18px;
  box-shadow: var(--shadow);
  margin-bottom: 14px;
}

.stat-card small {
  color: #64748b;
  font-weight: 800;
}

.stat-val {
  font-size: 2rem;
  font-weight: 900;
  color: #4F7CFF;
}

.lang-card {
  background: #fff;
  border-radius: var(--r-card);
  padding: 16px 18px;
  box-shadow: var(--shadow);
  margin-bottom: 14px;
}

.lang-title {
  font-weight: 800;
  font-size: 1.05rem;
  margin-bottom: 10px;
}

.lang-row {
  display: flex;
  gap: 10px;
}

.lang-row div {
  flex: 1;
  text-align: center;
  background: #F8FAFC;
  border-radius: 16px;
  padding: 10px 4px;
}

.lang-row b {
  display: block;
  font-size: 1.6rem;
  font-weight: 900;
  color: #4F7CFF;
}

.lang-row span {
  font-size: .75rem;
  color: #64748b;
  font-weight: 700;
}

/* Anı Defteri Kartları */
.memory-card {
  background: #fff;
  border-radius: var(--r-card);
  padding: 16px 20px;
  margin-bottom: 14px;
  box-shadow: var(--shadow);
  border-left: 5px solid #7C4DFF;
}

.memory-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.memory-quote {
  font-style: italic;
  background: #F5F3FF;
  border-radius: 12px;
  padding: 8px 14px;
  margin: 8px 0;
  color: #6D28D9;
  font-weight: 600;
  font-size: .9rem;
}
</style>
"""


def get_admin_css() -> str:
    """Yönetici paneli için özel stiller."""
    return """
<style>
.admin-head {
  border-bottom: 1px solid #e2e8f0;
  margin-bottom: 16px;
  padding-bottom: 8px;
}

.admin-head h2 {
  margin: 0;
  font-size: 1.4rem;
  color: #0F172A;
}

.admin-head p {
  margin: 0;
  color: #64748b;
  font-size: .85rem;
}

.adm-pill {
  display: inline-block;
  border-radius: 99px;
  padding: 2px 12px;
  font-size: .8rem;
  font-weight: 700;
}

.adm-pill.ok {
  background: #DCFCE7;
  color: #166534;
}

[data-baseweb="tab-list"] {
  gap: 4px;
  background: #EEF2F7;
  padding: 4px;
  border-radius: 14px;
}

[data-baseweb="tab"] {
  font-weight: 600;
  border-radius: 10px;
}
</style>
"""
