
import React, { useState, useCallback, useEffect } from 'react';
import { HashRouter, Routes, Route } from 'react-router-dom';
import { MOCK_STOCKS, MOCK_MARKET_SUMMARY } from './mockData';
import { TrackType, StockData, MentorInsight } from './types';
import { getMentorAnalysis } from './services/geminiService';
import Dashboard from './components/Dashboard';
import Screener from './components/Screener';
import Sidebar from './components/Sidebar';
import AccountView from './components/AccountView';
import SettingsView from './components/SettingsView';
import BasketView from './components/BasketView';

const App: React.FC = () => {
  const [stocks, setStocks] = useState<StockData[]>(MOCK_STOCKS);
  const [insight, setInsight] = useState<MentorInsight | null>(null);
  const [loading, setLoading] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [basket, setBasket] = useState<string[]>([]);

  // 실시간 데이터 페칭 추가
  useEffect(() => {
    const fetchStocks = async () => {
      try {
        const response = await fetch('/api/stocks');
        const data = await response.json();
        if (data && data.length > 0) {
          setStocks(data);
        }
      } catch (err) {
        console.error("Failed to fetch stocks from API", err);
      }
    };
    fetchStocks();
  }, []);

  // 장바구니 로드
  useEffect(() => {
    const savedBasket = localStorage.getItem('th_target_basket');
    if (savedBasket) setBasket(JSON.parse(savedBasket));
  }, []);

  // 장바구니 토글
  const toggleBasket = (symbol: string) => {
    setBasket(prev => {
      const newBasket = prev.includes(symbol) 
        ? prev.filter(s => s !== symbol) 
        : [...prev, symbol];
      localStorage.setItem('th_target_basket', JSON.stringify(newBasket));
      return newBasket;
    });
  };

  const fetchInsight = useCallback(async () => {
    if (loading) return;
    setLoading(true);
    try {
      const data = await getMentorAnalysis(stocks);
      setInsight(data);
    } catch (err) {
      console.error("Failed to fetch AI insights", err);
    } finally {
      setLoading(false);
    }
  }, [stocks, loading]);

  return (
    <HashRouter>
      <div className="flex min-h-screen bg-slate-950 text-slate-50 relative overflow-hidden">
        {isSidebarOpen && (
          <div 
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 md:hidden"
            onClick={() => setIsSidebarOpen(false)}
          ></div>
        )}

        <Sidebar isOpen={isSidebarOpen} onClose={() => setIsSidebarOpen(false)} basketCount={basket.length} />
        
        <main className="flex-1 p-4 lg:p-10 overflow-auto relative z-10">
          <header className="mb-8 flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div className="flex items-center gap-4">
              <button 
                onClick={() => setIsSidebarOpen(true)}
                className="p-2 bg-slate-900 border border-slate-800 rounded-lg md:hidden text-blue-500 shadow-lg shadow-blue-500/10"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </button>
              <div>
                <h1 className="text-2xl lg:text-3xl font-bold tracking-tight text-white flex items-center gap-3">
                  <span className="bg-blue-600 p-2 rounded-xl shadow-lg shadow-blue-600/30">🎯</span>
                  TrendHunter <span className="text-slate-500 font-normal text-sm lg:text-base">v2.1 PRO</span>
                </h1>
                <p className="text-slate-500 text-xs lg:text-sm mt-1">KIS API 연동 퀀트 엔진</p>
              </div>
            </div>
            
            <div className="flex items-center gap-4 lg:gap-6 bg-slate-900/40 p-3 lg:p-4 rounded-2xl border border-slate-800/50 backdrop-blur-md">
              <div className="text-right">
                <p className="text-xs text-slate-500 uppercase font-bold text-[10px] tracking-widest">TARGET BASKET</p>
                <p className="text-xs lg:text-sm font-mono text-emerald-400 font-bold">{basket.length}개 감시 중</p>
              </div>
              <div className="h-10 w-[1px] bg-slate-800/50"></div>
              <div className="text-right">
                <p className="text-xs text-slate-500 uppercase font-bold text-[10px] tracking-widest">MARKET RS</p>
                <p className="text-xs lg:text-sm font-bold text-green-400">{MOCK_MARKET_SUMMARY.marketRS}% 강세</p>
              </div>
            </div>
          </header>

          <Routes>
            <Route path="/" element={<Dashboard stocks={stocks} insight={insight} loading={loading} onRetry={fetchInsight} />} />
            <Route path="/account" element={<AccountView />} />
            <Route path="/basket" element={<BasketView stocks={stocks.filter(s => basket.includes(s.symbol))} onToggleBasket={toggleBasket} />} />
            <Route path="/settings" element={<SettingsView />} />
            <Route path="/track1" element={<Screener stocks={stocks.filter(s => s.track === TrackType.TRACK_1)} trackName={TrackType.TRACK_1} basket={basket} onToggleBasket={toggleBasket} />} />
            <Route path="/trackex" element={<Screener stocks={stocks.filter(s => s.track === TrackType.TRACK_EX)} trackName={TrackType.TRACK_EX} basket={basket} onToggleBasket={toggleBasket} />} />
            <Route path="/track2" element={<Screener stocks={stocks.filter(s => s.track === TrackType.TRACK_2)} trackName={TrackType.TRACK_2} basket={basket} onToggleBasket={toggleBasket} />} />
          </Routes>
        </main>
      </div>
    </HashRouter>
  );
};

export default App;
