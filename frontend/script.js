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
    const timeoutId = setTimeout(() => controller.abort(), 90000); // 90 saniye timeout

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
            throw new Error("İstek zaman aşımına uğradı (90 saniye). Gemini API geç yanıt veriyor olabilir.");
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
    if (text.length > 100) return { valid: false, msg: "Girdi çok uzun (maks 100 karakter)." };
    const regex = /^[\w\s\-\.,ığüşöçİĞÜŞÖÇ]+$/i;
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

    const sorunHTML = kronikSorunlar.map(s => `
        <div class="sorun-item">
            <h4>⚠️ ${s.baslik}</h4>
            <div class="solution-box">
                <span class="solution-icon">💡</span>
                <div class="solution-content">
                    <strong>Önerilen Çözüm:</strong>
                    <p>${s.detay}</p>
                </div>
            </div>
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
            <button id="pdf-indir" style="background: #ef4444;">📄 PDF Rapor İndir</button>
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
            sonucDiv.innerHTML = `<div class="loading"><div class="spinner"></div><p>⏳ Analiz yapılıyor...<br><small style="color:#9ca3af;font-size:0.85rem">(Yapay zeka değerlendiriyor, işlem 30-60 saniye sürebilir)</small></p></div>`;
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
            sonucDiv.innerHTML = `<div class="loading"><div class="spinner"></div><p>⏳ Toplu analiz yapılıyor...<br><small style="color:#9ca3af;font-size:0.85rem">(Bu işlem dosya boyutuna göre birkaç dakika sürebilir, lütfen sayfayı kapatmayın)</small></p></div>`;

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
            sonucDiv.innerHTML = `<div class="loading"><div class="spinner"></div><p>⏳ Karşılaştırma yapılıyor...<br><small style="color:#9ca3af;font-size:0.85rem">(Derinlemesine analiz ediliyor)</small></p></div>`;
            try {
                const data = await apiCall("/api/karsilastir", "POST", { urun1, urun2 });

                // Renklendirme mantığı (büyük olan yeşil olur)
                const m1 = data.urun1.sonuc.genel_memnuniyet || 0;
                const m2 = data.urun2.sonuc.genel_memnuniyet || 0;
                const s1 = data.urun1.sonuc.kronik_sikayet_orani || 0;
                const s2 = data.urun2.sonuc.kronik_sikayet_orani || 0;

                const m1Color = m1 >= m2 ? '#10b981' : '#fca5a5';
                const m2Color = m2 >= m1 ? '#10b981' : '#fca5a5';

                // Şikayet az olan daha iyidir (yeşil olur)
                const s1Color = s1 <= s2 ? '#10b981' : '#fca5a5';
                const s2Color = s2 <= s1 ? '#10b981' : '#fca5a5';

                const av1 = data.avantaj_analizi.urun_a_avantajlar || [];
                const av2 = data.avantaj_analizi.urun_b_avantajlar || [];
                const ozet = data.avantaj_analizi.genel_degerlendirme || "";

                let html = `
                    <h3 style="text-align:center; color:#facc15; font-size:1.5rem; margin-bottom:1rem">🏆 Kazanan: ${data.kazanan}</h3>
                    
                    <div class="karsilastir-grid">
                        <div class="card" style="margin-bottom: 0;">
                            <h4 style="color:#38bdf8; font-size:1.2rem; margin-bottom:1rem">${data.urun1.adi}</h4>
                            <div style="margin-bottom: 1rem;">
                                <p style="display:flex; justify-content:space-between; margin-bottom:0.5rem">
                                    <span>Memnuniyet:</span> <strong style="color:${m1Color}">%${m1}</strong>
                                </p>
                                <p style="display:flex; justify-content:space-between;">
                                    <span>Şikayet Oranı:</span> <strong style="color:${s1Color}">%${s1}</strong>
                                </p>
                            </div>
                            <h5 style="color:#a5f3fc; margin-bottom:0.5rem;">🌟 Avantajları</h5>
                            <ul style="margin-left: 1.5rem; color:#cbd5e1; font-size:0.9rem; line-height:1.5;">
                                ${av1.map(av => `<li>${av}</li>`).join('')}
                            </ul>
                        </div>
                        
                        <div class="card" style="margin-bottom: 0;">
                            <h4 style="color:#38bdf8; font-size:1.2rem; margin-bottom:1rem">${data.urun2.adi}</h4>
                            <div style="margin-bottom: 1rem;">
                                <p style="display:flex; justify-content:space-between; margin-bottom:0.5rem">
                                    <span>Memnuniyet:</span> <strong style="color:${m2Color}">%${m2}</strong>
                                </p>
                                <p style="display:flex; justify-content:space-between;">
                                    <span>Şikayet Oranı:</span> <strong style="color:${s2Color}">%${s2}</strong>
                                </p>
                            </div>
                            <h5 style="color:#a5f3fc; margin-bottom:0.5rem;">🌟 Avantajları</h5>
                            <ul style="margin-left: 1.5rem; color:#cbd5e1; font-size:0.9rem; line-height:1.5;">
                                ${av2.map(av => `<li>${av}</li>`).join('')}
                            </ul>
                        </div>
                    </div>
                    
                    <div class="solution-box" style="margin-top: 1.5rem;">
                        <span class="solution-icon">🧠</span>
                        <div class="solution-content">
                            <strong>Yapay Zeka Karşılaştırma Özeti:</strong>
                            <p>${ozet}</p>
                        </div>
                    </div>
                `;
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
            const yorumMetni = document.getElementById("ajan-yorumlar").value;
            const yorumlar = yorumMetni.split("\n").filter(l => l.trim().length > 0);

            if (!isValidInput(urunAdi).valid) {
                alert("Ürün adı geçersiz.");
                return;
            }
            if (yorumlar.length === 0) {
                alert("En az bir yorum girmelisiniz.");
                return;
            }

            const sonucDiv = document.getElementById("ajan-sonuc");
            sonucDiv.innerHTML = `<div class="loading"><div class="spinner"></div><p>⏳ Akıllı ajan çalışıyor...<br><small style="color:#9ca3af;font-size:0.85rem">(Yapay zeka yanıtı bekleniyor)</small></p></div>`;
            try {
                const data = await apiCall("/api/ajan", "POST", { urun_adi: urunAdi, yorumlar });
                let html = `
                    <div class="card" style="background: rgba(16, 185, 129, 0.1); border-color: rgba(16, 185, 129, 0.2);">
                        <h3 style="color: #10b981; margin-bottom: 0.5rem">🧠 Yönetici Özeti</h3>
                        <p style="color: #cbd5e1; line-height: 1.6;">${data.yonetici_ozeti}</p>
                    </div>
                    <div style="margin-top: 1rem;">
                        <h4 style="color: #facc15; margin-bottom: 0.5rem;">İyileştirme Önerileri:</h4>
                        <ul style="margin-left: 2rem; color: #cbd5e1;">${data.iyilestirmeler.map(i => `<li>${i}</li>`).join('')}</ul>
                    </div>
                    <div style="margin-top: 1rem;">
                        <h4 style="color: #60a5fa; margin-bottom: 0.5rem;">Aksiyonlar:</h4>
                        <ul style="margin-left: 2rem; color: #cbd5e1;">${data.aksiyonlar.map(a => `<li>${a}</li>`).join('')}</ul>
                    </div>`;
                sonucDiv.innerHTML = html;
            } catch (err) {
                sonucDiv.innerHTML = `<div class="error">❌ Hata: ${err.message}</div>`;
            }
        });
    }
});