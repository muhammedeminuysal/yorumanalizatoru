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
    model = genai.GenerativeModel("gemini-2.5-flash")
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
    Hata durumlarında anlamlı mesaj döner.
    """
    if not model:
        return {"hata": "GEMINI_API_KEY bulunamadı. Lütfen .env dosyanızı kontrol edin."}
        
    urun_key = urun_adi.lower().strip()
    if urun_key in _analiz_cache:
        return _analiz_cache[urun_key]
    
    prompt = f"""
    Görevin: "{urun_adi}" ürünü hakkında detaylı bir tüketici yorum analizi yap.
    Bu ürün internette satıldığında insanların en çok övdüğü ve kronik şikayet ettikleri konuları hatırla.
    
    SADECE aşağıdaki JSON formatında cevap ver, başka metin ekleme:
    {{
        "urun_adi": "{urun_adi}",
        "genel_ozet": "Kullanıcıların genel görüşü...",
        "olumlu_yonler": ["öne çıkan 3 madde"],
        "sikayetler": ["en çok şikayet edilen 3 konu"],
        "ortalama_puan": 7.5,
        "oneri": "Geliştirme önerisi..."
    }}
    """
    try:
        # Timeout süresi genai yapılandırması içerisinde veya Flask tarafında ele alınır
        response = model.generate_content(prompt)
        text = response.text
        
        json_match = re.search(r"\{.*\}", text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
        else:
            result = json.loads(text)
            
        # Arayüz ile uyumluluk için formatlama
        puan = float(result.get("ortalama_puan", 7.5))
        result["genel_memnuniyet"] = int(puan * 10)
        result["kronik_sikayet_orani"] = max(100 - result["genel_memnuniyet"] - 10, 0)
        
        duygu_dagilimi = [
            {"name": "Pozitif", "value": result["genel_memnuniyet"], "color": "#10B981"},
            {"name": "Nötr", "value": max(100 - result["genel_memnuniyet"] - result["kronik_sikayet_orani"], 0), "color": "#9CA3AF"},
            {"name": "Kritik", "value": result["kronik_sikayet_orani"], "color": "#EF4444"}
        ]
        result["duygu_dagilimi"] = duygu_dagilimi
        
        # Kronik sorunların yanına dinamik "Önerilen Çözüm" ekleniyor (Aşama 2 - Optimize: Tek İstek)
        kor_noktalar = []
        sikayetler = result.get("sikayetler", [])
        
        if sikayetler:
            cozum_prompt = f"'{urun_adi}' ürünü için müşteriler şu konularda şikayetçi:\n"
            for idx, s in enumerate(sikayetler):
                cozum_prompt += f"{idx+1}. {s}\n"
            cozum_prompt += "\nBu sorunları çözmek için her birine özel, eyleme geçirilebilir 1-2 cümlelik yenilikçi çözüm önerileri sun. Yanıtını KESİN JSON dizisi formatında dön:\n"
            cozum_prompt += "[\n  {\"baslik\": \"şikayet adı\", \"detay\": \"çözüm önerisi\"}\n]"
            
            try:
                cozum_response = model.generate_content(
                    cozum_prompt, 
                    generation_config=genai.types.GenerationConfig(temperature=0.7)
                )
                cozum_text = cozum_response.text
                json_match_cozum = re.search(r"\[.*\]", cozum_text, re.DOTALL)
                
                if json_match_cozum:
                    cozum_array = json.loads(json_match_cozum.group())
                else:
                    cozum_array = json.loads(cozum_text)
                    
                # Hata ve eksik sonuçlara karşı eşleştirme
                for idx, s in enumerate(sikayetler):
                    if idx < len(cozum_array):
                        kor_noktalar.append({"baslik": s, "detay": cozum_array[idx].get("detay", "Süreç iyileştirilmelidir.")})
                    else:
                        kor_noktalar.append({"baslik": s, "detay": "Kalite kontrol süreçlerinin artırılması önerilir."})
            except Exception as e:
                print(f"Çözüm üretme hatası: {str(e)}")
                for s in sikayetler:
                    kor_noktalar.append({"baslik": s, "detay": "Müşteri iletişiminin güçlendirilmesi önerilir."})
            
        result["kor_noktalar"] = kor_noktalar
        result["analiz_edilen_urun"] = urun_adi
        result["toplam_yorum"] = "Sentetik Üretim"
        
        # Cache'e kaydet
        _analiz_cache[urun_key] = result
        
        return result
        
    except json.JSONDecodeError:
        return {"hata": "Gemini yanıtı geçerli bir JSON değil. Lütfen tekrar deneyin."}
    except Exception as e:
        return {"hata": f"Gemini API Hatası: {str(e)}"}

def toplu_grup_analiz(yorumlar_grubu: list) -> list[dict]:
    # Model yüklü değilse fallback dön
    if not model:
        return [{"duygu": "Nötr", "kategori": "Hata", "puan": 5, "onerilen_cozum": "API Key eksik"} for _ in yorumlar_grubu]
        
    prompt = f"""
    Aşağıda numaralandırılmış {len(yorumlar_grubu)} adet müşteri yorumu bulunmaktadır.
    Her bir yorumu analiz et ve aşağıdaki KESİN JSON dizisi (array) formatında cevap ver.
    Cevabın sadece geçerli bir JSON dizisi olmalı, kod bloğu (```json) veya başka hiçbir metin içermemeli.

    Format:
    [
      {{
        "yorum_no": 1,
        "duygu": "Pozitif", # Sadece: Pozitif, Negatif veya Nötr
        "kategori": "Kargo", # Sadece: Kargo, Kalite, Fiyat, Müşteri Hizmetleri, Genel
        "puan": 8, # 1 ile 10 arasında bir sayı
        "onerilen_cozum": "..." # Eğer duygu Negatif ise 1 cümlelik çözüm, değilse '-' bırak
      }}
    ]

    Yorumlar:
    """
    for i, y in enumerate(yorumlar_grubu):
        prompt += f"{i+1}. {y}\n"
        
    try:
        # Deterministic sonuçlar için düşük temperature
        response = model.generate_content(
            prompt, 
            generation_config=genai.types.GenerationConfig(temperature=0.1)
        )
        text = response.text
        
        # Sadece JSON array kısmını ayıkla
        json_match = re.search(r"\[.*\]", text, re.DOTALL)
        if json_match:
            parsed_results = json.loads(json_match.group())
        else:
            parsed_results = json.loads(text)
            
        # Dönen sonucun boyutuyla gönderilen grubun boyutunu garanti altına al (1:1 mapping)
        sonuclar = []
        for i in range(len(yorumlar_grubu)):
            if i < len(parsed_results):
                res = parsed_results[i]
                sonuclar.append({
                    "duygu": res.get("duygu", "Nötr"),
                    "kategori": res.get("kategori", "Genel"),
                    "puan": res.get("puan", 5),
                    "onerilen_cozum": res.get("onerilen_cozum", "-")
                })
            else:
                sonuclar.append({
                    "duygu": "Nötr",
                    "kategori": "Genel",
                    "puan": 5,
                    "onerilen_cozum": "-"
                })
        return sonuclar
        
    except Exception as e:
        print(f"Toplu Analiz Hatası: {str(e)}")
        # Çökmemesi için fallback listesi
        return [{"duygu": "Nötr", "kategori": "Hata", "puan": 5, "onerilen_cozum": "Analiz edilemedi"} for _ in yorumlar_grubu]

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
    
    # 1. Yorumlar sayfası: Toplu Analiz ile %100 uyumlu sentetik veri
    yorum_verileri = []
    
    # Olumlu yönler için sentetik yorumlar
    for olumlu in sonuc.get("olumlu_yonler", []):
        yorum_verileri.append({
            "Yorum": f"Bu ürünün {olumlu.lower()} özelliğini çok beğendim, harika bir deneyim.",
            "Duygu": "Pozitif",
            "Kategori": "Genel",
            "Puan": random.randint(8, 10),
            "Önerilen Çözüm": "-"
        })
        
    # Şikayetler (kor_noktalar) için sentetik yorumlar
    for sorun in sonuc.get("kor_noktalar", []):
        kategori = sorun.get("baslik")
        cozum = sorun.get("detay")
        yorum_verileri.append({
            "Yorum": f"{kategori} konusunda ciddi sıkıntılar yaşadım, maalesef memnun kalmadım.",
            "Duygu": "Negatif",
            "Kategori": kategori,
            "Puan": random.randint(1, 4),
            "Önerilen Çözüm": cozum
        })
        
    # Ekstra Nötr yorum
    yorum_verileri.append({
        "Yorum": "Ürün fena değil ama beklentilerimi tam karşılamadı. İdare eder.",
        "Duygu": "Nötr",
        "Kategori": "Genel",
        "Puan": random.randint(5, 7),
        "Önerilen Çözüm": "-"
    })

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_yorumlar = pd.DataFrame(yorum_verileri)
        df_yorumlar.to_excel(writer, sheet_name="Yorumlar", index=False)
        
        ozet_df = pd.DataFrame({
            "Metrik": ["Genel Memnuniyet", "Kronik Şikayet Oranı"],
            "Değer": [sonuc.get("genel_memnuniyet"), sonuc.get("kronik_sikayet_orani")]
        })
        ozet_df.to_excel(writer, sheet_name="Ozet", index=False)
        
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

def karsilastirma_avantaj_analizi(urun1_adi, sonuc1, urun2_adi, sonuc2):
    if not model:
        return {
            "urun_a_avantajlar": ["API bağlantısı eksik, veri okunamadı."],
            "urun_b_avantajlar": ["API bağlantısı eksik, veri okunamadı."],
            "genel_degerlendirme": "Avantaj analizi için geçerli bir API Key gereklidir."
        }
        
    memnuniyet1 = sonuc1.get("genel_memnuniyet", 0)
    sikayet1 = sonuc1.get("kronik_sikayet_orani", 0)
    olumlu1 = sonuc1.get("olumlu_yonler", [])
    sorunlar1 = [s.get("baslik", "") for s in sonuc1.get("kor_noktalar", [])]
    
    memnuniyet2 = sonuc2.get("genel_memnuniyet", 0)
    sikayet2 = sonuc2.get("kronik_sikayet_orani", 0)
    olumlu2 = sonuc2.get("olumlu_yonler", [])
    sorunlar2 = [s.get("baslik", "") for s in sonuc2.get("kor_noktalar", [])]
    
    prompt = f"""
    İki ürün analiz edildi ve sayısal karşılaştırmaları yapıldı. Görevin, bu iki ürün arasında tarafsız ve derinlemesine bir "Avantaj Analizi" yapmak.
    
    Ürün 1: {urun1_adi}
    - Genel Memnuniyet: %{memnuniyet1}
    - Kronik Şikayet Oranı: %{sikayet1}
    - Öne Çıkan Olumlu Yönler: {olumlu1}
    - Şikayet Edilen Konular: {sorunlar1}
    
    Ürün 2: {urun2_adi}
    - Genel Memnuniyet: %{memnuniyet2}
    - Kronik Şikayet Oranı: %{sikayet2}
    - Öne Çıkan Olumlu Yönler: {olumlu2}
    - Şikayet Edilen Konular: {sorunlar2}
    
    Yukarıdaki verilere dayanarak, hangi ürünün hangi konularda daha avantajlı olduğunu SADECE aşağıdaki KESİN JSON formatında üret.
    Format dışına çıkma ve başka hiçbir metin (örneğin ```json vb.) ekleme.
    
    {{
      "urun_a_avantajlar": ["{urun1_adi} için madde 1", "{urun1_adi} için madde 2"],
      "urun_b_avantajlar": ["{urun2_adi} için madde 1", "{urun2_adi} için madde 2"],
      "genel_degerlendirme": "İki ürünün detaylı, tarafsız ve karşılaştırmalı net özeti..."
    }}
    """
    
    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(temperature=0.3)
        )
        text = response.text
        json_match = re.search(r"\{.*\}", text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        else:
            return json.loads(text)
    except Exception as e:
        print(f"Karşılaştırma Analizi Hatası: {str(e)}")
        return {
            "urun_a_avantajlar": [f"Genel Memnuniyet: %{memnuniyet1}"],
            "urun_b_avantajlar": [f"Genel Memnuniyet: %{memnuniyet2}"],
            "genel_degerlendirme": "Detaylı yapay zeka analizi API hatası nedeniyle oluşturulamadı."
        }
