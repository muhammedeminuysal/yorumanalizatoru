# Yorum Analiz Asistanı (Hackathon Projesi)

Bu proje, yapay zeka (Gemini API) kullanarak e-ticaret ürün yorumlarını analiz eden, duygu dağılımını çıkaran ve yönetici özetleri sunan kapsamlı bir platformdur. 

## 🚀 Özellikler
- **Tekli Analiz**: Bir ürün adı girerek o ürün hakkında internetteki genel kanıyı sentetik olarak analiz eder.
- **Toplu Analiz**: Yüklenen CSV veya Excel dosyasındaki yorumları duygu, kategori ve puan bağlamında değerlendirir.
- **Karşılaştırma**: İki farklı ürünün analiz sonuçlarını yan yana getirir ve bir kazanan belirler.
- **Akıllı Ajan**: Manuel girilen yorum setleri üzerinden yönetici özeti ve aksiyon planı çıkarır.
- **Dışa Aktarma**: Analiz sonuçlarını **PDF** veya **Excel** formatında indirmenizi sağlar.

## 🛠️ Kurulum ve Çalıştırma

### 1. Gereksinimleri Yükleyin
Proje, Python 3.9+ gerektirir. Backend dizinine giderek bağımlılıkları yükleyin:
```bash
cd backend
pip install -r requirements.txt
```

### 2. Ortam Değişkenlerini Ayarlayın
Projenin kök dizininde bulunan `.env` dosyasını kendi Gemini API anahtarınız ile güncelleyin:
```env
GEMINI_API_KEY=buraya_api_anahtarinizi_giriniz
```

### 3. Backend Sunucusunu Başlatın
Backend klasöründe iken Flask uygulamasını başlatın:
```bash
python app.py
```
Sunucu varsayılan olarak `http://localhost:5000` adresinde çalışacaktır.

### 4. Frontend'i Çalıştırın
`frontend` klasöründeki `index.html` dosyasını herhangi bir modern web tarayıcısında (Chrome, Edge, Safari vb.) doğrudan açarak veya bir Live Server eklentisi kullanarak arayüze erişebilirsiniz.

## 📚 API Dokümantasyonu

### `POST /api/sentetik`
Ürün adına göre sentetik analiz döner.
- **Body**: `{"urun_adi": "iPhone 13"}`
- **Response**: JSON (genel_memnuniyet, kronik_sikayet_orani, duygu_dagilimi, kor_noktalar vb.)

### `POST /api/toplu`
CSV veya Excel dosyasındaki yorumları analiz eder.
- **Body**: `multipart/form-data` (dosya)
- **Response**: JSON (toplam yorum, ortalama puan, kategori dağılımı)

### `POST /api/karsilastir`
İki ürünü karşılaştırır.
- **Body**: `{"urun1": "X", "urun2": "Y"}`
- **Response**: JSON (Her iki ürünün analiz sonucu ve kazanan)

### `POST /api/ajan`
Verilen spesifik yorumlara göre yönetici özeti oluşturur.
- **Body**: `{"urun_adi": "X", "yorumlar": ["yorum1", "yorum2"]}`
- **Response**: JSON (yonetici_ozeti, iyilestirmeler, aksiyonlar)

### `POST /api/pdf` & `POST /api/excel`
Rapor oluşturur ve dosya olarak indirir.

## 🌟 Tekli Analiz İyileştirmeleri

Sistem, tekli analiz sürecinde sadece duygu dağılımı yapmakla kalmaz, aynı zamanda tespit edilen sorunlar için dinamik çözümler üretir.
- **İki Aşamalı Yapay Zeka Mantığı**: İlk aşamada kronik şikayetler tespit edilir. İkinci aşamada her bir şikayet için özel bir Gemini promptu (`temperature=0.9` ile) tetiklenir ve her ürüne/soruna özel eşsiz "Önerilen Çözüm" metinleri üretilir.
- **Gelişmiş Excel Çıktısı**: Tekli analiz sonucunda indirilen Excel raporu, doğrudan "Toplu Analiz" modülünde girdi olarak kullanılabilecek formattadır. Sentetik olarak üretilen yorumlar; `Yorum`, `Duygu`, `Kategori`, `Puan` ve `Önerilen Çözüm` sütunlarını barındırır.
- **UI Entegrasyonu**: Önerilen Çözüm modülü, arayüzde özel olarak tasarlanmış renkli bir kutu (highlighted box) içerisinde sunulmaktadır.

