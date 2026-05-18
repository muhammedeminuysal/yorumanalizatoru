# backend/app.py
from concurrent.futures import ThreadPoolExecutor
import os
import json
import pandas as pd
import io
import time
import re  
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from dotenv import load_dotenv

current_dir = os.path.dirname(os.path.abspath(__file__))
# current_dir backend klasörüdür. '..' diyerek bir üst klasördeki (Yorum_analiz_asistanı) .env'yi buluruz.
load_dotenv(dotenv_path=os.path.join(current_dir, "..", ".env"))
# Analiz motorundan fonksiyonları içe aktarıyoruz

from analiz_engine import (
    sentetik_analiz,
    toplu_grup_analiz,
    excel_olustur,
    akilli_ajan_analizi
)

app = Flask(__name__)
CORS(app)  # Tüm originlere izin ver

@app.route('/api/sentetik', methods=['POST'])
def sentetik():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"hata": "Geçersiz JSON formatı"}), 400
        
        urun = data.get('urun_adi', '').strip()
        if not urun:
            return jsonify({"hata": "Ürün adı boş olamaz"}), 400
            
        if len(urun) > 100:
            return jsonify({"hata": "Ürün adı çok uzun (maksimum 100 karakter)"}), 400
            
        # Özel karakter filtresi (temel seviye)
        # + ve # gibi yaygın ürün karakterlerine izin veren esnek regex
        
        # 💡 DÜZELTME 2: Türkçe karakter desteği içeren güvenli regex yapısı
        if not re.match(r'^[\w\s\-\.,\+#&ığüşöçİĞÜŞÖÇ]+$', urun):
            return jsonify({"hata": "Ürün adı geçersiz karakterler içeriyor"}), 400

        sonuc = sentetik_analiz(urun)
        if "hata" in sonuc:
            return jsonify(sonuc), 500
            
        return jsonify(sonuc)
    except Exception as e:
        app.logger.error(f"Sentetik Analiz Hatası: {str(e)}")
        return jsonify({"hata": "Sunucu içi beklenmeyen hata"}), 500

@app.route('/api/toplu', methods=['POST'])

def toplu_analiz():
    if 'dosya' not in request.files:
        return jsonify({"hata": "Dosya gönderilmedi"}), 400
    dosya = request.files['dosya']
    if dosya.filename == '':
        return jsonify({"hata": "Dosya seçilmedi"}), 400
    
    try:
        if dosya.filename.endswith('.csv'):
            df = pd.read_csv(dosya)
        else:
            df = pd.read_excel(dosya)
    except Exception as e:
        return jsonify({"hata": f"Dosya okunamadı: {str(e)}"}), 400
    
    yorum_sutunu = next((col for col in df.columns if col.lower() in ['yorum', 'yorumlar', 'comment', 'review']), None)
    if yorum_sutunu is None:
        return jsonify({"hata": "Yorum sütunu bulunamadı (Sütun adı 'yorum', 'yorumlar' olmalı)"}), 400
    
    yorumlar = df[yorum_sutunu].dropna().astype(str).tolist()
    if not yorumlar:
        return jsonify({"hata": "Yorumlar boş"}), 400
        
    gruplar = [yorumlar[i:i+5] for i in range(0, len(yorumlar), 5)]
    
    # 💡 DÜZELTME: Eski yavaş for döngüsü yerine ThreadPoolExecutor ile paralel analiz yapıyoruz
    sonuclar = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        # Tüm grupları aynı anda Gemini'a gönderiyoruz
        paralel_gorevler = list(executor.map(toplu_grup_analiz, gruplar))
        
        # Gelen sonuçları tek bir listede birleştiriyoruz
        for grup_sonuc in paralel_gorevler:
            sonuclar.extend(grup_sonuc)
    
    # DataFrame güncellemeleri
    df['Duygu'] = [s['duygu'] for s in sonuclar] + ['']*(len(df)-len(sonuclar))
    df['Kategori'] = [s['kategori'] for s in sonuclar] + ['']*(len(df)-len(sonuclar))
    df['Puan'] = [s['puan'] for s in sonuclar] + ['']*(len(df)-len(sonuclar))
    
    pozitif_sayisi = sum(1 for s in sonuclar if s['duygu'] == 'Olumlu')
    negatif_sayisi = sum(1 for s in sonuclar if s['duygu'] == 'Olumsuz')
    ortalama_puan = sum(s['puan'] for s in sonuclar) / len(sonuclar) if sonuclar else 0
    
    kategori_sayilari = {}
    for s in sonuclar:
        kat = s['kategori']
        kategori_sayilari[kat] = kategori_sayilari.get(kat, 0) + 1
    
    return jsonify({
        "toplam_yorum": len(yorumlar),
        "pozitif_sayisi": pozitif_sayisi,
        "negatif_sayisi": negatif_sayisi,
        "ortalama_puan": round(ortalama_puan, 2),
        "kategori_dagilimi": kategori_sayilari,
        "veriler": df.to_dict(orient="records")
    })

