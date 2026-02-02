
import React from 'react';
import { StockData } from '../types';

interface BasketViewProps {
  stocks: StockData[];
  onToggleBasket: (symbol: string) => void;
}

const BasketView: React.FC<BasketViewProps> = ({ stocks, onToggleBasket }) => {
  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-20">
      <div className="flex items-center justify-between border-b border-slate-800 pb-6">
        <div>
          <h2 className="text-3xl font-bold text-white tracking-tight flex items-center gap-3">
            <span className="bg-emerald-600 p-2 rounded-xl shadow-lg shadow-emerald-900/40">🛒</span>
            Target Basket
          </h2>
          <p className="text-slate-500 text-sm mt-1">시스템 트레이딩 실행 대상 종목군</p>
        </div>
        <div className="text-right">
          <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Active Watchlist</p>
          <p className="text-2xl font-bold text-emerald-400 font-mono">{stocks.length} 종목</p>
        </div>
      </div>

      {stocks.length === 0 ? (
        <div className="h-[400px] border-2 border-dashed border-slate-800 rounded-3xl flex flex-col items-center justify-center p-12 text-center text-slate-600">
          <span className="text-6xl mb-6 grayscale opacity-30">📦</span>
          <h3 className="text-lg font-bold text-slate-400 mb-2">장바구니가 비어있습니다</h3>
          <p className="text-sm max-w-xs leading-relaxed">
            트랙별 리더 종목 리스트에서 🛒 아이콘을 눌러<br/>
            시스템 트레이딩 대상을 추가하세요.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          {stocks.map(stock => (
            <div key={stock.symbol} className="bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-xl relative group overflow-hidden">
              <div className="absolute top-0 right-0 p-6 opacity-10 group-hover:opacity-20 transition-all pointer-events-none text-6xl">📈</div>
              <div className="flex justify-between items-start mb-6">
                <div>
                  <h4 className="text-xl font-bold text-white">{stock.name}</h4>
                  <p className="text-blue-500 font-mono text-xs">{stock.symbol} / {stock.sector}</p>
                </div>
                <button 
                  onClick={() => onToggleBasket(stock.symbol)}
                  className="p-2 text-slate-600 hover:text-red-500 transition-all"
                  title="장바구니에서 제거"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                </button>
              </div>

              <div className="space-y-4 mb-6">
                <div className="flex justify-between text-xs">
                  <span className="text-slate-500">상대강도(RS)</span>
                  <span className="text-blue-400 font-bold">{stock.rsScore} pt</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-slate-500">VCP 수축도</span>
                  <span className="text-emerald-400 font-bold">{(stock.vcpRatio * 100).toFixed(1)}%</span>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <div className="flex-1 px-4 py-2 bg-slate-800 rounded-xl flex items-center gap-2">
                  <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                  <span className="text-[10px] font-bold text-slate-300 uppercase">Monitoring</span>
                </div>
                <button className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-[10px] font-bold rounded-xl transition-all shadow-lg shadow-blue-900/20">
                  EXECUTE
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default BasketView;
