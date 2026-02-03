import React, { useState, useEffect } from 'react';

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
  const [minRs, setMinRs] = useState(0);
  const [sortBy, setSortBy] = useState('rs_score');
  const [order, setOrder] = useState('desc');
  
  const fetchExplorerData = async () => {
    setLoading(true);
    try {
      const query = new URLSearchParams({
        page: page.toString(),
        limit: '20',
        sort_by: sortBy,
        order: order,
        search: search,
        min_rs: minRs.toString()
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
    // Debounce search
    const timer = setTimeout(() => {
      fetchExplorerData();
    }, 300);
    return () => clearTimeout(timer);
  }, [page, search, minRs, sortBy, order]);

  const handleSort = (field: string) => {
    if (sortBy === field) {
      setOrder(order === 'desc' ? 'asc' : 'desc');
    } else {
      setSortBy(field);
      setOrder('desc');
    }
  };

  const formatAmount = (amt: number) => {
    // 억 단위 변환
    const inUk = amt / 100000000;
    return inUk.toFixed(1) + '억';
  };

  return (
    <div className="space-y-6 animate-in fade-in pb-20">
      <div className="flex flex-col md:flex-row justify-between items-end gap-4 border-b border-slate-800 pb-6">
        <div>
          <h2 className="text-3xl font-bold text-white flex items-center gap-3">
            <span className="bg-indigo-600 p-2 rounded-xl shadow-lg shadow-indigo-900/40">🔭</span>
            Market Explorer
          </h2>
          <p className="text-slate-500 text-sm mt-1">
            전체 시장 데이터 원시 조회 (Raw Data) - {total.toLocaleString()} 종목
          </p>
        </div>
        
        <div className="flex gap-2">
           <input 
             type="text" 
             placeholder="종목명/코드 검색..." 
             className="bg-slate-900 border border-slate-700 rounded-xl px-4 py-2 text-sm text-white focus:outline-none focus:border-indigo-500 w-64"
             value={search}
             onChange={(e) => { setSearch(e.target.value); setPage(1); }}
           />
        </div>
      </div>

      <div className="bg-slate-900/50 border border-slate-800 rounded-3xl p-6">
        <div className="flex flex-wrap items-center gap-6 mb-6 text-sm">
           <div className="flex items-center gap-3">
             <span className="text-slate-500 font-bold">Min RS Score:</span>
             <input 
               type="range" 
               min="0" max="100" 
               value={minRs} 
               onChange={(e) => setMinRs(Number(e.target.value))}
               className="w-32 accent-indigo-500"
             />
             <span className="text-indigo-400 font-mono font-bold">{minRs}</span>
           </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead className="text-xs uppercase text-slate-500 font-bold border-b border-slate-800">
              <tr>
                <th className="px-4 py-3 cursor-pointer hover:text-indigo-400" onClick={() => handleSort('code')}>Symbol</th>
                <th className="px-4 py-3">Name</th>
                <th className="px-4 py-3 text-right cursor-pointer hover:text-indigo-400" onClick={() => handleSort('close')}>Price</th>
                <th className="px-4 py-3 text-right cursor-pointer hover:text-indigo-400" onClick={() => handleSort('rs_score')}>RS Score</th>
                <th className="px-4 py-3 text-right cursor-pointer hover:text-indigo-400" onClick={() => handleSort('amount')}>Volume(Amt)</th>
                <th className="px-4 py-3 text-right cursor-pointer hover:text-indigo-400" onClick={() => handleSort('market_cap')}>Market Cap</th>
                <th className="px-4 py-3 text-center">Market</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50 text-sm">
              {loading ? (
                <tr><td colSpan={7} className="text-center py-12 text-slate-500">Loading Market Data...</td></tr>
              ) : items.map((item) => (
                <tr key={item.code} className="hover:bg-slate-800/50 transition-colors">
                  <td className="px-4 py-3 font-mono text-slate-400">{item.code}</td>
                  <td className="px-4 py-3 font-bold text-slate-200">{item.name}</td>
                  <td className={`px-4 py-3 text-right font-mono font-bold ${item.change > 0 ? 'text-red-400' : item.change < 0 ? 'text-blue-400' : 'text-slate-400'}`}>
                    {item.close.toLocaleString()} 
                    <span className="text-[10px] ml-1 opacity-70">({item.change > 0 ? '+' : ''}{item.change}%)</span>
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-indigo-300">{item.rsScore.toFixed(0)}</td>
                  <td className="px-4 py-3 text-right text-slate-400">{formatAmount(item.amount)}</td>
                  <td className="px-4 py-3 text-right text-slate-500">{formatAmount(item.marketCap * 1000000)}</td>
                  <td className="px-4 py-3 text-center text-xs text-slate-600">{item.marketType}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="flex justify-center items-center gap-4 mt-6">
          <button 
            disabled={page === 1}
            onClick={() => setPage(p => p - 1)}
            className="px-4 py-2 bg-slate-800 rounded-lg text-slate-400 disabled:opacity-50 hover:bg-slate-700"
          >
            Prev
          </button>
          <span className="text-slate-500 font-mono">Page {page}</span>
          <button 
            disabled={items.length < 20}
            onClick={() => setPage(p => p + 1)}
            className="px-4 py-2 bg-slate-800 rounded-lg text-slate-400 disabled:opacity-50 hover:bg-slate-700"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
};

export default Explorer;
