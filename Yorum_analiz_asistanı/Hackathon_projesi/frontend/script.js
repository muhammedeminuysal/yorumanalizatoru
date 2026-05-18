// frontend/script.js

const API_BASE = "http://localhost:5000";

// --- Tab Sistemi ---
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        // Aktif buton ve içeriği sıfırla
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        
        // Tıklananı aktif yap
        btn.classList.add('active');
        const tabId = btn.getAttribute('data-tab');
        document.getElementById(tabId).classList.add('active');
    });
});

// --- Yardımcı Fonksiyonlar ---
async function apiCall(endpoint, method, body) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 saniye timeout

    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            method: method,
            headers: { "Content-Type": "application/json" },
            body: body ? JSON.stringify(body) : undefined,
            signal: controller.signal
        });
        clearTimeout(timeoutId);

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.hata || `API Hatası: HTTP ${response.status}`);
        }
        return await response.json();
    } catch (err) {
        if (err.name === 'AbortError') {
            throw new Error("İstek zaman aşımına uğradı (30 saniye). Gemini API geç yanıt veriyor olabilir.");
        }
        throw err;
    }
}

function puanRengi(p) {
    if (p >= 7.5) return "#22c55e"; // Yeşil
    if (p >= 5) return "#f59e0b"; // Turuncu
    return "#ef4444"; // Kırmızı
}

function isValidInput(text) {
    if (!text || text.trim().length === 0) return { valid: false, msg: "Alan boş bırakılamaz." };
    
    // 💡 E-Ticaret URL bağlantısıysa karakter filtresine takılmadan onay ver
    if (text.startsWith("http://") || text.startsWith("https://")) {
        return { valid: true };
    }
    
    if (text.length > 100) return { valid: false, msg: "Girdi çok uzun (maks 100 karakter)." };
    const regex = /^[\w\s\-\.,+#&ığüşöçİĞÜŞÖÇ]+$/i;
    if (!regex.test(text)) return { valid: false, msg: "Girdi geçersiz özel karakterler içeriyor." };
    return { valid: true };
}

// --- UI Güncelleme (Tekli Analiz) ---
let chartInstance = null; // Global chart değişkeni

function displaySentetikSonuc(data, urunAdi) {
    const resultDiv = document.getElementById("sonuc-alani");
    if (!resultDiv) return;
    
    if (data.hata) {
        resultDiv.innerHTML = `<div class="error">❌ ${data.hata}</div>`;
        return;
    }

    const memnuniyet = data.genel_memnuniyet || "?";
    const kronik = data.kronik_sikayet_orani || "?";
    const duyguDagilimi = data.duygu_dagilimi || [];
    const kronikSorunlar = data.kor_noktalar || [];

    // Puan Rengi mantığı
    const onUzerindenPuan = (memnuniyet !== "?" ? memnuniyet / 10 : "?");
    const skorRenk = puanRengi(onUzerindenPuan);

    // 💡 DÜZELTME: Sabit HTML yazısı yerine, her şikayete ait kendi s.cozum verisini ekrana basıyoruz.
    const sorunHTML = kronikSorunlar.map(s => `
        <div class="sorun-item">
            <h4>⚠️ ${s.baslik || "Bilinmeyen Sorun"}</h4>
            <p>${s.detay || "Detay bulunamadı."}</p>
            ${s.cozum ? `<div style="margin-top:0.5rem; font-size:0.9rem; color:#a5f3fc;">💡 <strong>Önerilen Çözüm:</strong> ${s.cozum}</div>` : ''}
        </div>
    `).join('');

    resultDiv.innerHTML = `
        <div class="metric-grid">
            <div class="metric">
                <h3>📊 Memnuniyet Skoru</h3>
                <div class="value" style="color: ${skorRenk}">${onUzerindenPuan} <span style="font-size:1rem; color:#94a3b8">/10</span></div>
            </div>
            <div class="metric"><h3>🔴 Kronik Şikayet</h3><div class="value">%${kronik}</div></div>
            <div class="metric"><h3>📝 Analiz Edilen</h3><div class="value">${data.analiz_edilen_urun || urunAdi}</div></div>
            <div class="metric"><h3>🗂️ Analiz Türü</h3><div class="value">${data.toplam_yorum || "?"}</div></div>
        </div>
        
        <div style="display: flex; gap: 2rem; margin-top: 1rem; flex-wrap: wrap;">
            <div style="flex: 1; min-width: 250px;">
                <canvas id="sentimentChart" width="200" height="200"></canvas>
            </div>
            <div style="flex: 2; min-width: 300px;">
                <h3 style="margin-bottom: 1rem; color: #cbd5e1;">🧩 Kronik Şikayet Noktaları</h3>
                <div class="sorun-listesi">
                    ${sorunHTML || "<p>Herhangi bir kronik sorun tespit edilmedi.</p>"}
                </div>
            </div>
        </div>
        
        <div class="button-group" style="justify-content: center; margin-top: 2rem;">
            <button id="excel-indir" style="background: #10b981;">📊 Excel Rapor İndir</button>
        </div>
    `;

    // Chart.js Çizimi
    if (duyguDagilimi.length > 0) {
        const ctx = document.getElementById('sentimentChart').getContext('2d');
        if (chartInstance) chartInstance.destroy(); 
        
        chartInstance = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: duyguDagilimi.map(d => d.name),
                datasets: [{
                    data: duyguDagilimi.map(d => d.value),
                    backgroundColor: duyguDagilimi.map(d => d.color),
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom', labels: { color: 'white' } }
                }
            }
        });
    }

    // İndirme Butonları Eventleri
    document.getElementById("pdf-indir")?.addEventListener("click", () => indirRapor(urunAdi, data, "pdf"));
    document.getElementById("excel-indir")?.addEventListener("click", () => indirRapor(urunAdi, data, "excel"));
}