@app.route('/api/karsilastir', methods=['POST'])
def karsilastir():
    print("🚨 DİKKAT: YENİ KARŞILAŞTIRMA KODU ÇALIŞTI!") # Terminalden doğru dosyanın çalıştığını kanıtlamak için
    
    data = request.get_json(silent=True) or {}
    urun1 = data.get('urun1', '').strip()
    urun2 = data.get('urun2', '').strip()
    
    if not urun1 or not urun2:
        return jsonify({"hata": "İki ürün adı da gerekli"}), 400
    
    # 1. Ürün Analizi
    sonuc1 = sentetik_analiz(urun1)
    if "hata" in sonuc1:
        return jsonify({"hata": f"1. Ürün Reddedildi: {sonuc1['hata']}"}), 500
        
    print("⏳ Gemini API dinlendiriliyor (3 saniye mola)...")
    time.sleep(3) # 💡 ÇÖZÜM: İki ürün analizi arasında API kotasını doldurmamak için bekliyoruz!
    
    # 2. Ürün Analizi
    sonuc2 = sentetik_analiz(urun2)
    if "hata" in sonuc2:
        return jsonify({"hata": f"2. Ürün Reddedildi: {sonuc2['hata']}"}), 500
        
    memnuniyet1 = sonuc1.get('genel_memnuniyet', 0)
    memnuniyet2 = sonuc2.get('genel_memnuniyet', 0)
    
    if memnuniyet1 > memnuniyet2:
        kazanan = urun1
    elif memnuniyet2 > memnuniyet1:
        kazanan = urun2
    else:
        kazanan = "Berabere"
    
    return jsonify({
        "urun1": {"adi": urun1, "sonuc": sonuc1},
        "urun2": {"adi": urun2, "sonuc": sonuc2},
        "kazanan": kazanan
    })

@app.route('/api/ajan', methods=['POST'])
def ajan():
    try:
        data = request.get_json(silent=True) or {}
        urun_adi = data.get('urun_adi', '').strip()
        yorumlar = data.get('yorumlar', [])
        link = data.get('link', '').strip()
        
        if not urun_adi:
            return jsonify({"hata": "Ürün adı gerekli"}), 400
            
        if not yorumlar and not link:
            return jsonify({"hata": "Analiz için ya bir link ya da manuel yorumlar gönderilmelidir."}), 400
            
        # Eğer link geldiyse, analiz motoruna linki; gelmediyse yorum listesini geçiyoruz
        if link:
            sonuc = akilli_ajan_analizi(urun_adi, yorumlar=[], link=link)
        else:
            sonuc = akilli_ajan_analizi(urun_adi, yorumlar=yorumlar, link="")
            
        return jsonify(sonuc)
        
    except Exception as e:
        app.logger.error(f"Ajan Hatası: {str(e)}")
        return jsonify({"hata": "Ajan çalışırken beklenmeyen bir hata oluştu."}), 500



@app.route('/api/excel', methods=['POST'])
def excel_indir():
    data = request.get_json(silent=True) or {}
    urun_adi = data.get('urun_adi')
    sonuc = data.get('sonuc')
    if not urun_adi or not sonuc:
        return jsonify({"hata": "Ürün adı ve sonuç gerekli"}), 400
        
    try:
        excel_bytes = excel_olustur(urun_adi, sonuc)
        return send_file(
            io.BytesIO(excel_bytes),
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f"{urun_adi}_rapor.xlsx"
        )
    except Exception as e:
        return jsonify({"hata": f"Excel oluşturulamadı: {str(e)}"}), 500

if __name__ == '__main__':
    # 5000 portunda Flask sunucusu başlatılıyor
    app.run(debug=True, port=5000)
