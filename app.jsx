import React, { useState } from 'react';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, BarChart, Bar, XAxis, YAxis } from 'recharts';
import { Search, AlertTriangle, CheckCircle, Activity, LayoutDashboard, History, Settings, FileText, TrendingUp, Zap } from 'lucide-react';

export default function App() {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [showResults, setShowResults] = useState(false);

  // Gemini'den dönecek örnek veriler
  const duyguData = [
    { name: 'Pozitif', value: 54, color: '#10B981' },
    { name: 'Nötr', value: 38, color: '#9CA3AF' },
    { name: 'Kritik', value: 8, color: '#EF4444' }
  ];

  const trendData = [
    { name: 'Ocak', sikayet: 4 },
    { name: 'Şubat', sikayet: 7 },
    { name: 'Mart', sikayet: 3 },
    { name: 'Nisan', sikayet: 8 }
  ];

  const handleAnalyze = () => {
    setIsAnalyzing(true);
    setShowResults(false);
    setTimeout(() => {
      setIsAnalyzing(false);
      setShowResults(true);
    }, 2500);
  };

  return (
    <div className="flex h-screen bg-gray-50 font-sans text-gray-800 overflow-hidden">
      
      {/* 1. SOL MENÜ (SIDEBAR) */}
      <aside className="w-64 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-6 flex items-center gap-3">
          <div className="bg-blue-600 p-2 rounded-xl">
            <Activity className="text-white w-6 h-6" />
          </div>
          <h1 className="text-2xl font-black tracking-tight text-gray-900">Sinyal.</h1>
        </div>
        <nav className="flex-1 px-4 space-y-2 mt-4">
          <a href="#" className="flex items-center gap-3 px-4 py-3 bg-blue-50 text-blue-700 rounded-xl font-medium transition-colors">
            <LayoutDashboard className="w-5 h-5" /> Analiz Paneli
          </a>
          <a href="#" className="flex items-center gap-3 px-4 py-3 text-gray-600 hover:bg-gray-50 rounded-xl font-medium transition-colors">
            <History className="w-5 h-5" /> Geçmiş Taramalar
          </a>
          <a href="#" className="flex items-center gap-3 px-4 py-3 text-gray-600 hover:bg-gray-50 rounded-xl font-medium transition-colors">
            <FileText className="w-5 h-5" /> Raporlarım
          </a>
          <a href="#" className="flex items-center gap-3 px-4 py-3 text-gray-600 hover:bg-gray-50 rounded-xl font-medium transition-colors">
            <Settings className="w-5 h-5" /> Ayarlar
          </a>
        </nav>
      </aside>

      {/* 2. ANA İÇERİK ALANI */}
      <main className="flex-1 flex flex-col h-full overflow-y-auto">
        
        {/* Üst Arama Barı */}
        <header className="bg-white border-b border-gray-200 p-6 flex justify-between items-center sticky top-0 z-10">
          <div className="flex gap-4 w-full max-w-3xl">
            <div className="relative flex-1">
              <Search className="absolute left-4 top-3 text-gray-400 w-5 h-5" />
              <input 
                type="text" 
                placeholder="Trendyol, Hepsiburada ürün linkini yapıştırın..." 
                className="w-full pl-12 pr-4 py-3 bg-gray-50 rounded-xl border-transparent focus:bg-white focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition-all"
              />
            </div>
            <button 
              onClick={handleAnalyze}
              disabled={isAnalyzing}
              className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-8 rounded-xl transition-all shadow-lg shadow-blue-200 flex items-center gap-2 min-w-[160px] justify-center"
            >
              {isAnalyzing ? (
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              ) : (
                <><Zap className="w-4 h-4"/> Analiz Et</>
              )}
            </button>
          </div>
        </header>

        {/* Dashboard İçeriği */}
        <div className="p-8">
          
          {!showResults && !isAnalyzing && (
            <div className="h-full flex flex-col items-center justify-center text-gray-400 mt-20">
              <LayoutDashboard className="w-24 h-24 mb-6 opacity-20" />
              <h2 className="text-2xl font-medium text-gray-500">Analiz için bir ürün arayın</h2>
              <p className="mt-2">Yapay zeka binlerce yorumu saniyeler içinde okuyup özetleyecek.</p>
            </div>
          )}

          {showResults && (
            <div className="animate-fade-in-up space-y-6">
              
              {/* Özet Kartları (KPIs) */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm flex items-center gap-4">
                  <div className="p-4 bg-green-100 text-green-600 rounded-xl"><CheckCircle className="w-8 h-8"/></div>
                  <div>
                    <p className="text-gray-500 text-sm font-medium">Genel Memnuniyet</p>
                    <h3 className="text-2xl font-bold text-gray-900">%53.8</h3>
                  </div>
                </div>
                <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm flex items-center gap-4">
                  <div className="p-4 bg-red-100 text-red-600 rounded-xl"><AlertTriangle className="w-8 h-8"/></div>
                  <div>
                    <p className="text-gray-500 text-sm font-medium">Kronik Şikayet Oranı</p>
                    <h3 className="text-2xl font-bold text-gray-900">%7.7</h3>
                  </div>
                </div>
                <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm flex items-center gap-4">
                  <div className="p-4 bg-blue-100 text-blue-600 rounded-xl"><TrendingUp className="w-8 h-8"/></div>
                  <div>
                    <p className="text-gray-500 text-sm font-medium">Analiz Edilen Yorum</p>
                    <h3 className="text-2xl font-bold text-gray-900">154</h3>
                  </div>
                </div>
              </div>

              {/* Grafikler Alanı */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm">
                  <h3 className="font-bold text-lg mb-6">Yapay Zeka Duygu Dağılımı</h3>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie data={duyguData} innerRadius={70} outerRadius={100} paddingAngle={5} dataKey="value">
                          {duyguData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                          ))}
                        </Pie>
                        <Tooltip formatter={(value) => `%${value}`} />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm">
                  <h3 className="font-bold text-lg mb-6 text-red-600 flex items-center gap-2">
                    <AlertTriangle className="w-5 h-5"/> Tespit Edilen Kör Noktalar
                  </h3>
                  <div className="space-y-4">
                    <div className="p-4 bg-red-50 border border-red-100 rounded-xl">
                      <p className="text-red-800 font-medium mb-1">Aşırı Isınma ve Temassız Şarj Sorunu</p>
                      <p className="text-red-600 text-sm italic">"şarj olurken ısınıyor | fakat temassız şarj özelliğinde hızlı şarj yok"</p>
                    </div>
                    <div className="p-4 bg-gray-50 border border-gray-100 rounded-xl">
                      <p className="text-gray-800 font-medium mb-1">Batarya Ömrü Beklentisi</p>
                      <p className="text-gray-500 text-sm italic">Sistem, batarya ömrü ile ilgili genel olarak pozitif övgüler tespit etti. Kritik bir donanım sorunu bulunmamaktadır.</p>
                    </div>
                  </div>
                </div>
              </div>

            </div>
          )}
        </div>
      </main>
    </div>
  );
}