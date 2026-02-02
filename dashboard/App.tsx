
import React, { useState, useCallback, useEffect } from 'react';
import { HashRouter, Routes, Route } from 'react-router-dom';
import { TrackType, StockData, MentorInsight, MarketSummary } from './types';
import { getMentorAnalysis } from './services/geminiService';
import Dashboard from './components/Dashboard';
import Screener from './components/Screener';
import Sidebar from './components/Sidebar';
import AccountView from './components/AccountView';
import SettingsView from './components/SettingsView';
import BasketView from './components/BasketView';

const App: React.FC = () => {
  const [stocks, setStocks] = useState<StockData[]>([]);
  const [summary, setSummary] = useState<MarketSummary>({
    totalStocks: 3800, marketRS: 0, activeLeaders: 0, stage2Ratio: 0, lastSync: ''
  });
  const [insight, setInsight] = useState<MentorInsight | null>(null);
  const [loading, setLoading] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [basket, setBasket] = useState<string[]>([]);
  const [fetchError, setFetchError] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      const sRes = await fetch('/api/stocks');
      if (!sRes.ok) throw new Error(`Stocks API: ${sRes.status}`);
      const sData = await sRes.json();
      setStocks(sData || []);

      const sumRes = await fetch('/api/summary');
      if (!sumRes.ok) throw new Error(`Summary API: ${sumRes.status}`);
      const sumData = await sumRes.json();
      if (sumData) {
        setSummary({
          totalStocks: 3800,
          marketRS: sumData.marketRS || 0,
          activeLeaders: sumData.activeLeaders || 0,
          stage2Ratio: sumData.stage2Ratio || 0,
          lastSync: sumData.lastSync || '',
          topSector: sumData.topSector,
          riskLevel: sumData.riskLevel
        });
      }
      
      setFetchError(null);
    } catch (err: any) {
      console.error("Fetch Error:", err);
      setFetchError(err.message);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    const savedBasket = localStorage.getItem('th_target_basket');
    if (savedBasket) setBasket(JSON.parse(savedBasket));
  }, []);

  const toggleBasket = (symbol: string) => {
    setBasket(prev => {
      const newBasket = prev.includes(symbol) ? prev.filter(s => s !== symbol) : [...prev, symbol];
      localStorage.setItem('th_target_basket', JSON.stringify(newBasket));
      return newBasket;
    });
  };

  return (
    <HashRouter>
      <div className="flex min-h-screen bg-slate-950 text-slate-50 relative overflow-hidden">
        <Sidebar isOpen={isSidebarOpen} onClose={() => setIsSidebarOpen(false)} basketCount={basket.length} />
        
        <main className="flex-1 p-4 lg:p-10 overflow-auto relative z-10">
          {fetchError && (
            <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-xl text-red-500 text-[10px] font-mono flex justify-between items-center animate-pulse">
              <span>⚠️ API CONNECTION ERROR: {fetchError}</span>
              <button onClick={fetchData} className="px-3 py-1 bg-red-500 text-white rounded-lg font-bold">RETRY</button>
            </div>
          )}
          
          <header className="mb-8 flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div className="flex items-center gap-4">
              <button onClick={() => setIsSidebarOpen(true)} className="md:hidden p-2 bg-slate-900 border border-slate-800 rounded-lg text-blue-500">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" /></svg>
              </button>
              <div>
                <h1 className="text-2xl lg:text-3xl font-bold tracking-tight text-white flex items-center gap-3">
                  <span className="bg-blue-600 p-2 rounded-xl shadow-lg shadow-blue-600/30">🎯</span>
                  TrendHunter <span className="text-slate-500 font-normal text-sm lg:text-base italic">v3.9 PRO</span>
                </h1>
                <p className="text-slate-500 text-[10px] lg:text-xs mt-1 font-mono uppercase tracking-widest">
                  Status: {stocks.length > 0 ? 'CONNECTED' : 'STANDBY'} | API: 8000
                </p>
              </div>
            </div>
            
            <div className="flex items-center gap-4 lg:gap-6 bg-slate-900/40 p-3 lg:p-4 rounded-2xl border border-slate-800/50 backdrop-blur-md">
              <div className="text-right">
                <p className="text-[10px] text-slate-500 uppercase font-bold tracking-widest">BASKET</p>
                <p className="text-xs lg:text-sm font-mono text-emerald-400 font-bold">{basket.length} Stocks</p>
              </div>
              <div className="h-10 w-[1px] bg-slate-800/50"></div>
              <div className="text-right">
                <p className="text-[10px] text-slate-500 uppercase font-bold tracking-widest">MARKET RS</p>
                <p className="text-xs lg:text-sm font-bold text-green-400">{summary.marketRS} Alpha</p>
              </div>
            </div>
          </header>

          <Routes>
            <Route path="/" element={<Dashboard stocks={stocks} summary={summary} insight={insight} loading={loading} onRetry={() => {}} />} />
            <Route path="/account" element={<AccountView />} />
            <Route path="/basket" element={<BasketView stocks={stocks.filter(s => basket.includes(s.symbol))} onToggleBasket={toggleBasket} />} />
            <Route path="/settings" element={<SettingsView />} />
            <Route path="/track1" element={<Screener stocks={stocks.filter(s => s.track?.startsWith('트랙 1'))} trackName={TrackType.TRACK_1} basket={basket} onToggleBasket={toggleBasket} />} />
            <Route path="/trackex" element={<Screener stocks={stocks.filter(s => s.track?.startsWith('트랙 EX'))} trackName={TrackType.TRACK_EX} basket={basket} onToggleBasket={toggleBasket} />} />
            <Route path="/track2" element={<Screener stocks={stocks.filter(s => s.track?.startsWith('트랙 2'))} trackName={TrackType.TRACK_2} basket={basket} onToggleBasket={toggleBasket} />} />
          </Routes>
        </main>
      </div>
    </HashRouter>
  );
};

export default App;
