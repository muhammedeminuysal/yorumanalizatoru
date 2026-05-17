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
    Structured Outputs (Mecburi JSON) kullanarak Regex ihtiyacını ortadan kaldırır
    ve her şikayet için özel çözüm üretir.
    """
    if not model:
        return {"hata": "GEMINI_API_KEY bulunamadı. Lütfen .env dosyanızı kontrol edin."}
        
    # urun_key burada tanımlanıyor (Cache mekanizması için)
    urun_key = urun_adi.lower().strip()
    if urun_key in _analiz_cache:
        return _analiz_cache[urun_key]
    
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
        "ortalama_puan": 7.5
    }}
    """
    try:
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        text = response.text.strip()
        result = json.loads(text)
            
        puan = float(result.get("ortalama_puan", 7.5))
        result["genel_memnuniyet"] = int(puan * 10)
        result["kronik_sikayet_orani"] = max(100 - result["genel_memnuniyet"] - 10, 0)
        
        duygu_dagilimi = [
            {"name": "Pozitif", "value": result["genel_memnuniyet"], "color": "#10B981"},
            {"name": "Nötr", "value": max(100 - result["genel_memnuniyet"] - result["kronik_sikayet_orani"], 0), "color": "#9CA3AF"},
            {"name": "Kritik", "value": result["kronik_sikayet_orani"], "color": "#EF4444"}
        ]
        result["duygu_dagilimi"] = duygu_dagilimi
        
        # Şikayetler doğrudan başlık, detay ve çözüm içeriyor
        result["kor_noktalar"] = result.get("sikayetler", [])
        
        result["analiz_edilen_urun"] = urun_adi
        result["toplam_yorum"] = "Sentetik Üretim"
        
        # Cache'e kaydet
        _analiz_cache[urun_key] = result
        
        return result
        
    except json.JSONDecodeError:
        return {"hata": "Gemini yanıtı geçerli bir JSON formatında oluşturamadı. Lütfen tekrar deneyin."}
    except Exception as e:
        return {"hata": f"Gemini API Hatası: {str(e)}"}
def toplu_grup_analiz(yorumlar_grubu: list) -> list[dict]:
    # Basit bir mock fonksiyonu
    sonuclar = []
    for yorum in yorumlar_grubu:
        sonuclar.append({
            "duygu": random.choice(["Olumlu", "Olumsuz", "Nötr"]),
            "kategori": random.choice(["Kalite", "Kargo", "Fiyat", "İade"]),
            "puan": round(random.uniform(3, 9), 1)
        })
    return sonuclar

def pdf_olustur(urun_adi, sonuc):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.cell(200, 10, text=f"Urun Analiz Raporu: {urun_adi}", ln=1, align="C")
    pdf.ln(10)
    
    memnuniyet = sonuc.get("genel_memnuniyet", "?")
    pdf.cell(200, 10, text=f"Genel Memnuniyet: %{memnuniyet}", ln=1)
    kronik = sonuc.get("kronik_sikayet_orani", "?")
    pdf.cell(200, 10, text=f"Kronik Sikayet Orani: %{kronik}", ln=1)
    pdf.ln(10)
    
    pdf.cell(200, 10, text="Kronik Sorunlar:", ln=1)
    for sorun in sonuc.get("kor_noktalar", []):
        pdf.multi_cell(0, 10, text=f"{sorun.get('baslik')}: {sorun.get('detay')}")
        pdf.ln(2)
        
    return pdf.output(dest='S').encode('latin-1', errors='replace')

def excel_olustur(urun_adi, sonuc):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        pd.DataFrame([{"Metin": "Sentetik analiz", "Duygu": "Pozitif"}]).to_excel(writer, sheet_name="Yorumlar", index=False)
        ozet_df = pd.DataFrame({
            "Metrik": ["Genel Memnuniyet", "Kronik Şikayet Oranı"],
            "Değer": [sonuc.get("genel_memnuniyet"), sonuc.get("kronik_sikayet_orani")]
        })
        ozet_df.to_excel(writer, sheet_name="Ozet", index=False)
        sikayet_df = pd.DataFrame(sonuc.get("kor_noktalar", []))
        sikayet_df.to_excel(writer, sheet_name="Sikayet Kategorileri", index=False)
    output.seek(0)
    return output.getvalue()

def ajan_adim1_veri_hazirla(urun_adi, yorumlar):
    return {"urun": urun_adi, "yorum_sayisi": len(yorumlar)}

def ajan_adim2a_duygu(urun_adi, yorumlar):
    return [{"yorum_no": i+1, "duygu": "Olumlu", "guven": 0.9} for i in range(len(yorumlar))]

def ajan_adim2b_kategoriler(urun_adi, yorumlar):
    return [{"kategori": "Kargo", "adet": 3, "ornekler": ["Gec geldi"]}]

def ajan_adim2c_iyilestirmeler(urun_adi, sikayet_kategorileri):
    return ["Kargo hizi artirilmali", "Kalite kontrol iyilestirilmeli"]

def ajan_adim3_rapor(urun_adi, duygu_sonuclari, kategori_sonuclari, iyilestirmeler):
    return f"{urun_adi} icin analiz tamamlandi. Onerilen aksiyonlar alinmali."

def ajan_adim4_aksiyonlar(urun_adi, kategoriler, iyilestirmeler):
    return [f"Aksiyon: {iyilestirmeler[0]}"]
