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

---
*Geliştiriciler: Yorum Analiz Hackathon Ekibi*
