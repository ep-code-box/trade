import React, { useState, useEffect } from 'react';
import { StockData } from '../types';
import StockDetailChart from './StockDetailChart';

interface ExplorerItem {
  code: string;
  name: string;
  close: number;
  change: number;
  amount: number;
  rsScore: number;
  marketType: string;
  marketCap: number;
  volume: number;
}

const Explorer: React.FC = () => {
  const [items, setItems] = useState<ExplorerItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  
  // [Screener Rules - Migrated from Settings]
  const [minRs, setMinRs] = useState(70);
  const [minLowDist, setMinLowDist] = useState(25); // 52주 저점 대비 상승 %
  const [maxHighDist, setMaxHighDist] = useState(25); // 52주 고점 대비 거리 %
  const [minAmount, setMinAmount] = useState(30); // 거래대금 (억)
  const [maxDisparity, setMaxDisparity] = useState(0); // 이격도 (0=OFF)
  const [alignment, setAlignment] = useState(true); // 정배열
  const [masterRules, setMasterRules] = useState(false); // [v5.8] 마스터 룰 스위치
  
  const [sortBy, setSortBy] = useState('rs_score');
  const [order, setOrder] = useState('desc');
  
  const [selectedStock, setSelectedStock] = useState<StockData | null>(null);
  const [basket, setBasket] = useState<string[]>([]);

  useEffect(() => {
    const saved = localStorage.getItem('th_target_basket');
    if (saved) setBasket(JSON.parse(saved));
  }, []);

  const toggleBasket = (symbol: string) => {
    const newBasket = basket.includes(symbol) ? basket.filter(s => s !== symbol) : [...basket, symbol];
    setBasket(newBasket);
    localStorage.setItem('th_target_basket', JSON.stringify(newBasket));
  };
  
  const fetchExplorerData = async () => {
    setLoading(true);
    try {
      const query = new URLSearchParams({
        page: page.toString(),
        limit: '20',
        sort_by: sortBy,
        order: order,
        search: search,
        min_rs: minRs.toString(),
        min_amount: (minAmount * 100).toString(),
        max_disparity: maxDisparity.toString(),
        strict_alignment: alignment.toString(),
        min_low_dist: minLowDist.toString(),
        max_high_dist: maxHighDist.toString(),
        master_rules: masterRules.toString()
      });
      
      const res = await fetch(`/api/explore?${query.toString()}`);
      const data = await res.json();
      
      if (data.items) {
        setItems(data.items);
        setTotal(data.total);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      fetchExplorerData();
    }, 300);
    return () => clearTimeout(timer);
  }, [page, search, minRs, minLowDist, maxHighDist, minAmount, maxDisparity, alignment, masterRules, sortBy, order]);

  const handleSort = (field: string) => {
    if (sortBy === field) {
      setOrder(order === 'desc' ? 'asc' : 'desc');
    } else {
      setSortBy(field);
      setOrder('desc');
    }
  };

  const handleRowClick = (item: ExplorerItem) => {
    const stockData: StockData = {
      symbol: item.code,
      name: item.name,
      price: item.close,
      change: item.change,
      rsScore: item.rsScore,
      sector: item.marketType,
      volumeDryUp: false,
      isStage2: true, 
      vcpRatio: 0,
      track: "Explorer",
      dividendYield: 0,
      roe: 0,
      opMargin: 0,
      targetPrice: 0,
      stopLossPrice: 0,
      rationale: [],
      weight: "",
      atr: 0,
      volatility: 0,
      template: {
        priceAbove50: false, priceAbove150_200: false, sma150Above200: false, 
        sma50Above150_200: false, sma200TrendingUp: false, above52wLow25: false, 
        within52wHigh25: false, rsAbove70: false
      }
    };
    setSelectedStock(stockData);
  };

  const formatAmount = (amt: number) => {
    const inUk = amt / 100000000;
    return inUk.toFixed(1) + '억';
  };

  const resetFilters = () => {
    setMinRs(70);
    setMinLowDist(25);
    setMaxHighDist(25);
    setMinAmount(30);
    setMaxDisparity(0);
    setAlignment(true);
    setMasterRules(false);
    setSearch('');
  };

  return (
    <div className="space-y-8 animate-in fade-in pb-20">
      <div className="flex flex-col md:flex-row justify-between items-end gap-4 border-b border-slate-800 pb-6">
        <div>
          <h2 className="text-3xl font-bold text-white flex items-center gap-3">
            <span className="bg-indigo-600 p-2 rounded-xl shadow-lg shadow-indigo-900/40">🔭</span>
            Interactive Custom Screener
          </h2>
          <p className="text-slate-500 text-sm mt-1">
            설정된 퀀트 필터를 실시간으로 조절하며 시장 전체를 탐색하세요.
          </p>
        </div>
        
        <div className="flex gap-4">
           {/* [MASTER RULES TOGGLE] */}
           <div className={`flex items-center gap-3 border px-4 py-2 rounded-xl shadow-lg transition-all ${masterRules ? 'bg-indigo-600/10 border-indigo-500/50' : 'bg-slate-900 border-slate-800'}`}>
              <span className={`text-[10px] font-bold uppercase tracking-widest ${masterRules ? 'text-indigo-400' : 'text-slate-600'}`}>Master Rules</span>
              <button 
                onClick={() => setMasterRules(!masterRules)}
                className={`w-10 h-5 rounded-full p-1 transition-all ${masterRules ? 'bg-indigo-600' : 'bg-slate-800'}`}
              >
                <div className={`w-3 h-3 bg-white rounded-full transition-all ${masterRules ? 'translate-x-5' : 'translate-x-0'}`}></div>
              </button>
           </div>

           <input 
             type="text" 
             placeholder="종목명/코드 검색..." 
             className="bg-slate-900 border border-slate-700 rounded-xl px-4 py-2 text-sm text-white focus:outline-none focus:border-indigo-500 w-64 shadow-inner"
             value={search}
             onChange={(e) => { setSearch(e.target.value); setPage(1); }}
           />
        </div>
      </div>

      {/* [Screener Logic Panel] */}
      <div className="bg-slate-900 border border-slate-800 rounded-3xl p-8 shadow-2xl relative overflow-hidden">
        <div className="absolute top-0 right-0 p-8 opacity-5 pointer-events-none text-8xl font-bold text-white">ENGINE</div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-10">
          <div className="space-y-6">
            <h4 className="text-[11px] font-bold text-blue-500 uppercase tracking-widest border-b border-slate-800 pb-2">Trend Template</h4>
            <RangeInput label="최소 RS 점수 (Rel. Strength)" value={minRs} min={0} max={99} step={5} onChange={setMinRs} />
            <RangeInput label="52주 저점 대비 최소 상승" value={minLowDist} min={0} max={100} step={5} onChange={setMinLowDist} />
            <RangeInput label="52주 고점 대비 최대 거리" value={maxHighDist} min={0} max={50} step={5} onChange={setMaxHighDist} />
          </div>

          <div className="space-y-6">
            <h4 className="text-[11px] font-bold text-emerald-500 uppercase tracking-widest border-b border-slate-800 pb-2">Liquidity & Stability</h4>
            <RangeInput label="최소 거래대금 (억)" value={minAmount} min={0} max={1000} step={10} onChange={setMinAmount} suffix="억" />
            <RangeInput label="최대 이격도 (200MA)" value={maxDisparity} min={0} max={100} step={5} onChange={setMaxDisparity} suffix={maxDisparity === 0 ? "OFF" : "%"} />
            
            <div className="flex items-center justify-between p-4 bg-slate-800/40 rounded-2xl border border-slate-700/50">
              <div>
                <p className="text-xs font-bold text-slate-300">SMA 정배열 강제</p>
                <p className="text-[10px] text-slate-500 mt-1">20 &gt; 50 &gt; 200일선 유지 필수</p>
              </div>
              <button 
                onClick={() => setAlignment(!alignment)}
                className={`w-12 h-6 rounded-full p-1 transition-all ${alignment ? 'bg-blue-600' : 'bg-slate-700'}`}
              >
                <div className={`w-4 h-4 bg-white rounded-full transition-all ${alignment ? 'translate-x-6' : 'translate-x-0'}`}></div>
              </button>
            </div>
          </div>

          <div className="bg-slate-800/20 border border-dashed border-slate-700 rounded-3xl p-6 flex flex-col justify-center items-center text-center">
             <span className="text-4xl mb-3">{total > 0 ? '💎' : '💤'}</span>
             <h4 className="text-white font-bold text-2xl mb-1 font-mono">{total.toLocaleString()}</h4>
             <p className="text-slate-500 text-[10px] uppercase font-bold tracking-widest">Candidates Found</p>
             <div className="mt-6 flex flex-col gap-3">
                <p className="text-[9px] text-slate-600 leading-tight">
                  {masterRules ? 'Master Rules Active: VDU, 150MA, 200MA Slope, Profitability 필터링 중' : '기본 필터 적용 중'}
                </p>
                <button 
                  onClick={resetFilters}
                  className="text-[10px] text-blue-400 font-bold uppercase hover:underline"
                >
                  Reset to Default
                </button>
             </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-5 gap-8">
        <div className={`xl:col-span-${selectedStock ? '3' : '5'} space-y-6`}>
          <div className="bg-slate-900 border border-slate-800 rounded-3xl overflow-hidden shadow-2xl">
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead className="bg-slate-800/30 text-slate-500 text-[10px] font-bold uppercase tracking-widest border-b border-slate-800">
                  <tr>
                    <th className="px-6 py-4 cursor-pointer hover:text-indigo-400" onClick={() => handleSort('code')}>Symbol</th>
                    <th className="px-6 py-4">Name</th>
                    <th className="px-6 py-4 text-right cursor-pointer hover:text-indigo-400" onClick={() => handleSort('close')}>Price</th>
                    <th className="px-6 py-4 text-right cursor-pointer hover:text-indigo-400" onClick={() => handleSort('rs_score')}>RS</th>
                    <th className="px-6 py-4 text-right cursor-pointer hover:text-indigo-400" onClick={() => handleSort('amount')}>Amt</th>
                    <th className="px-6 py-4 text-center">Market</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/50">
                  {loading ? (
                    <tr><td colSpan={6} className="text-center py-20 text-slate-500 font-mono animate-pulse uppercase tracking-widest text-[10px]">Scanning entire market...</td></tr>
                  ) : items.length === 0 ? (
                    <tr><td colSpan={6} className="text-center py-20 text-slate-600">No stocks match your criteria.</td></tr>
                  ) : items.map((item) => (
                    <tr 
                      key={item.code} 
                      className={`transition-all cursor-pointer ${selectedStock?.symbol === item.code ? 'bg-blue-600/10' : 'hover:bg-slate-800/40'}`} 
                      onClick={() => handleRowClick(item)}
                    >
                      <td className="px-6 py-4 font-mono text-slate-400 text-xs">{item.code}</td>
                      <td className="px-6 py-4 font-bold text-slate-200">{item.name}</td>
                      <td className={`px-6 py-4 text-right font-mono font-bold ${item.change > 0 ? 'text-red-400' : item.change < 0 ? 'text-blue-400' : 'text-slate-400'}`}>
                        {item.close.toLocaleString()} 
                        <span className="text-[10px] ml-1 opacity-70">({item.change > 0 ? '+' : ''}{item.change}%)</span>
                      </td>
                      <td className="px-6 py-4 text-right font-mono text-indigo-300 font-bold">{item.rsScore.toFixed(0)}</td>
                      <td className="px-6 py-4 text-right text-slate-400 text-xs">{formatAmount(item.amount)}</td>
                      <td className="px-6 py-4 text-center">
                        <span className="text-[9px] font-bold px-2 py-0.5 rounded bg-slate-800 text-slate-500 border border-slate-700">{item.marketType}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="flex justify-center items-center gap-6 py-6 border-t border-slate-800 bg-slate-800/10">
              <button 
                disabled={page === 1}
                onClick={() => setPage(p => p - 1)}
                className="px-4 py-2 bg-slate-800 rounded-xl text-slate-400 disabled:opacity-30 hover:bg-slate-700 transition-all font-bold text-xs"
              >
                PREV
              </button>
              <span className="text-slate-500 font-mono text-xs font-bold uppercase tracking-widest">Page {page}</span>
              <button 
                disabled={items.length < 20}
                onClick={() => setPage(p => p + 1)}
                className="px-4 py-2 bg-slate-800 rounded-xl text-slate-400 disabled:opacity-30 hover:bg-slate-700 transition-all font-bold text-xs"
              >
                NEXT
              </button>
            </div>
          </div>
        </div>

        {selectedStock && (
          <div className="xl:col-span-2 animate-in slide-in-from-right-4 duration-300">
            <div className="sticky top-10">
              <StockDetailChart 
                stock={selectedStock} 
                isInBasket={basket.includes(selectedStock.symbol)}
                onToggleBasket={() => toggleBasket(selectedStock.symbol)}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

const RangeInput = ({ label, value, min, max, step, onChange, suffix = "%" }: { label: string, value: number, min: number, max: number, step: number, onChange: (v: number) => void, suffix?: string }) => (
  <div className="space-y-3">
    <div className="flex justify-between items-center">
      <span className="text-[11px] font-bold text-slate-400 uppercase tracking-tighter">{label}</span>
      <span className="text-xs font-mono text-blue-400 font-bold">{value}{suffix === '%' ? '%' : ` ${suffix}`}</span>
    </div>
    <input 
      type="range" min={min} max={max} step={step} value={value} 
      onChange={e => onChange(parseInt(e.target.value))}
      className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-blue-600 shadow-inner"
    />
  </div>
);

export default Explorer;
