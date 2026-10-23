# 🗺️ Atlas Library - Sürüm Yol Haritası ve Değişiklik Günlüğü (Changelog & Roadmap)

Bu doküman, **Atlas'ın Sihirli Kütüphanesi** projesinin başlangıcından bugüne kadar olan tüm sürüm geçmişini, mimari evrimini ve gelecekte planlanan yenilikleri kronolojik olarak kayıt altında tutar.

---

## 📌 Sürüm Özeti

| Sürüm | Tarih | Odak Noktası | Durum |
| :--- | :--- | :--- | :--- |
| **v2.0.4** | 2026-10-23 | Hero Sol Panel Ultra-Kompakt Düzen & Dikey Alan Optimizasyonu | 🚀 Canlıda |
| **v2.0.3** | 2026-10-23 | Hero Sol Panel Dikey Kompaktlaştırma ve Yükseklik Eşitleme | ✅ Tamamlandı |
| **v2.0.2** | 2026-10-23 | Ergonomik Hero Yeniden Tasarımı, Ortalı Hemen Oku Butonları | ✅ Tamamlandı |
| **v2.0.1** | 2026-10-23 | UI İyileştirmeleri, Hero HTML Kodu Düzeltmesi, Tarihe Göre Okuma İptali | ✅ Tamamlandı |
| **v2.0.0** | 2026-10-23 | Modüler Mimari, Anı Defteri, Caching, Kalite Bekçileri, Dinamik Kapaklar | ✅ Tamamlandı |
| **v1.3.x** | 2026-10-12 | 5 Gruplu Yönetici Paneli, Ücretsiz Kategori Tarama, Çoklu Seri Önceliği | ✅ Tamamlandı |
| **v1.2.x** | 2026-10-12 | Türkçe / Dutch Dil Ayrımı, Akşam Kuralı, Cin Ali Önceliği | ✅ Tamamlandı |
| **v1.1.x** | 2026-10-12 | GitHub `data` Branch Kalıcı Senkronizasyon, "Atlas Okudu" Ayrımı | ✅ Tamamlandı |
| **v1.0.x** | 2026-10-09 | Yaşı Geçti Etiketi, Kategori İncelemesi, Kompakt Hero | ✅ Tamamlandı |
| **v0.8.x** | 2026-10-09 | De Vuurvlinder Okul Kitapları, Open Library ISBN Entegrasyonu | ✅ Tamamlandı |
| **v0.6 - v0.7** | 2026-10-04 | Akıllı Bilim Sınıflandırması, UI İyileştirmeleri, Akşam 19:00 Filtresi | ✅ Tamamlandı |
| **v0.1 - v0.5** | 2026-09-30 | İlk Kurulum, SQLite Veritabanı, Kitap Kataloğu ve Şifreli Giriş | ✅ Tamamlandı |
| **v2.1+** | Gelecek | Okuma Zamanlayıcısı, Avatar Sistemi, Turso/libSQL Senkronu | 📋 Planlandı |

---

## 🚀 Sürüm Detayları

### [v2.0.4] - 2026-10-23
- **Hero Sol Alan Ultra-Kompakt Düzen:**
  - `👋 Merhaba Atlas!` başlığı ve `🔥 Seri` rozeti tek bir yatay satırda birleştirildi (`hero-header-row`).
  - Görev durumu, yuvalar ve motivasyon mesajı (`🎯 Günün Görevi: [⭐] [ ] 1/2 • ✨ Hedefe 1 kitap kaldı`) tek bir kapsül çubukta birleştirilerek dikeyde 2 ayrı satır yerine tek satıra indirgendi.
  - Streamlit dikey blok boşlukları (`[data-testid="stVerticalBlock"] gap: 5px !important`), buton padding'leri ve sütun arası boşlukları (`gap="medium"`, `gap="small"`) daraltılarak toplam hero yüksekliği yarı yarıya düşürüldü; sağ kart ile dikey yükseklik birebir eşitlendi.

### [v2.0.3] - 2026-10-23
- **Hero Sol Alan Dikey Kompaktlaştırma:**
  - Fazlalık oluşturan `🚀 Günlük Okuma Macerası` hap rozeti kaldırıldı.
  - Başlık (`1.45rem`) ve alt başlık (`0.84rem`) font ve satır aralıkları optimize edildi.
  - Görev çubuğu ve slot boyutları kompaktlaştırılarak (`24px`) gereksiz dikey alan tüketimi engellendi.
  - Aksiyon butonları dolgu ve yazı boyutları (`0.86rem`, `padding: 7px 10px`) revize edildi; böylece sol karşılama bölümü sağdaki başarı kartı ile aynı dikey yüksekliğe eşitlendi.