## 🌟 Toplu Analiz Stabilizasyonu

Sistemin toplu analiz modülü tamamen gerçek Gemini API bağlantısı ve güvenilir (robust) algoritmalar ile çalışmaktadır:
- **Deterministic Prompt & Temperature**: Modelin her yoruma özel, tam uyumlu ve "sadece JSON" döneceği katı bir şablon (STRICT FORMAT) kullanılır. `temperature=0.1` ile rastgelelik azaltılarak tutarlı ve güvenilir kararlar alınması sağlanmıştır.
- **1:1 Mapping (Eşleştirme)**: Toplu şekilde gönderilen 5'li yorum gruplarında, API'den dönen sonuç sayısı eksik veya hatalı olsa bile, kod içi uzunluk kontrolleri ve *fallback* (yedek) mekanizmaları sayesinde frontend ve DataFrame akışı asla kopmaz ve 1'e 1 eşleşme garanti edilir.
- **Robust JSON Parsing**: Regex destekli filtreleme ile yapay zekanın araya sıkıştırabileceği ("İşte analiz sonuçları:" gibi) fazladan metinler temizlenerek uygulamanın çökmesi (`JSONDecodeError`) kalıcı olarak önlenmiştir.

## 🌟 Karşılaştırma Geliştirmeleri (Hibrit Avantaj Analizi)

Ürün karşılaştırma sekmesi basit bir metrik tablosundan ziyade, derinlemesine içgörüler sunan bir "Avantaj Analizi" sistemine dönüştürülmüştür.
- **AI + Metrik Kombinasyonu (Hibrit Sistem)**: Uygulama öncelikle iki ürünün sayısal farklarını (memnuniyet oranları, şikayet istatistikleri) hesaplar. Ardından bu verileri Gemini AI modeline sunarak "A ürünü X'te, B ürünü Y'de daha iyidir" tarzında akıllı bir özet (`genel_degerlendirme`) üretir.
- **2 Sütunlu Karşılaştırma UI**: Hangi ürünün hangi konuda üstün olduğunu daha net vurgulamak adına metriklerde görsel renklendirmeler (iyi değerler yeşil) yapılmıştır. Her iki ürünün benzersiz avantajları, kendi kartında listeli bir şekilde sergilenir.
- **Kullanıcı Faydası**: Kullanıcı, sadece skoru yüksek olanı değil, skoru düşük olmasına rağmen spesifik bir özelliğiyle öne çıkan alternatif ürünü de net bir biçimde idrak eder (Örn: Fiyat/Performans veya dayanıklılık gibi).

## ⚡ Sistem Performansı ve API Timeout Optimizasyonu

Gemini API üzerinde oluşan 30 saniyelik timeout (zaman aşımı) hatalarını kalıcı olarak çözmek için sistemin temel mimarisi optimize edilmiştir:
- **Tek İstek (Single Prompt) - Çok Çözüm**: Tekli analizde tespit edilen her şikayet için API'ye ayrı ayrı gidilip gelinmek yerine (Sequential Loop); tüm sorunlar tek bir isteğe sıkıştırılmış, cevaplar tek bir JSON Array olarak alınarak analiz süresi dramatik şekilde hızlandırılmıştır.
- **Multi-threading (Paralel İşleme)**: Backend tarafında (`app.py`), Karşılaştırma ve Akıllı Ajan gibi birbirinden bağımsız veri çeken fonksiyonlar `concurrent.futures.ThreadPoolExecutor` aracılığıyla asenkronize edilmiş ve aynı anda paralel olarak çalıştırılarak bekleme süresi yarı yarıya indirilmiştir.
- **Daha Küçük Batch Boyutları & UX**: Toplu Analiz gruplaması (batch_size) 5'ten 3'e düşürülerek yük dağıtılmış, Frontend üzerinde timeout koruması 90 saniyeye çekilip kullanıcı dostu bilgilendirici asenkron mesajlarla (`Sayfayı kapatmayın...`) desteklenmiştir.

---
*Geliştiriciler: Yorum Analiz Hackathon Ekibi*
