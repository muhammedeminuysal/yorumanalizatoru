# backend/app.py

import os
import json
import pandas as pd
import io
import time
import concurrent.futures
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from dotenv import load_dotenv

# Sadece app.py içerisinde .env yüklüyoruz.
load_dotenv(dotenv_path="../.env")

# Analiz motorundan fonksiyonları içe aktarıyoruz
from analiz_engine import (
    sentetik_analiz,
    toplu_grup_analiz,
    pdf_olustur,
    excel_olustur,
    ajan_adim1_veri_hazirla,
    ajan_adim2a_duygu,
    ajan_adim2b_kategoriler,
    ajan_adim2c_iyilestirmeler,
    ajan_adim3_rapor,
    ajan_adim4_aksiyonlar,
    karsilastirma_avantaj_analizi
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
        import re
        if not re.match(r'^[\w\s\-\.,]+$', urun):
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
        
    gruplar = [yorumlar[i:i+3] for i in range(0, len(yorumlar), 3)]
    sonuclar = []
    for idx, grup in enumerate(gruplar):
        app.logger.info(f"Toplu Analiz: Batch {idx+1}/{len(gruplar)} işleniyor (Boyut: {len(grup)})...")
        grup_sonuc = toplu_grup_analiz(grup)
        sonuclar.extend(grup_sonuc)
        time.sleep(0.5)  # API rate limit koruması
    
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
    data = request.get_json(silent=True) or {}
    urun1 = data.get('urun1', '').strip()
    urun2 = data.get('urun2', '').strip()
    
    if not urun1 or not urun2:
        return jsonify({"hata": "İki ürün adı da gerekli"}), 400
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        f1 = executor.submit(sentetik_analiz, urun1)
        f2 = executor.submit(sentetik_analiz, urun2)
        sonuc1 = f1.result()
        sonuc2 = f2.result()
    
    if "hata" in sonuc1 or "hata" in sonuc2:
        return jsonify({"hata": "Analiz sırasında hata oluştu"}), 500
        
    memnuniyet1 = sonuc1.get('genel_memnuniyet', 0)
    memnuniyet2 = sonuc2.get('genel_memnuniyet', 0)
    
    if memnuniyet1 > memnuniyet2:
        kazanan = urun1
    elif memnuniyet2 > memnuniyet1:
        kazanan = urun2
    else:
        kazanan = "Berabere"
        
    avantaj_analizi = karsilastirma_avantaj_analizi(urun1, sonuc1, urun2, sonuc2)
    
    return jsonify({
        "urun1": {"adi": urun1, "sonuc": sonuc1},
        "urun2": {"adi": urun2, "sonuc": sonuc2},
        "kazanan": kazanan,
        "avantaj_analizi": avantaj_analizi
    })

@app.route('/api/ajan', methods=['POST'])
def ajan():
    data = request.get_json(silent=True) or {}
    urun_adi = data.get('urun_adi', '').strip()
    yorumlar = data.get('yorumlar', [])
    if not urun_adi or not yorumlar:
        return jsonify({"hata": "Ürün adı ve yorumlar gerekli"}), 400
    
    # 1. Aşama: Bağımsız süreçleri paralel çalıştır
    with concurrent.futures.ThreadPoolExecutor() as executor:
        f_adim1 = executor.submit(ajan_adim1_veri_hazirla, urun_adi, yorumlar)
        f_adim2a = executor.submit(ajan_adim2a_duygu, urun_adi, yorumlar)
        f_adim2b = executor.submit(ajan_adim2b_kategoriler, urun_adi, yorumlar)
        
        adim1 = f_adim1.result()
        adim2a = f_adim2a.result()
        adim2b = f_adim2b.result()

    # 2. Aşama: Adım 2b'ye bağımlı olanı senkron çalıştır
    iyilestirmeler = ajan_adim2c_iyilestirmeler(urun_adi, adim2b)
    
    # 3. Aşama: Son raporlama ve aksiyonları paralel çalıştır
    with concurrent.futures.ThreadPoolExecutor() as executor:
        f_rapor = executor.submit(ajan_adim3_rapor, urun_adi, adim2a, adim2b, iyilestirmeler)
        f_aksiyon = executor.submit(ajan_adim4_aksiyonlar, urun_adi, adim2b, iyilestirmeler)
        
        rapor = f_rapor.result()
        aksiyonlar = f_aksiyon.result()
    
    return jsonify({
        "adim1": adim1,
        "adim2a": adim2a,
        "adim2b": adim2b,
        "iyilestirmeler": iyilestirmeler,
        "yonetici_ozeti": rapor,
        "aksiyonlar": aksiyonlar
    })

@app.route('/api/pdf', methods=['POST'])
def pdf_indir():
    data = request.get_json(silent=True) or {}
    urun_adi = data.get('urun_adi')
    sonuc = data.get('sonuc')
    if not urun_adi or not sonuc:
        return jsonify({"hata": "Ürün adı ve sonuç gerekli"}), 400
        
    try:
        pdf_bytes = pdf_olustur(urun_adi, sonuc)
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"{urun_adi}_rapor.pdf"
        )
    except Exception as e:
        return jsonify({"hata": f"PDF oluşturulamadı: {str(e)}"}), 500

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