### [v2.0.2] - 2026-10-23
- **Ergonomik Hero ("Merhaba Atlas") Yeniden Tasarımı:**
  - Hero alanı 2 dengeli bölüme ayrıldı:
    - **Sol Alan (Karşılama & Görev):** "🚀 Günlük Okuma Macerası" rozeti, sıcak selamlama, dinamik motivasyon cümlesi, görsel görev çubuğu (yuvalar, hedef oranı ve seri rozeti), ve hemen altında 50-50 simetrik yerleştirilmiş iki adet büyük, dokunmatik dostu beyaz aksiyon butonu (`🎡 Sihirli Çarkı Çevir`, `🎲 Rastgele 4 Kitap`).
    - **Sağ Alan (Glassmorphic Başarı Kartı):** Buzlu cam efektli şık kart içerisinde Seviye, seviye unvanı ("Kitap Kaşifi"), altın ışıltılı XP ilerleme çubuğu, sonraki seviyeye kalan XP ve yan yana iki mini başarı kutucuğu ("👦 Kendim Okudum", "📅 Bu Ay Toplam").
- **Ortalı Kitap Altı Butonları ("Hemen Oku"):**
  - Kitap kartlarının altındaki `📖 Hemen Oku` butonları, görsellerin altına tam ortalanacak şekilde hap (pill) biçiminde (`max-width: 200px`, `border-radius: 99px`) ortalandı.

### [v2.0.1] - 2026-10-23
- **Ana Sayfa UI & Buton Düzeni İyileştirmesi:**
  - Hero kutusu aksiyon butonları (`Sihirli Çark` ve `Rastgele Öner`) hero kutusunun içine alındı; butonlar beyaz renk ve `use_container_width=True` ile derli toplu hale getirildi.
  - Kategori filtre butonları orijinal beyaz kart formatına (`min-height: 64px`, `box-shadow`, kitap sayıları ve seçili kart kenarlığı) geri getirildi, butonlar arasındaki anlamsız boşluklar giderildi.
- **Hero HTML Kod Bloğu Düzeltmesi:**
  - Sağ üstteki Seviye ve Atlas'ın kendi okudukları alanındaki çok satırlı boşluk kaynaklı `<pre><code>` raw HTML görünümü sıfırlandı.
- **Tarihe Göre Okuma İptali (Undo Reading):**
  - Yönetici panelindeki "Son okumayı geri al" sekmesinde kitaplar **en son okunma tarihine göre azalan sırada (en son okunan ilk)** listelendi.
  - Kullanıcı tercihine göre opsiyonel olarak **🔤 Alfabetik (A-Z)** sıralama seçeneği eklendi.

