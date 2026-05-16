import google.generativeai as genai
import os
from dotenv import load_dotenv

# API anahtarını .env dosyasından çekiyoruz
load_dotenv()
api_anahtarim = os.getenv("GEMINI_API_KEY")

if not api_anahtarim:
    print("🚨 HATA: .env dosyasında GEMINI_API_KEY bulunamadı!")
    exit()

genai.configure(api_key=api_anahtarim)

print("="*50)
print("🚀 HESABINIZA TANIMLI KULLANILABİLİR MODELLER")
print("="*50)

# Sadece "metin/içerik üretme" (generateContent) yeteneği olan modelleri listeliyoruz
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(f"✅ {m.name}")
        
print("="*50)