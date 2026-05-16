import google.generativeai as genai
from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import json
from dotenv import load_dotenv

print("="*50)
print(" 🚀 SİNYAL: EVRENSEL E-TİCARET ASİSTANI (RİSKSİZ SÜRÜM)")
print("="*50)

load_dotenv()
api_anahtarim = os.getenv("GEMINI_API_KEY")

if not api_anahtarim:
    print("\n🚨 HATA: .env dosyasından GEMINI_API_KEY okunamadı!")
    exit()

genai.configure(api_key=api_anahtarim)
model = genai.GenerativeModel('gemini-3.1-flash-lite')

app = Flask(__name__)
CORS(app)

@app.route('/api/analiz', methods=['POST'])
def analiz_et():
    gelen_veri = request.json
    urun_girdisi = gelen_veri.get('urun_linki', 'Bilinmeyen Ürün')
    
    print(f"\n🚀 Analiz Başladı! Aranan: {urun_girdisi}")

    prompt = f"""
    Sen e-ticaret sitelerindeki milyonlarca müşteri yorumunu analiz eden uzman bir yapay zekasın.
    Kullanıcı arama kutusuna şunu yazdı (bu bir ürün adı veya link olabilir): "{urun_girdisi}"

    GÖREVİN:
    1. Bu girdinin hangi ürüne veya ürün kategorisine ait olduğunu anla.
    2. Bu ürün internette satıldığında insanların en çok övdüğü ve özellikle KRONİK OLARAK ŞİKAYET ETTİĞİ şeyleri hatırla.
    3. SADECE aşağıdaki formatta, eksiksiz bir JSON çıktısı ver. Başka hiçbir açıklama yazma.

    {{
      "analiz_edilen_urun": "Anladığın Ürün Adı (Örn: Apple iPhone 13)",
      "genel_memnuniyet": 85, 
      "kronik_sikayet_orani": 10, 
      "toplam_yorum": 3250, 
      "kaynak_bilgisi": "Bu tespitleri genellikle hangi platformlardan edindiğini yaz. (Örn: 'Şikayetvar verileri, teknoloji forumları ve Amazon/Trendyol müşteri değerlendirmelerinden sentezlenmiştir.')",
      "kor_noktalar": [
        {{
          "baslik": "Kullanıcıların En Sık Yaşadığı 1. Sorun",
          "detay": "Bu sorunu yaşayan bir müşterinin kurabileceği örnek bir eleştiri cümlesi."
        }},
        {{
          "baslik": "Kullanıcıların En Sık Yaşadığı 2. Sorun",
          "detay": "Bu sorunu yaşayan bir müşterinin kurabileceği örnek bir eleştiri cümlesi."
        }}
      ]
    }}
    """

    try:
        response = model.generate_content(prompt)
        cikti = response.text.replace('```json', '').replace('```', '').strip()
        veri = json.loads(cikti)
        
        notr_deger = 100 - veri["genel_memnuniyet"] - veri["kronik_sikayet_orani"]
        
        veri["duygu_dagilimi"] = [
            {"name": "Pozitif", "value": veri["genel_memnuniyet"], "color": "#10B981"},
            {"name": "Nötr", "value": max(0, notr_deger), "color": "#9CA3AF"},
            {"name": "Kritik", "value": veri["kronik_sikayet_orani"], "color": "#EF4444"}
        ]
        
        return jsonify(veri)

    except Exception as e:
        print(f"🚨 Hata: {e}")
        return jsonify({"hata": "Analiz başarısız. Lütfen ürün adını daha anlaşılır yazın."}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)