### [v2.0.0] - 2026-10-23 (Büyük Mimari ve Kalite Dönüşümü)
* **Modüler Mimari Refactoring:**
  - 2.600 satırlık dev monolitik dosya (`Library.py`) sorumluluklarına göre parçalandı:
    - `core/`: Merkezi konfigürasyon (`config.py`) ve context manager tabanlı veritabanı motoru (`db.py`).
    - `services/`: `book_service`, `reading_service`, `recommendation_service`, `classifier_service`, `isbn_service`, `memory_service`.
    - `ui/`: `components.py`, `covers.py`, `audio.py`, `styles.py`.
    - `app_pages/`: `home.py`, `library.py`, `journey.py`, `badges.py`, `memories.py`, `admin.py`.
  - `Library.py` geriye dönük tam uyumluluk köprüsü olarak korundu (`app.py`'yi çalıştırır).
* **✨ Anı Defteri (Reading Memories) Modülü:**
  - Kitaplar hakkında Atlas'ın ve ailenin unutulmaz yorumları, kitap replikleri ve 1-5 yıldız arası değerlendirme sistemi eklendi.
  - Veritabanına `reading_memories` tablosu kazandırıldı.
* **Performans ve Önbellekleme:**
  - `@st.cache_data` mekanizması ile kitap ve okuma sorguları optimize edildi (sayfa geçişleri 5-10 kat hızlandı).
  - Kitap ekleme, silme, düzenleme ve onaylama durumlarında otomatik cache geçersiz kılma (`clear_books_cache`, `clear_logs_cache`) uygulandı.
* **Modern Streamlit Standartları:**
  - `st.navigation` ve `st.Page` yerel yönlendirmesine geçildi.
  - Kullanımdan kalkan `use_container_width=True` parametreleri temizlendi.
  - `.streamlit/config.toml` tema paleti uygulama renkleriyle (`#4F7CFF`) uyumlu hale getirildi.
* **Veritabanı Bütünlüğü ve İndeksleme:**
  - 8 adet performans B-Tree indeksi eklendi (`reading_log(book_id, read_at, status)` ve `books(category, language, is_school, is_outgrown)`).
  - `sync_read_counts()` fonksiyonu ile sayaç doğrulama ve senkronizasyon aracı geliştirildi.
* **Çocuk Odaklı UX (Atlas İçin Eğlenceli Detaylar):**
  - **Dinamik Kapaklar (`ui/covers.py`):** Kapağı bulunmayan kitaplar için deterministik renklerle çocuk kitabı mockup kapakları üretildi.
  - **Web Audio API (`ui/audio.py`):** Okuma onayında ve hedeflerde harici dosyasız neşeli kutlama tınıları eklendi.
* **🛡️ Kalite ve Bekçi Sistemleri:**
  - **Kapsam Bekçisi (`tests/test_kapsam_bekcisi.py`):** Her fonksiyonun test edilmesini garanti eden AST tabanlı bekçi kuruldu.
  - **Doküman Bekçisi (`tests/test_dokuman_bekcisi.py`):** README'nin tüm modülleri ve Anı Defterini kapsamasını denetleyen bekçi kuruldu.
  - Toplam 46 birim ve entegrasyon testi ile `run_tests.py` test koşucusu eklendi.

---

### [v1.3.x] - 2026-10-12
- **Yönetici Paneli Optimizasyonu:** 15 dağınık sekme, 5 organize ana sekme altında toplandı (`Onaylar`, `Kitaplar`, `Kapaklar`, `Öneri & Düzen`, `Sistem`).
- **Ücretsiz Otomatik Kategori Tarama:** Seri tutarlılığı ve başlık analiziyle çalışan, internetsiz kategori tahmin motoru geliştirildi.
- **Çoklu Öncelikli Seri:** Öncelikli serilerin listeden çoklu seçilebilmesi ve yeni serilerin kitap başlığı önekiyle eklenebilmesi sağlandı.
- **Responsive Tablolar:** İçerik satır sayısına göre yüksekliği otomatik ayarlayan tablo gösterimi.
- **Senkron Durum İyileştirmesi:** Kenar çubuğu eşitleme metni sadeleştirilerek sadece saat formatına dönüştürüldü.

---

### [v1.2.x] - 2026-10-12
- **Dillere Göre Ayrım:** Türkçe ve Dutch dil ayrımı yapıldı.
- **Otomatik Dil Tespiti:** Hollandaca kelime ve yayınevi listesi (`looks_dutch`) ile diller otomatik etiketlendi.
- **Akşam Kuralı (19:00+):** Akşam okumalarında sakinlik için Aktivite ve Dutch kitapların öneri havuzundan hariç tutulması kuralı eklendi.
- **Cin Ali Önceliği:** Öncelikli serilerden günde en fazla belirlenen kota kadar (varsayılan: 1) kitap önerilmesi sağlandı.
- **Amsterdam Saat Dilimi:** Tüm kayıt ve commit saatleri `Europe/Amsterdam` saat dilimine sabitlendi.

---

### [v1.1.x] - 2026-10-12
- **Kalıcı Bulut Veritabanı (`cloud_db.py`):** Streamlit Cloud'un geçici disk problemine karşı, GitHub'ın ayrı `data` branch'inde `db/atlas_library.sql` iterdump dökümü tutan arka plan senkronizasyonu kuruldu.
- **👦 Atlas Okudu Ayrımı:** Okumayı Atlas'ın kendi başına okuyup okumadığını belirten `by_atlas` bayrağı ve bağımsız okuma sayaçları eklendi.
- **Güvenlik Yükseltmesi:** `ADMIN_PIN` ve `APP_PASSWORD` koddan çıkartılarak Streamlit Secrets altına taşındı.
- **Brute-Force Koruması:** Hatalı parola denemelerinde artan bekleme süresi eklendi.

---

### [v1.0.x] - 2026-10-09
- **🎒 Yaşı Geçti Etiketi:** Atlas'ın yaşının geçtiği bebek/ilk dönem kitaplarını öneri havuzundan çıkaran ama kütüphane arşivinde saklayan bayrak eklendi.
- **Kategori İncelemesi:** Kitap başlıkları araştırılarak 100+ kitabın kategorisi gözden geçirildi (`category_review.csv`).
- **Kompakt Hero Alanı:** Günlük hedef ve seviye durumu tek satırda birleştirildi.
- **Hedef Yuvaları:** Günlük hedef için onaylı (✅), bekleyen (⏳) ve boş yuva görselleştirmesi.

---

### [v0.8.x] - 2026-10-09
- **🏫 De Vuurvlinder Okul Kitapları:** Okuldan getirilen geçici kitapların doğrudan Dutch okuma ve XP hanesine yazılmasını sağlayan hızlı ekleme akışı oluşturuldu.
- **Open Library Entegrasyonu:** ISBN numarası ile Open Library API'den başlık, yazar, yayınevi ve kapak görselini otomatik çeken servis eklendi.
- **Sayfa Bilgisi Esnekliği:** Sayfa sayısı olmayan kitaplarda varsayılan sabit değer yerine boş bırakılabilme imkanı sağlandı.

---

### [v0.6 - v0.7] - 2026-10-04 / 10-05
- **🔬 Akıllı Bilim Kategorizasyonu:** Kitap adı ve alt kategoriler analiz edilerek bilim içerikli kitapların otomatik tespit edilmesi.
- **🌙 Gece Kuralı:** Saat 19:00 sonrası uyku öncesi önerilerde Aktivite kategorisinin elenmesi.
- **Sidebar Optimizasyonu:** Sol kenar çubuğunun dikey sığdırılması ve kaydırma çubuğu olmadan tek ekrana oturması.
- **Kapak Yönetimi:** Görseli eksik olan kitaplar için özel yönetim sekmesi eklendi.

---

### [v0.1 - v0.5] - 2026-09-30
- **İlk Yayın:** Projenin SQLite veritabanı ve temel Streamlit arayüzü ile kuruluşu.
- **Katalog ve Filtreleme:** Ev kitaplarının listelenmesi, arama ve filtreleme özellikleri.
- **Okuma Takibi ve XP:** Okunan kitapları işaretleme ve seviye hesaplama algoritması.
- **Şifreli Giriş:** Uygulama giriş güvenliği.

---

## 🔮 Gelecek Yol Haritası (Planned & Upcoming)

### 📌 v2.1.0 - Etkileşim ve Çocuk Motivasyonu
- [ ] **Birlikte Okuma Zamanlayıcısı:** 15 veya 20 dakikalık geri sayım yapan, animasyonlu eğlenceli okuma sayacı.
- [ ] **Atlas'ın Karakteri (Avatar Sistemi):** Atlas'ın seçebileceği ve seviye atladıkça evrimleşen sevimli maskot (Minik Ejderha 🐉 -> Kitap Şövalyesi 🛡️ -> Galaksi Bilgini 🚀).
- [ ] **Haftalık Okuma Raporu:** Pazartesi günleri ebeveynlere haftalık okuma özeti sunan görsel karne.

### 📌 v2.2.0 - Bulut Altyapısı ve Gerçek Zamanlı Senkronizasyon
- [ ] **Turso (libSQL) Edge SQLite Desteği:** GitHub'a SQL dökümü göndermek yerine doğrudan SQLite uyumlu Turso bulut veritabanı desteği ile sıfır gecikmeli çoklu cihaz senkronizasyonu.
- [ ] **Supabase PostgreSQL Alternatifi:** Opsiyonel PostgreSQL backend desteği.

### 📌 v2.3.0 - Zengin Medya ve Sesli Hatıralar
- [ ] **Sesli Anılar:** Anı Defterine Atlas'ın ses kaydını yükleyebilme özelliği.
- [ ] **Resim ve Çizim Defteri:** Atlas'ın okuduğu kitap hakkında yaptığı resimlerin fotoğraflarını anıya iliştirme imkanı.
