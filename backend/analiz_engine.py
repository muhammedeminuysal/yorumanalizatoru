# backend/analiz_engine.py

import os
import json
import google.generativeai as genai
import pandas as pd
from fpdf import FPDF
from io import BytesIO
import re
import random

# Gemini Yapılandırması
API_KEY = os.getenv("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel("gemini-3.1-flash-lite")
else:
    model = None

_analiz_cache = {}

def puan_rengi(p: float) -> str:
    """
    Puan rengi mantığı: p >= 7.5 (Yeşil), p >= 5 (Turuncu), p < 5 (Kırmızı)
    Frontend'de kullanılmak üzere tasarlandı.
    """
    if p >= 7.5:
        return "#22c55e"
    elif p >= 5:
        return "#f59e0b"
    else:
        return "#ef4444"

def sentetik_analiz(urun_adi: str):
    """
    Gemini kullanarak sentetik ürün analizi oluşturur.
    Girdi bir ürün değilse veya HENÜZ PİYASAYA ÇIKMAMIŞSA analizi reddeder.
    """
    if not model:
        return {"hata": "GEMINI_API_KEY bulunamadı. Lütfen .env dosyanızı kontrol edin."}
        
    urun_key = urun_adi.lower().strip()
    if urun_key in _analiz_cache:
        return _analiz_cache[urun_key]

    # 💡 GÜNCELLEME: Hem ürün mü diye, hem de piyasaya çıktı mı diye kontrol ediyoruz
    # 1. AŞAMA: Ürün ve Halüsinasyon Doğrulaması (Gatekeeper)
    dogrulama_prompt = f"""
    ŞU ANKİ ZAMAN: 2026 Yılı. (Bu bilgiye dayanarak, örneğin 2024 ve 2025 yıllarında tanıtılan Samsung Galaxy S24, S25 veya iPhone 16, 17 gibi cihazlar aktif olarak piyasadadır).
    
    Sana verilen girdinin:
    1) Tüketiciler tarafından satın alınabilen fiziksel veya dijital bir E-TİCARET ÜRÜNÜ olup olmadığını kontrol et.
    2) Piyasaya fiilen sürülmüş, aktif olarak satılan bir ürün olup olmadığını kontrol et.
    
    Girdi: "{urun_adi}"
    
    Yanıtını SADECE aşağıdaki JSON formatında ver. Değerler kesinlikle tırnaksız boolean (true veya false) olmalıdır:
    {{
        "is_product": true,
        "is_released": true
    }}
    """
    try:
        dogrulama_response = model.generate_content(
            dogrulama_prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        dogrulama_data = json.loads(dogrulama_response.text.strip())
        
        # 1. Kural: Ürün değilse engelle (Okul, şehir, insan vb.)
        if not dogrulama_data.get("is_product", True):
            return {"hata": f"'{urun_adi}' geçerli bir tüketici ürünü olarak algılanmadı. Lütfen sadece e-ticaret ürünlerini analiz edin."}
            
        # 2. Kural: Ürün ama piyasaya çıkmadıysa halüsinasyonu engelle
        if not dogrulama_data.get("is_released", True):
            return {"hata": f"'{urun_adi}' henüz piyasaya sürülmemiş veya yeterli gerçek kullanıcı yorumu barındırmayan bir ürün. Sahte veri (halüsinasyon) riskine karşı analiz durduruldu."}
            
    except Exception as e:
        print(f"Ürün doğrulama adımı atlandı (Hata: {e})")
    
    # 💡 DÜZELTME 1: Prompt içindeki statik 7.5 değerini dinamik bir talimatla değiştirdik
    prompt = f"""
    "{urun_adi}" ürünü hakkında detaylı bir tüketici yorum analizi yap.
    Bu ürün internette satıldığında insanların en çok övdüğü ve kronik şikayet ettikleri konuları hatırla.
    
    Yanıtını mutlaka aşağıdaki JSON şemasına birebir uyacak şekilde yapılandır:
    {{
        "urun_adi": "Ürünün tam adı",
        "genel_ozet": "Kullanıcıların genel görüşü...",
        "olumlu_yonler": ["öne çıkan 3 madde"],
        "sikayetler": [
            {{
                "baslik": "Sorunun kısa başlığı",
                "detay": "Kullanıcıların bu konudaki şikayetinin detayı",
                "cozum": "Bu spesifik sorunu çözmek için şirkete eyleme geçirilebilir özel öneri"
            }}
        ],
        "ortalama_puan": 8.5
    }}
    
    CRITICAL: 'ortalama_puan' alanına sabit olarak 8.5 yazma! Ürünün gerçek pazar kalitesine ve tüketici hissiyatına göre 1.0 ile 10.0 arasında dinamik bir puan belirle.
    """
    try:
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        text = response.text.strip()
        
        # Terminalden ne geldiğini görebilmek için logluyoruz
        print(f"🔄 Gemini Sentetik Çıktısı ({urun_adi}): {text}")
        
        result = json.loads(text)
            
        # 💡 DÜZELTME 2: Alternatif anahtar kelime olasılıklarına karşı puan yakalamayı esnettik
        puan_degeri = result.get("ortalama_puan") or result.get("puan") or result.get("rating") or 7.5
        
        try:
            puan = float(puan_degeri)
        except:
            puan = 7.5
            
        result["ortalama_puan"] = round(puan, 1)
        result["genel_memnuniyet"] = int(puan * 10)
        result["kronik_sikayet_orani"] = max(100 - result["genel_memnuniyet"] - 10, 0)
        
        duygu_dagilimi = [
            {"name": "Pozitif", "value": result["genel_memnuniyet"], "color": "#10B981"},
            {"name": "Nötr", "value": max(100 - result["genel_memnuniyet"] - result["kronik_sikayet_orani"], 0), "color": "#9CA3AF"},
            {"name": "Kritik", "value": result["kronik_sikayet_orani"], "color": "#EF4444"}
        ]
        result["duygu_dagilimi"] = duygu_dagilimi
        
        result["kor_noktalar"] = result.get("sikayetler", [])
        result["analiz_edilen_urun"] = urun_adi
        result["toplam_yorum"] = "Sentetik Üretim"
        
        _analiz_cache[urun_key] = result
        
        return result
        
    except json.JSONDecodeError:
        return {"hata": "Gemini yanıtı geçerli bir JSON formatında oluşturamadı. Lütfen tekrar deneyin."}
    except Exception as e:
        return {"hata": f"Gemini API Hatası: {str(e)}"}
       
def toplu_grup_analiz(yorumlar_grubu: list) -> list[dict]:
    """
    Gemini API kullanarak bir grup yorumu toplu olarak analiz eder.
    Mock (rastgele) veri yerine gerçek metin analizi yapar.
    """
    if not model or not yorumlar_grubu:
        return [{"duygu": "Nötr", "kategori": "Sistem", "puan": 5.0} for _ in yorumlar_grubu]
        
    # Yorumları modele göndermek için numaralandırıp düz metne çeviriyoruz
    yorumlar_metni = "\n".join([f"{i+1}. Yorum: {y}" for i, y in enumerate(yorumlar_grubu)])
    
    prompt = f"""
    Aşağıdaki müşteri yorumlarını dikkatlice oku ve analiz et. 
    Her bir yorum için ana duygu durumunu, şikayet/övgü kategorisini ve 10 üzerinden puanını belirle.
    
    Yorumlar:
    {yorumlar_metni}
    
    Yanıtını SADECE aşağıdaki JSON formatında ve yorum sırasıyla birebir eşleşen bir DİZİ (array) olarak ver.
    Dizideki eleman sayısı tam olarak {len(yorumlar_grubu)} olmalıdır:
    [
        {{
            "duygu": "Olumlu", "Olumsuz" veya "Nötr",
            "kategori": "Kalite, Kargo, Fiyat, Paketleme, Müşteri Hizmetleri, Genel vb. tek kelimelik kategori",
            "puan": 1 ile 10 arasında bir sayı
        }}
    ]
    """
    
    try:
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        text = response.text.strip()
        sonuclar = json.loads(text)
        
        # API'den gelen cevapları asıl yorum sırasıyla eşleştirip güvene alıyoruz
        guvenli_sonuclar = []
        for i in range(len(yorumlar_grubu)):
            if i < len(sonuclar):
                # Puanı float'a, hatalı veri geldiyse 5.0'a çekiyoruz
                try:
                    p = float(sonuclar[i].get("puan", 5.0))
                except:
                    p = 5.0
                    
                guvenli_sonuclar.append({
                    "duygu": sonuclar[i].get("duygu", "Nötr"),
                    "kategori": sonuclar[i].get("kategori", "Genel"),
                    "puan": round(p, 1)
                })
            else:
                guvenli_sonuclar.append({"duygu": "Nötr", "kategori": "Eksik", "puan": 5.0})
                
        return guvenli_sonuclar

    except Exception as e:
        # Gemini kotası dolarsa veya anlık bir çökme olursa, sistemi ayakta tutacak varsayılan yanıtlar
        print(f"Toplu analiz hatası: {e}")
        return [{"duygu": "Nötr", "kategori": "Hata", "puan": 5.0} for _ in yorumlar_grubu]



def excel_olustur(urun_adi, sonuc):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        
        # 💡 DÜZELTME: Sentetik yorum satırlarını ve analiz detaylarını dinamik oluşturuyoruz
        yorum_satirlari = []
        
        # Olumlu yönlerden yorum örnekleri türetelim
        for yon in sonuc.get("olumlu_yonler", []):
            yorum_satirlari.append({"Yorum Metni": f"Bu ürünün en sevdiğim yanı: {yon}", "Duygu": "Pozitif"})
            
        # Şikayetlerden yorum örnekleri türetelim
        for sorun in sonuc.get("kor_noktalar", []):
            baslik = sorun.get('baslik', '')
            detay = sorun.get('detay', '')
            yorum_satirlari.append({"Yorum Metni": f"Maalesef sorun yaşadım. {baslik} - {detay}", "Duygu": "Kritik"})
            
        # Eğer hiç veri gelmediyse boş kalmasın diye genel özeti ekleyelim
        if not yorum_satirlari:
            yorum_satirlari.append({"Yorum Metni": sonuc.get("genel_ozet", "Analiz verisi"), "Duygu": "Nötr"})
            
        # DataFrame'e dönüştürüp "Yorumlar" sayfasına yazıyoruz
        yorumlar_df = pd.DataFrame(yorum_satirlari)
        yorumlar_df.to_excel(writer, sheet_name="Yorumlar", index=False)
        
        # Özet sayfası (Mevcut mantık korunuyor)
        ozet_df = pd.DataFrame({
            "Metrik": ["Genel Memnuniyet", "Kronik Şikayet Oranı", "Analiz Edilen Ürün"],
            "Değer": [f"%{sonuc.get('genel_memnuniyet')}", f"%{sonuc.get('kronik_sikayet_orani')}", urun_adi]
        })
        ozet_df.to_excel(writer, sheet_name="Ozet", index=False)
        
        # Şikayet kategorileri ve çözüm önerileri sayfası
        sikayet_listesi = []
        for s in sonuc.get("kor_noktalar", []):
            sikayet_listesi.append({
                "Sorun Başlığı": s.get("baslik"),
                "Sorun Detayı": s.get("detay"),
                "Önerilen Çözüm": s.get("cozum", "Kalite kontrol artırılmalı.")
            })
        
        sikayet_df = pd.DataFrame(sikayet_listesi)
        sikayet_df.to_excel(writer, sheet_name="Sikayet ve Cozumler", index=False)
        
    output.seek(0)
    return output.getvalue()

def akilli_ajan_analizi(urun_adi: str, yorumlar: list = None, link: str = ""):
    """
    Hem Manuel Yorum Listesini hem de E-Ticaret Linklerini analiz edebilen,
    dogruluk ve guven metrikleri ureten gelismis AI Ajani.
    """
    if not model:
        return {"hata": "API anahtari eksik veya model yuklenemedi."}

    if yorumlar is None:
        yorumlar = []

    # Girdi turune gore Gemini promptunu sekillendiriyoruz
    if link:
        context_talimati = f"""
        Kullanici su an analiz alanina dogrudan bir e-ticaret bağlantisi yapistirdi: '{link}'.
        Gorevin, bu '{urun_adi}' urununun belirtilen e-ticaret dunyasindaki (Trendyol, Hepsiburada, Amazon, N11, Vatan Bilgisayar vb.) opasitesini, 
        genel tuketici sikayet trendlerini ve bu link ozelindeki potansiyel satici/operasyon sorunlarini gercekci bir sekilde simule edip analiz etmektir.
        """
    else:
        yorum_metni = "\n".join([f"[{i+1}] {y}" for i, y in enumerate(yorumlar)])
        context_talimati = f"""
        Kullanici sana analiz etmen icin manuel olarak şu ham yorumlari girdi:
        {yorum_metni}
        
        Gorevin, bu dogrudan girilen musteri geri bildirimlerini titizlikle incelemektir.
        """

    prompt = f"""
    Sen profesyonel bir E-Ticaret Veri Analitigi ve Pazar Arastirmasi Ajanisin.
    Urun Odak Noktasi: "{urun_adi}"
    
    {context_talimati}
    
    Lütfen bu girdi baglamindan yola çikarak istatistiksel bir dashboard raporu hazirla.
    CRITICAL: Yanıtını oluştururken metinsel alanlar içinde asla kaçışsız çift tırnak kullanma.
    
    Yanıtını mutlaka aşağıdaki JSON şemasına %100 uyacak şekilde yapılandır:
    {{
        "yonetici_ozeti": "Urun/Link hakkinda genel analitik durum ve tuketici hissiyat ozeti.",
        "guven_skoru": 90, 
        "pozitif_oran": 70,
        "negatif_oran": 30,
        "kategori_analizi": [
            {{"kategori": "Fiyat/Performans", "durum": "İyi", "etki_orani": 90, "detay": "Fiyat segmentine gore sundugu ozellikler cok basarili bulunuyor."}},
            {{"kategori": "Paketleme ve Kargo", "durum": "Kötü", "etki_orani": 35, "detay": "Lojistik sureclerinde kutularin hasar gormesi ana sikayet odagi."}}
        ],
        "kritik_alintilar": [
            "Durumu en iyi ozetleyen 1. kullanici cumlesi",
            "Durumu ozetleyen 2. kullanici cumlesi"
        ],
        "aksiyonlar": [
            "Atilmasi gereken acil somut operasyonel adim 1",
            "Atilmasi gereken acil somut operasyonel adim 2"
        ]
    }}
    
    Not: 'guven_skoru', 'pozitif_oran' ve 'negatif_oran' alanlari sadece sayi (integer) olmalidir. 'etki_orani' o kategorinin kendi icindeki basari yuzdesidir (0-100 arasi).
    """

    try:
        # 💡 DÜZELTME 1: Yapay zekayı kesin olarak saf JSON dönmeye zorluyoruz (Regex ihtiyacını kaldırır)
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        
        text = response.text.strip()
        
        # 💡 DÜZELTME 2: Metin temizleme adımları ve doğrudan JSON'a çevirme
        result = json.loads(text)
        return result
        
    except json.JSONDecodeError as je:
        print(f"JSON Decode Hatası detayları: {je}, Gelen Ham Metin: {text}")
        return {
            "yonetici_ozeti": "Gemini geçerli bir JSON şablonu üretemedi. Lütfen isteği tekrar tetikleyin.",
            "guven_skoru": 0, "pozitif_oran": 0, "negatif_oran": 0,
            "kategori_analizi": [], "kritik_alintilar": [],
            "aksiyonlar": ["Butona tekrar basarak analizi yeniden başlatın."]
        }
    except Exception as e:
        print(f"Genel Ajan Hatası: {e}")
        return {
            "yonetici_ozeti": f"Ajan veri cozumlemesi yaparken sistem hatasi aldi: {str(e)}",
            "guven_skoru": 0, "pozitif_oran": 0, "negatif_oran": 0,
            "kategori_analizi": [], "kritik_alintilar": [],
            "aksiyonlar": ["Sistem hatası kontrol edilmeli."]
        }