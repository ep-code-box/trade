
import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, ResponsiveContainer, ReferenceLine, Tooltip, Legend } from 'recharts';
import { StockData } from '../types';

interface StockDetailChartProps {
  stock: StockData;
  isInBasket?: boolean;
  onToggleBasket?: () => void;
}

const FundamentalCard = ({ label, value, sub }: { label: string, value: string, sub?: string }) => (
  <div className="bg-slate-800/50 border border-slate-700/50 p-4 rounded-2xl">
    <p className="text-[9px] font-bold text-slate-500 uppercase tracking-wider mb-1">{label}</p>
    <h4 className="text-lg font-mono font-bold text-white">{value}</h4>
    {sub && <p className="text-[9px] text-slate-400 mt-1">{sub}</p>}
  </div>
);

const StockDetailChart: React.FC<StockDetailChartProps> = ({ stock, isInBasket, onToggleBasket }) => {
  const [chartData, setChartData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  
  const isDividendTrack = stock.track?.includes('뚜벅이') || stock.track?.includes('TRACK 2');

  useEffect(() => {
    const fetchHistory = async () => {
      setLoading(true);
      try {
        const response = await fetch(`/api/stocks/${stock.symbol}/history`);
        const data = await response.json();
        console.log(`Rendering Chart for ${stock.name}:`, data?.length, "points");
        if (data && data.length > 0) {
          const formatted = data.map((d: any) => ({
            ...d,
            name: `${d.date.substring(4,6)}/${d.date.substring(6,8)}`,
            price: Number(d.close),
            sma50: d.sma_50 && d.sma_50 > 0 ? Number(d.sma_50) : null,
            sma150: d.sma_150 && d.sma_150 > 0 ? Number(d.sma_150) : null,
            sma200: d.sma_200 && d.sma_200 > 0 ? Number(d.sma_200) : null
          }));
          setChartData(formatted);
        }
      } catch (err) {
        console.error("History API Error", err);
      } finally {
        setLoading(false);
      }
    };
    fetchHistory();
  }, [stock.symbol]);
  
  const stopLoss = stock.stopLossPrice || stock.price * 0.93;
  const targetPrice = stock.targetPrice || stock.price * 1.2;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 h-full flex flex-col gap-6 overflow-y-auto max-h-[calc(100vh-160px)] custom-scrollbar">
      {/* Header Section */}
      <div className="flex justify-between items-start">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h4 className="text-2xl font-bold text-white">{stock.name}</h4>
            <span className="bg-slate-800 text-slate-400 font-mono text-[10px] px-2 py-0.5 rounded border border-slate-700">{stock.symbol}</span>
          </div>
          <p className="text-[10px] font-bold text-blue-500 uppercase tracking-widest mb-2">{stock.track}</p>
          <div className="flex gap-4">
            {isDividendTrack ? (
              <><div className="flex flex-col"><span className="text-[9px] text-slate-500 font-bold uppercase">Yield</span><span className="text-emerald-400 font-bold font-mono text-lg">{(stock.dividendYield || 0).toFixed(1)}%</span></div>
                <div className="flex flex-col ml-4"><span className="text-[9px] text-slate-500 font-bold uppercase">ROE</span><span className="text-blue-400 font-bold font-mono text-lg">{(stock.roe || 0).toFixed(1)}%</span></div></>
            ) : (
              <><div className="flex flex-col"><span className="text-[9px] text-slate-500 font-bold uppercase">Pivot</span><span className="text-emerald-400 font-bold font-mono text-lg">₩{targetPrice.toLocaleString()}</span></div>
                <div className="flex flex-col ml-4"><span className="text-[9px] text-slate-500 font-bold uppercase">Stop</span><span className="text-red-500 font-bold font-mono text-lg">₩{stopLoss.toLocaleString()}</span></div></>
            )}
          </div>
        </div>
        <div className="text-right">
          <p className="text-[10px] font-bold text-slate-500 uppercase">Current Price</p>
          <p className="text-2xl font-bold text-white font-mono">₩{stock.price.toLocaleString()}</p>
          <p className={`text-xs font-bold ${stock.change >= 0 ? 'text-green-500' : 'text-red-500'}`}>{stock.change >= 0 ? '▲' : '▼'} {Math.abs(stock.change)}%</p>
        </div>
      </div>

      {/* Chart Area */}
      <div className="flex-1 min-h-[300px] shrink-0 border-b border-slate-800 pb-4 relative overflow-hidden">
        {loading ? (
          <div className="absolute inset-0 flex items-center justify-center text-slate-500 text-xs font-bold animate-pulse">데이터 로딩 중...</div>
        ) : isDividendTrack ? (
          <div className="grid grid-cols-2 gap-4 h-full animate-in fade-in duration-500">
            <FundamentalCard label="Op Margin" value={`${(stock.opMargin || 0).toFixed(1)}%`} sub="영업 효율성" />
            <FundamentalCard label="Dividend" value="STABLE" sub="배당 지속성" />
            <div className="col-span-2 bg-slate-800/30 border border-slate-700/50 p-4 rounded-2xl">
               <ResponsiveContainer width="100%" height={120}>
                  <LineChart data={chartData}>
                    <Line type="monotone" dataKey="price" stroke="#3b82f6" strokeWidth={2} dot={false} isAnimationActive={false} />
                    <YAxis hide domain={['auto', 'auto']} />
                  </LineChart>
               </ResponsiveContainer>
            </div>
          </div>
        ) : (
          /* ResponsiveContainer를 쓰되 높이를 명시적으로 부여 (사파리 호환성) */
          <div style={{ width: '100%', height: '300px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} opacity={0.5} />
                <XAxis dataKey="name" stroke="#475569" fontSize={8} tickLine={false} axisLine={false} interval={Math.floor(chartData.length / 6)} />
                <YAxis domain={[(dataMin: number) => dataMin * 0.97, (dataMax: number) => Math.max(dataMax, targetPrice) * 1.03]} stroke="#475569" fontSize={10} axisLine={false} tickLine={false} tickFormatter={(val) => val.toLocaleString()} />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '12px', fontSize: '10px' }} />
                <Legend verticalAlign="top" align="right" height={36} iconType="circle" wrapperStyle={{ fontSize: '10px', fontWeight: 'bold' }} />
                
                <ReferenceLine y={stopLoss} stroke="#ef4444" strokeDasharray="5 5" label={{ position: 'right', value: 'STOP', fill: '#ef4444', fontSize: 10 }} />
                <ReferenceLine y={targetPrice} stroke="#10b981" strokeDasharray="3 3" label={{ position: 'right', value: 'PIVOT', fill: '#10b981', fontSize: 10 }} />

                <Line name="Price" type="monotone" dataKey="price" stroke="#ffffff" strokeWidth={2.5} dot={false} isAnimationActive={false} connectNulls />
                <Line name="SMA 50" type="monotone" dataKey="sma50" stroke="#fbbf24" strokeWidth={2} dot={false} connectNulls />
                <Line name="SMA 150" type="monotone" dataKey="sma150" stroke="#34d399" strokeWidth={2} dot={false} connectNulls />
                <Line name="SMA 200" type="monotone" dataKey="sma200" stroke="#a78bfa" strokeWidth={2} dot={false} connectNulls />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      <div className="bg-slate-800/40 border border-slate-700 rounded-2xl p-5 mt-auto">
          <div className="flex items-center gap-4">
             <div className="flex flex-col text-right">
                <span className="text-[10px] text-slate-500 uppercase font-bold">Action</span>
                <span className="text-xs text-white">Review & Confirm</span>
             </div>
             <button onClick={onToggleBasket} className={`px-6 py-3 rounded-xl text-xs font-bold transition-all border shadow-lg ${isInBasket ? 'bg-slate-800 border-slate-700 text-slate-500' : 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-emerald-900/40 border-transparent'}`}>
                {isInBasket ? 'REVOKE APPROVAL' : 'CONFIRM TARGET'}
             </button>
          </div>
      </div>
    </div>
  );
};

export default StockDetailChart;