async function indirRapor(urunAdi, sonuc, tip) {
    try {
        const response = await fetch(`${API_BASE}/api/${tip}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ urun_adi: urunAdi, sonuc: sonuc })
        });
        if (!response.ok) throw new Error("Rapor oluşturulamadı");
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `${urunAdi}_rapor.${tip === "pdf" ? "pdf" : "xlsx"}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    } catch (error) {
        alert("Rapor indirme hatası: " + error.message);
    }
}

// --- Ana Event Listener'lar ---
document.addEventListener("DOMContentLoaded", () => {
    
    // 1) Tekli Analiz
    const analizBtn = document.getElementById("analiz-btn");
    if (analizBtn) {
        analizBtn.addEventListener("click", async () => {
            const urunAdi = document.getElementById("urun-adi").value.trim();
            const valid = isValidInput(urunAdi);
            if (!valid.valid) {
                alert("Hata: " + valid.msg);
                return;
            }

            const sonucDiv = document.getElementById("sonuc-alani");
            sonucDiv.innerHTML = `<div class="loading"><div class="spinner"></div><p>⏳ Analiz yapılıyor... (Gemini değerlendiriyor, işlem 5-10 saniye sürebilir)</p></div>`;
            try {
                const data = await apiCall("/api/sentetik", "POST", { urun_adi: urunAdi });
                displaySentetikSonuc(data, urunAdi);
            } catch (err) {
                sonucDiv.innerHTML = `<div class="error">❌ Hata: ${err.message}</div>`;
            }
        });
    }

    // 2) Toplu Analiz
    const topluBtn = document.getElementById("toplu-analiz-btn");
    if (topluBtn) {
        topluBtn.addEventListener("click", async () => {
            const dosya = document.getElementById("toplu-dosya").files[0];
            if (!dosya) {
                alert("Lütfen bir CSV veya Excel dosyası seçin");
                return;
            }
            
            const sonucDiv = document.getElementById("toplu-sonuc");
            sonucDiv.innerHTML = `<div class="loading"><div class="spinner"></div><p>⏳ Toplu analiz yapılıyor...</p></div>`;
            
            try {
                const formData = new FormData();
                formData.append("dosya", dosya);
                
                const response = await fetch(`${API_BASE}/api/toplu`, {
                    method: "POST",
                    body: formData
                });
                
                const data = await response.json();
                if (!response.ok) throw new Error(data.hata || "Toplu analiz başarısız");
                
                let html = `<h3>📊 Toplu Analiz Sonuçları</h3>
                            <div class="metric-grid">
                                <div class="metric"><h3>Toplam Yorum</h3><div class="value">${data.toplam_yorum}</div></div>
                                <div class="metric"><h3>Ortalama Puan</h3><div class="value">${data.ortalama_puan} / 10</div></div>
                                <div class="metric" style="color:#10b981"><h3>Pozitif</h3><div class="value">${data.pozitif_sayisi}</div></div>
                                <div class="metric" style="color:#ef4444"><h3>Negatif</h3><div class="value">${data.negatif_sayisi}</div></div>
                            </div>
                            <h4 style="margin-top:1rem; margin-bottom:0.5rem">Kategori Dağılımı:</h4><ul>`;
                for (const [kat, adet] of Object.entries(data.kategori_dagilimi)) {
                    html += `<li style="margin-left: 2rem;">${kat}: ${adet} adet</li>`;
                }
                html += `</ul>`;
                sonucDiv.innerHTML = html;
            } catch (err) {
                sonucDiv.innerHTML = `<div class="error">❌ Hata: ${err.message}</div>`;
            }
        });
    }

    // 3) Karşılaştırma
    // 3) Karşılaştırma
    const karsilastirBtn = document.getElementById("karsilastir-btn");
    if (karsilastirBtn) {
        karsilastirBtn.addEventListener("click", async () => {
            const urun1 = document.getElementById("karsilastir-urun1").value.trim();
            const urun2 = document.getElementById("karsilastir-urun2").value.trim();
            
            if (!isValidInput(urun1).valid || !isValidInput(urun2).valid) {
                alert("Lütfen iki ürün adı için de geçerli isimler girin.");
                return;
            }

            const sonucDiv = document.getElementById("karsilastir-sonuc");
            sonucDiv.innerHTML = `<div class="loading"><div class="spinner"></div><p>⏳ Karşılaştırma yapılıyor... (İki ürün de analiz ediliyor)</p></div>`;
            try {
                const data = await apiCall("/api/karsilastir", "POST", { urun1, urun2 });
                
                // 💡 DÜZELTME 1: Ürünlerin olumlu yönlerini HTML liste elemanına dönüştürüyoruz
                const avantajlarHTML1 = (data.urun1.sonuc.olumlu_yonler || [])
                    .map(yon => `<li style="margin-bottom:0.4rem; color:#e2e8f0;">✅ ${yon}</li>`).join('');
                    
                const avantajlarHTML2 = (data.urun2.sonuc.olumlu_yonler || [])
                    .map(yon => `<li style="margin-bottom:0.4rem; color:#e2e8f0;">✅ ${yon}</li>`).join('');

                // Kazanan başlığı için kazanan rengini belirleyelim
                // Kazanan başlığı için kazanan rengini belirleyelim
                const kazananYazisi = data.kazanan === "Berabere" ? "🤝 Berabere!" : `🏆 Kazanan: ${data.kazanan}`;

                // 💡 DÜZELTME: Yanlış yorum satırları () düzeltildi ve kartların yan yana durması için Flexbox eklendi
                let html = `
                    <h3 style="text-align:center; color:#facc15; font-size:1.5rem; margin-bottom:1.5rem">${kazananYazisi}</h3>
                    
                    <div style="display: flex; gap: 20px; justify-content: center; flex-wrap: wrap; width: 100%;">
                        
                        <div class="card" style="flex: 1; min-width: 280px; margin-bottom:0; border-top: 4px solid #38bdf8; box-sizing: border-box;">
                            <h4 style="color:#38bdf8; font-size:1.3rem; margin-bottom:0.8rem">${data.urun1.adi}</h4>
                            <div style="font-size:1.2rem; margin-bottom:1rem; background:rgba(250,204,21,0.1); padding:0.5rem; border-radius:6px; display:inline-block;">
                                ⭐ <strong>Ürün Puanı:</strong> <span style="color:#facc15; font-weight:bold;">${data.urun1.sonuc.ortalama_puan || '?'} / 10</span>
                            </div>
                            <p><strong>Genel Memnuniyet:</strong> %${data.urun1.sonuc.genel_memnuniyet || 'Bilinmiyor'}</p>
                            <p><strong>Kronik Şikayet:</strong> %${data.urun1.sonuc.kronik_sikayet_orani || 'Bilinmiyor'}</p>
                            
                            <h5 style="margin-top:1.2rem; margin-bottom:0.5rem; color:#10b981; font-size:1rem;">🟢 Öne Çıkan Avantajları:</h5>
                            <ul style="list-style:none; padding-left:0; margin-top:0.5rem; font-size:0.95rem;">
                                ${avantajlarHTML1 || '<li style="color:#94a3b8;">Avantaj bilgisi üretilemedi.</li>'}
                            </ul>
                        </div>
                        
                        <div class="card" style="flex: 1; min-width: 280px; margin-bottom:0; border-top: 4px solid #a855f7; box-sizing: border-box;">
                            <h4 style="color:#a855f7; font-size:1.3rem; margin-bottom:0.8rem">${data.urun2.adi}</h4>
                            <div style="font-size:1.2rem; margin-bottom:1rem; background:rgba(250,204,21,0.1); padding:0.5rem; border-radius:6px; display:inline-block;">
                                ⭐ <strong>Ürün Puanı:</strong> <span style="color:#facc15; font-weight:bold;">${data.urun2.sonuc.ortalama_puan || '?'} / 10</span>
                            </div>
                            <p><strong>Genel Memnuniyet:</strong> %${data.urun2.sonuc.genel_memnuniyet || 'Bilinmiyor'}</p>
                            <p><strong>Kronik Şikayet:</strong> %${data.urun2.sonuc.kronik_sikayet_orani || 'Bilinmiyor'}</p>
                            
                            <h5 style="margin-top:1.2rem; margin-bottom:0.5rem; color:#10b981; font-size:1rem;">🟢 Öne Çıkan Avantajları:</h5>
                            <ul style="list-style:none; padding-left:0; margin-top:0.5rem; font-size:0.95rem;">
                                ${avantajlarHTML2 || '<li style="color:#94a3b8;">Avantaj bilgisi üretilemedi.</li>'}
                            </ul>
                        </div>
                        
                    </div>`;
                sonucDiv.innerHTML = html;
            } catch (err) {
                sonucDiv.innerHTML = `<div class="error">❌ Hata: ${err.message}</div>`;
            }
        });
    }

    // 4) Akıllı Ajan
    const ajanBtn = document.getElementById("ajan-btn");
    if (ajanBtn) {
        ajanBtn.addEventListener("click", async () => {
            const urunAdi = document.getElementById("ajan-urun").value.trim();
            const inputMetni = document.getElementById("ajan-yorumlar").value.trim();
            
            if (!isValidInput(urunAdi).valid) {
                alert("Ürün adı geçersiz.");
                return;
            }
            if (inputMetni.length === 0) {
                alert("Lütfen bir e-ticaret linki yapıştırın veya manuel yorum girin.");
                return;
            }

            // Girdinin link olup olmadığını doğruluyoruz
            const isUrl = inputMetni.startsWith("http://") || inputMetni.startsWith("https://");
            let payload = { urun_adi: urunAdi };
            
            if (isUrl) {
                payload.link = inputMetni;
            } else {
                const yorumlar = inputMetni.split("\n").filter(l => l.trim().length > 0);
                if (yorumlar.length === 0) {
                    alert("En az bir geçerli yorum girmelisiniz.");
                    return;
                }
                payload.yorumlar = yorumlar;
            }

            const sonucDiv = document.getElementById("ajan-sonuc");
            sonucDiv.innerHTML = `<div class="loading"><div class="spinner"></div><p>⏳ ${isUrl ? 'Verilen linkten veriler analize alınıyor...' : 'Manuel yorumlar analiz ediliyor...'} (Güven ve doğruluk oranları hesaplanıyor)</p></div>`;
            
            try {
                // Backend'e hazırlanan dinamik paketi gönderiyoruz
                const data = await apiCall("/api/ajan", "POST", payload);

                const guvenRenk = data.guven_skoru >= 75 ? "#10b981" : "#f59e0b";

                // Tablo satırlarını dinamik oluşturma
                const tabloSatirlari = data.kategori_analizi && data.kategori_analizi.length > 0 
                    ? data.kategori_analizi.map(k => `
                        <tr>
                            <td style="padding: 0.75rem; border-bottom: 1px solid rgba(255,255,255,0.1);"><strong>${k.kategori}</strong></td>
                            <td style="padding: 0.75rem; border-bottom: 1px solid rgba(255,255,255,0.1);">
                                <span style="background: ${k.durum === 'İyi' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)'}; 
                                             color: ${k.durum === 'İyi' ? '#10b981' : '#ef4444'}; 
                                             padding: 0.25rem 0.6rem; border-radius: 0.25rem; font-size: 0.8rem; font-weight: bold; border: 1px solid ${k.durum === 'İyi' ? 'rgba(16,185,129,0.3)' : 'rgba(239,68,68,0.3)'};">
                                    ${k.durum}
                                </span>
                            </td>
                            <td style="padding: 0.75rem; border-bottom: 1px solid rgba(255,255,255,0.1); color: #38bdf8; font-weight: bold;">%${k.etki_orani}</td>
                            <td style="padding: 0.75rem; border-bottom: 1px solid rgba(255,255,255,0.1); font-size: 0.9rem; color: #cbd5e1;">${k.detay}</td>
                        </tr>
                    `).join('') 
                    : '<tr><td colspan="4" style="padding:1rem; text-align:center;">Kategori analizi oluşturulamadı.</td></tr>';

                // Ham alıntı bloklarını oluşturma
                const alintiHTML = data.kritik_alintilar && data.kritik_alintilar.length > 0
                    ? data.kritik_alintilar.map(a => `
                        <blockquote style="border-left: 4px solid #6366f1; background: rgba(255,255,255,0.02); padding: 0.75rem; margin-bottom: 0.75rem; border-radius: 0 0.5rem 0.5rem 0; font-style: italic; color: #94a3b8; line-height: 1.4;">
                            "${a}"
                        </blockquote>
                    `).join('')
                    : '<p style="color:#94a3b8;">Belirgin bir alıntı eşlenemedi.</p>';

                let html = `
                    <div class="metric-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 1rem;">
                        <div class="metric" style="background: rgba(255,255,255,0.03); padding: 1rem; border-radius: 0.75rem; border: 1px solid rgba(255,255,255,0.05); text-align: center;">
                            <h3>🤖 Ajan Güven Skoru</h3>
                            <div class="value" style="color: ${guvenRenk}">%${data.guven_skoru || 0}</div>
                        </div>
                        <div class="metric" style="background: rgba(255,255,255,0.03); padding: 1rem; border-radius: 0.75rem; border: 1px solid rgba(255,255,255,0.05); text-align: center;">
                            <h3>🟢 Pozitif Oranı</h3>
                            <div class="value" style="color: #10b981;">%${data.pozitif_oran || 0}</div>
                        </div>
                        <div class="metric" style="background: rgba(255,255,255,0.03); padding: 1rem; border-radius: 0.75rem; border: 1px solid rgba(255,255,255,0.05); text-align: center;">
                            <h3>🔴 Negatif Oranı</h3>
                            <div class="value" style="color: #ef4444;">%${data.negatif_oran || 0}</div>
                        </div>
                    </div>

                    <div class="card" style="background: rgba(99, 102, 241, 0.08); border-color: rgba(99, 102, 241, 0.2); margin-top: 1rem; padding: 1.25rem; border-radius: 0.75rem;">
                        <h3 style="color: #818cf8; margin-bottom: 0.5rem; font-size: 1.1rem;">🧠 Stratejik Yönetici Özeti ${isUrl ? '(Link Analizi)' : '(Manuel Yorum)'}</h3>
                        <p style="color: #cbd5e1; line-height: 1.6; font-size: 0.95rem;">${data.yonetici_ozeti || 'Özet üretilemedi.'}</p>
                    </div>

                    <div class="card" style="margin-top: 1rem; padding: 1.25rem; border-radius: 0.75rem; overflow-x: auto;">
                        <h4 style="color: #facc15; margin-bottom: 1rem; font-size: 1rem;">📊 Detaylı Kategori ve Doğruluk Kırılımı</h4>
                        <table style="width: 100%; border-collapse: collapse; text-align: left; font-size: 0.9rem;">
                            <thead>
                                <tr style="color: #94a3b8; font-size: 0.85rem; border-bottom: 2px solid rgba(255,255,255,0.1);">
                                    <th style="padding: 0.5rem 0.75rem;">Kategori</th>
                                    <th style="padding: 0.5rem 0.75rem;">Durum</th>
                                    <th style="padding: 0.5rem 0.75rem;">Doğruluk/Başarı</th>
                                    <th style="padding: 0.5rem 0.75rem;">Ajan Tespiti</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${tabloSatirlari}
                            </tbody>
                        </table>
                    </div>

                    <div class="karsilastir-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1rem; margin-top: 1rem;">
                        <div class="card" style="margin-bottom: 0; padding: 1.25rem; border-radius: 0.75rem;">
                            <h4 style="color: #a5f3fc; margin-bottom: 0.75rem; font-size: 1rem;">💬 Kritik Alıntılar</h4>
                            ${alintiHTML}
                        </div>
                        <div class="card" style="margin-bottom: 0; padding: 1.25rem; border-radius: 0.75rem;">
                            <h4 style="color: #38bdf8; margin-bottom: 0.75rem; font-size: 1rem;">🎯 Atılması Gereken Somut Aksiyonlar</h4>
                            <ul style="margin-left: 1.2rem; color: #cbd5e1; display: flex; flex-direction: column; gap: 0.6rem; line-height: 1.4; font-size: 0.9rem;">
                                ${data.aksiyonlar ? data.aksiyonlar.map(a => `<li>${a}</li>`).join('') : '<li>Aksiyon maddesi üretilemedi.</li>'}
                            </ul>
                        </div>
                    </div>
                `;

                sonucDiv.innerHTML = html;

            } catch (err) {
                sonucDiv.innerHTML = `<div class="error">❌ Hata: ${err.message}</div>`;
            }
        });
    }
    // ==========================================
    // 🚀 ENTER TUŞU İLE OTOMATİK TETİKLEME DESTEĞİ
    // ==========================================
    
    // 1) Tekli Analiz Sekmesi için Enter
    document.getElementById("urun-adi")?.addEventListener("keypress", function(e) {
        if (e.key === "Enter") {
            e.preventDefault(); // Form tetiklenmesini ve sayfa yenilenmesini önler
            document.getElementById("analiz-btn")?.click();
        }
    });

    // 2) Karşılaştırma Sekmesi için Enter (İki girdi alanı için de geçerli)
    ["karsilastir-urun1", "karsilastir-urun2"].forEach(id => {
        document.getElementById(id)?.addEventListener("keypress", function(e) {
            if (e.key === "Enter") {
                e.preventDefault();
                document.getElementById("karsilastir-btn")?.click();
            }
        });
    });

    // 3) Akıllı Ajan Sekmesi için Enter (Sadece Ürün Adı alanında çalışır)
    document.getElementById("ajan-urun")?.addEventListener("keypress", function(e) {
        if (e.key === "Enter") {
            e.preventDefault();
            document.getElementById("ajan-btn")?.click();
        }
    });
});