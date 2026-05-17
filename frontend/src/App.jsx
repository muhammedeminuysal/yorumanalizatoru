import React, { useState } from 'react';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts';
import { Search, AlertTriangle, CheckCircle, Activity, LayoutDashboard, History, Settings, FileText, TrendingUp, Zap ,Info} from 'lucide-react';

export default function App() {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [urunGirdisi, setUrunGirdisi] = useState("");
  
  const [duyguData, setDuyguData] = useState([]);
  const [korNoktalar, setKorNoktalar] = useState([]);
  const [ozetRapor, setOzetRapor] = useState({ memnuniyet: 0, sikayetOrani: 0, toplamYorum: 0, analizEdilenKriter: "",kaynakBilgisi: "" });

  const handleAnalyze = async () => {
    if (!urunGirdisi) return alert("Lütfen bir ürün adı veya linki girin!");
    setIsAnalyzing(true);
    setShowResults(false);

    try {
      const response = await fetch('http://127.0.0.1:5000/api/analiz', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ urun_linki: urunGirdisi })
      });
      const data = await response.json();

      if (!response.ok) return alert(data.hata);

      setOzetRapor({
        memnuniyet: data.genel_memnuniyet,
        sikayetOrani: data.kronik_sikayet_orani,
        toplamYorum: data.toplam_yorum,
        analizEdilenKriter: data.analiz_edilen_urun,
        kaynakBilgisi: data.kaynak_bilgisi
      });
      setDuyguData(data.duygu_dagilimi);
      setKorNoktalar(data.kor_noktalar);
      setShowResults(true);
    } catch (error) {
      alert("Sunucuya bağlanılamadı.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="flex h-screen bg-gray-50 font-sans text-gray-800 overflow-hidden">
      <aside className="w-64 bg-white border-r border-gray-200 flex flex-col hidden md:flex">
        <div className="p-6 flex items-center gap-3">
          <div className="bg-blue-600 p-2 rounded-xl"><Activity className="text-white w-6 h-6" /></div>
          <h1 className="text-2xl font-black tracking-tight text-gray-900">Sinyal.</h1>
        </div>
        <nav className="flex-1 px-4 space-y-2 mt-4">
          <a href="#" className="flex items-center gap-3 px-4 py-3 bg-blue-50 text-blue-700 rounded-xl font-medium"><LayoutDashboard className="w-5 h-5" /> Analiz Paneli</a>
        </nav>
      </aside>

      <main className="flex-1 flex flex-col h-full overflow-y-auto">
        <header className="bg-white border-b border-gray-200 p-6 flex justify-between items-center sticky top-0 z-10">
          <div className="flex gap-4 w-full max-w-4xl">
            <div className="relative flex-1">
              <Search className="absolute left-4 top-3 text-gray-400 w-5 h-5" />
              <input 
                type="text" 
                value={urunGirdisi}
                onChange={(e) => setUrunGirdisi(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleAnalyze()}
                placeholder="Örn: 'Dyson V15', 'Philips Airfryer' veya ürün linki yapıştırın..." 
                className="w-full pl-12 pr-4 py-3 bg-gray-50 rounded-xl border border-gray-200 focus:bg-white focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition-all font-medium"
              />
            </div>
            <button onClick={handleAnalyze} disabled={isAnalyzing} className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-8 rounded-xl transition-all shadow-lg shadow-blue-200 flex items-center gap-2 min-w-[160px] justify-center">
              {isAnalyzing ? <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div> : <><Zap className="w-4 h-4"/> Analiz Et</>}
            </button>
          </div>
        </header>
<div className="p-8">
          {!showResults && !isAnalyzing && (
            <div className="h-full flex flex-col items-center justify-center text-gray-400 mt-20">
              <LayoutDashboard className="w-24 h-24 mb-6 opacity-20" />
              <h2 className="text-2xl font-medium text-gray-500">Herhangi bir ürünü aratın</h2>
              <p className="mt-2 text-center max-w-md">Yapay zeka, internetteki binlerce müşteri deneyimini süzerek kronik sorunları anında bulsun.</p>
            </div>
          )}

          {showResults && (
            <div className="animate-fade-in-up space-y-6">
              <div className="mb-2">
                <h2 className="text-xl font-bold text-gray-800"><span className="text-blue-600 uppercase">{ozetRapor.analizEdilenKriter}</span> Analiz Raporu</h2>
                <p className="text-sm text-gray-500">İnternetteki müşteri deneyimleri yapay zeka ile süzülerek oluşturuldu.</p>
              </div>

              {/* KPI KARTLARI */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm flex items-center gap-4"><div className="p-4 bg-green-100 text-green-600 rounded-xl"><CheckCircle className="w-8 h-8"/></div><div><p className="text-gray-500 text-sm font-medium">Genel Memnuniyet</p><h3 className="text-2xl font-bold text-gray-900">%{ozetRapor.memnuniyet}</h3></div></div>
                <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm flex items-center gap-4"><div className="p-4 bg-red-100 text-red-600 rounded-xl"><AlertTriangle className="w-8 h-8"/></div><div><p className="text-gray-500 text-sm font-medium">Kronik Şikayet Oranı</p><h3 className="text-2xl font-bold text-gray-900">%{ozetRapor.sikayetOrani}</h3></div></div>
                <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm flex items-center gap-4"><div className="p-4 bg-blue-100 text-blue-600 rounded-xl"><TrendingUp className="w-8 h-8"/></div><div><p className="text-gray-500 text-sm font-medium">İncelenen Veri (Tahmini)</p><h3 className="text-2xl font-bold text-gray-900">{ozetRapor.toplamYorum}</h3></div></div>
              </div>

              {/* GRAFİK VE KÖR NOKTALAR */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm"><h3 className="font-bold text-lg mb-6 text-gray-800">Yapay Zeka Duygu Dağılımı</h3><div className="h-64"><ResponsiveContainer width="100%" height="100%"><PieChart><Pie data={duyguData} innerRadius={70} outerRadius={100} paddingAngle={5} dataKey="value">{duyguData.map((entry, index) => <Cell key={`cell-${index}`} fill={entry.color} />)}</Pie><Tooltip formatter={(value) => `%${value}`} /></PieChart></ResponsiveContainer></div></div>
                <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm"><h3 className="font-bold text-lg mb-6 text-red-600 flex items-center gap-2"><AlertTriangle className="w-5 h-5"/> Tespit Edilen Kör Noktalar</h3><div className="space-y-4">{korNoktalar.map((nokta, index) => <div key={index} className="p-4 bg-red-50 border border-red-100 rounded-xl"><p className="text-red-800 font-bold mb-1 text-sm uppercase">{nokta.baslik}</p><p className="text-red-600 text-sm italic">"{nokta.detay}"</p></div>)}</div></div>
              </div>

              {/* YENİ EKLENEN KISIM BURADAN BAŞLIYOR (KAYNAK BİLGİSİ) */}
              <div className="mt-8 bg-blue-50 border border-blue-100 rounded-2xl p-5 flex items-start gap-4">
                <div className="bg-blue-100 p-2 rounded-lg mt-1">
                  <Info className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                  <h4 className="text-blue-900 font-bold mb-1">Yapay Zeka Veri Kaynağı</h4>
                  <p className="text-blue-800 text-sm leading-relaxed">
                    {ozetRapor.kaynakBilgisi}
                  </p>
                </div>
              </div>
              {/* YENİ EKLENEN KISIM BURADA BİTİYOR */}

            </div>
          )}
        </div>
      </main>
    </div>
  );
}