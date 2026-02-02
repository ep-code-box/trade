
import React from 'react';
import { ComposedChart, Line, XAxis, YAxis, CartesianGrid, ResponsiveContainer, ReferenceLine } from 'recharts';
import { StockData } from '../types';
import { MOCK_ACCOUNT } from '../mockData';

interface StockDetailChartProps {
  stock: StockData;
  isInBasket?: boolean;
  onToggleBasket?: () => void;
}

const StockDetailChart: React.FC<StockDetailChartProps> = ({ stock, isInBasket, onToggleBasket }) => {
  const chartData = Array.from({ length: 20 }, (_, i) => ({
    name: `T-${19-i}`,
    price: stock.price * (0.95 + Math.random() * 0.1),
    volume: 1000 + Math.random() * 2000
  }));
  
  const maxLossAmount = MOCK_ACCOUNT.depositSeed * (MOCK_ACCOUNT.riskPerTradePercent / 100);
  const riskPerShare = stock.price - stock.stopLossPrice;
  const recommendedQty = riskPerShare > 0 ? Math.floor(maxLossAmount / riskPerShare) : 0;
  
  const isStopTooTight = riskPerShare < (stock.atr * 1.5);
  
  const currentSectorRisk = MOCK_ACCOUNT.positions
    .filter(p => p.sector === stock.sector)
    .reduce((acc, p) => acc + (p.avgPrice - p.initialStopLoss) * p.quantity, 0);
  
  const isSectorFull = (currentSectorRisk / MOCK_ACCOUNT.depositSeed) * 100 >= MOCK_ACCOUNT.maxSectorExposure;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 h-full flex flex-col gap-6 overflow-y-auto max-h-[calc(100vh-160px)] custom-scrollbar">
      <div className="flex justify-between items-start">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h4 className="text-2xl font-bold text-white">{stock.name}</h4>
            {isInBasket && (
              <span className="bg-emerald-500/10 text-emerald-500 text-[10px] font-bold px-1.5 py-0.5 rounded border border-emerald-500/20">TARGETING</span>
            )}
          </div>
          <div className="flex gap-4 text-xs font-mono">
            <span className="text-emerald-400">TARGET: ₩{stock.targetPrice.toLocaleString()}</span>
            <span className="text-red-500">STOP: ₩{stock.stopLossPrice.toLocaleString()}</span>
          </div>
        </div>
        <div className="text-right">
          <p className="text-[10px] font-bold text-slate-500 uppercase">Daily Vol (ATR)</p>
          <p className="text-xl font-bold text-orange-400 font-mono">₩{stock.atr.toLocaleString()}</p>
        </div>
      </div>

      <div className="flex-1 min-h-[180px] shrink-0 border-b border-slate-800 pb-4">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
            <XAxis dataKey="name" hide />
            <YAxis domain={['auto', 'auto']} stroke="#475569" fontSize={10} axisLine={false} tickLine={false} />
            <ReferenceLine y={stock.stopLossPrice} stroke="#ef4444" strokeDasharray="5 5" label={{ position: 'right', value: 'STOP', fill: '#ef4444', fontSize: 10 }} />
            <Line type="monotone" dataKey="price" stroke="#3b82f6" strokeWidth={2} dot={false} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      <div className="space-y-3">
        {isStopTooTight && (
          <div className="p-3 bg-orange-500/10 border border-orange-500/20 rounded-xl flex items-center gap-3">
            <span className="text-orange-500 text-xs">⚠️</span>
            <p className="text-[10px] text-orange-200 font-medium">손절폭 협소 경고 (ATR Noise)</p>
          </div>
        )}
        {!isInBasket && (
          <div className="p-3 bg-blue-500/10 border border-blue-500/20 rounded-xl flex items-center gap-3">
            <span className="text-blue-500 text-xs">🛒</span>
            <p className="text-[10px] text-blue-200 font-medium italic">시스템 트레이딩을 위해 장바구니에 먼저 담아주세요.</p>
          </div>
        )}
      </div>

      <div className="bg-slate-800/40 border border-slate-700 rounded-2xl p-5 space-y-4">
        <div className="flex justify-between items-end">
          <div>
            <p className="text-[9px] text-slate-500 font-bold uppercase mb-1">Recommended Qty</p>
            <h3 className="text-2xl font-mono font-bold text-white">{recommendedQty.toLocaleString()} <span className="text-xs text-slate-500">주</span></h3>
          </div>
          <button 
            onClick={onToggleBasket}
            className={`px-4 py-2 rounded-lg text-[10px] font-bold transition-all border ${isInBasket ? 'bg-slate-800 border-slate-700 text-slate-500' : 'bg-blue-600/20 border-blue-500/40 text-blue-400'}`}
          >
            {isInBasket ? 'BASKET OUT' : 'ADD TO BASKET'}
          </button>
        </div>
        
        <button 
          disabled={!isInBasket || isSectorFull}
          className={`w-full py-4 rounded-xl font-bold text-sm transition-all shadow-xl active:scale-[0.98] ${
            !isInBasket 
              ? 'bg-slate-800 text-slate-600 cursor-not-allowed border border-slate-700' 
              : isSectorFull 
                ? 'bg-red-500/10 text-red-500 border border-red-500/20 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-500 text-white shadow-blue-900/40'
          }`}
        >
          {!isInBasket ? 'ADD TO BASKET FIRST' : isSectorFull ? 'SECTOR LIMIT REACHED' : 'SYSTEM TRADE START'}
        </button>
      </div>
    </div>
  );
};

export default StockDetailChart;
