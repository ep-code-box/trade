
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
            <span className="bg-emerald-600 p-2 rounded-xl shadow-lg shadow-emerald-900/40">✅</span>
            Ready for Trading
          </h2>
          <p className="text-slate-500 text-sm mt-1">알고리즘 선정 후 트레이더 승인 완료 (매매 대기)</p>
        </div>
        <div className="text-right">
          <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Standing By</p>
          <p className="text-2xl font-bold text-emerald-400 font-mono">{stocks.length} 종목</p>
        </div>
      </div>

      {stocks.length === 0 ? (
        <div className="h-[400px] border-2 border-dashed border-slate-800 rounded-3xl flex flex-col items-center justify-center p-12 text-center text-slate-600">
          <span className="text-6xl mb-6 grayscale opacity-30">🛡️</span>
          <h3 className="text-lg font-bold text-slate-400 mb-2">대기 중인 종목이 없습니다</h3>
          <p className="text-sm max-w-xs leading-relaxed">
            각 트랙(Track) 리스트에서 알고리즘 추천 종목을 검토하고<br/>
            <span className="text-emerald-500 font-bold">CONFIRM</span> 버튼을 눌러 매매 대기열에 등록하세요.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          {stocks.map(stock => (
            <div key={stock.symbol} className="bg-slate-900 border border-emerald-500/30 rounded-3xl p-6 shadow-xl relative group overflow-hidden">
              <div className="absolute top-0 right-0 p-6 opacity-10 group-hover:opacity-20 transition-all pointer-events-none text-6xl">⏳</div>
              <div className="flex justify-between items-start mb-6">
                <div>
                  <h4 className="text-xl font-bold text-white">{stock.name}</h4>
                  <p className="text-emerald-500 font-mono text-xs flex items-center gap-1">
                    <span>✓ READY</span>
                    <span className="text-slate-600">|</span>
                    <span>{stock.symbol}</span>
                  </p>
                </div>
                <button 
                  onClick={() => onToggleBasket(stock.symbol)}
                  className="p-2 text-slate-600 hover:text-red-500 transition-all"
                  title="승인 취소 (제거)"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                </button>
              </div>

              <div className="space-y-4 mb-6">
                <div className="flex justify-between text-xs">
                  <span className="text-slate-500">상대강도(RS)</span>
                  <span className="text-blue-400 font-bold">{stock.rsScore} pt</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-slate-500">목표 진입가</span>
                  <span className="text-white font-bold">{stock.price.toLocaleString()}원</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-slate-500">손절 기준선</span>
                  <span className="text-red-400 font-bold">{stock.stopLossPrice.toLocaleString()}원</span>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <div className="flex-1 px-4 py-3 bg-emerald-950/30 border border-emerald-900 rounded-xl flex items-center justify-center gap-2">
                  <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></span>
                  <span className="text-[10px] font-bold text-emerald-400 uppercase tracking-wider">Trading Active</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default BasketView;
