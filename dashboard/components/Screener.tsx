
import React, { useState } from 'react';
import { StockData } from '../types';
import StockDetailChart from './StockDetailChart';

interface ScreenerProps {
  stocks: StockData[];
  trackName: string;
  basket: string[];
  onToggleBasket: (symbol: string) => void;
}

const TemplateDot: React.FC<{ active: boolean; index: number }> = ({ active, index }) => (
  <div 
    className={`w-4 h-4 rounded-md flex items-center justify-center text-[8px] font-bold border transition-all duration-300 ${
      active 
        ? 'bg-blue-600 border-blue-400 text-white shadow-[0_0_10px_rgba(59,130,246,0.4)]' 
        : 'bg-slate-800 border-slate-700 text-slate-600'
    }`}
    title={`Rule ${index}`}
  >
    {index}
  </div>
);

const Screener: React.FC<ScreenerProps> = ({ stocks, trackName, basket, onToggleBasket }) => {
  const [selectedStock, setSelectedStock] = useState<StockData | null>(null);
  const isDividendTrack = trackName.includes('뚜벅이') || trackName.includes('TRACK 2');

  return (
    <div className="space-y-8 animate-in slide-in-from-bottom-4 duration-500 pb-20">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-2">
            {trackName}
          </h2>
          <p className="text-slate-400 text-sm mt-1 font-medium">
            {isDividendTrack ? '안정적인 현금흐름을 창출하는 고배당 우량주' : '손익비가 검증된 상위 리더 목록'}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-5 gap-8">
        <div className="xl:col-span-3 space-y-4">
          <div className="bg-slate-900 border border-slate-800 rounded-3xl overflow-hidden shadow-2xl">
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead className="bg-slate-800/30 text-slate-500 text-[10px] font-bold uppercase tracking-widest border-b border-slate-800">
                  <tr>
                    <th className="px-6 py-5">Target</th>
                    <th className="px-6 py-5">Ticker</th>
                    {isDividendTrack ? (
                      <>
                        <th className="px-6 py-5 text-center">Yield</th>
                        <th className="px-6 py-5 text-center">ROE</th>
                      </>
                    ) : (
                      <>
                        <th className="px-6 py-5 text-center">RS</th>
                        <th className="px-6 py-5 text-center">Template</th>
                      </>
                    )}
                    <th className="px-6 py-5 text-right">Price</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/50">
                  {stocks.sort((a,b) => isDividendTrack ? (b.dividendYield || 0) - (a.dividendYield || 0) : b.rsScore - a.rsScore).map((stock) => (
                    <tr 
                      key={stock.symbol} 
                      className={`transition-all group cursor-pointer ${selectedStock?.symbol === stock.symbol ? 'bg-blue-600/10' : 'hover:bg-blue-600/5'}`}
                      onClick={() => setSelectedStock(stock)}
                    >
                      <td className="px-6 py-5">
                        <button 
                          onClick={(e) => {
                            e.stopPropagation();
                            onToggleBasket(stock.symbol);
                          }}
                          className={`text-xl transition-all hover:scale-125 ${basket.includes(stock.symbol) ? 'grayscale-0 opacity-100' : 'grayscale opacity-30 hover:opacity-100'}`}
                        >
                          🛒
                        </button>
                      </td>
                      <td className="px-6 py-5">
                        <div className="flex flex-col">
                          <span className="text-blue-500 font-mono font-bold text-xs">KRX:{stock.symbol}</span>
                          <span className="font-bold text-white text-md group-hover:text-blue-400">{stock.name}</span>
                        </div>
                      </td>
                      
                      {isDividendTrack ? (
                        <>
                          <td className="px-6 py-5 text-center">
                            <span className="font-mono font-bold text-emerald-400">{(stock.dividendYield || 0).toFixed(1)}%</span>
                          </td>
                          <td className="px-6 py-5 text-center">
                            <span className="font-mono font-bold text-slate-300">{(stock as any).roe || 10}%</span>
                          </td>
                        </>
                      ) : (
                        <>
                          <td className="px-6 py-5 text-center">
                            <span className="font-mono font-bold text-blue-400">{stock.rsScore.toFixed(0)}</span>
                          </td>
                          <td className="px-6 py-5">
                            <div className="flex justify-center gap-1">
                              {(Object.entries(stock.template) as [string, boolean][]).slice(0, 4).map(([key, value], idx) => (
                                <TemplateDot key={key} active={value} index={idx + 1} />
                              ))}
                            </div>
                          </td>
                        </>
                      )}

                      <td className="px-6 py-5 text-right">
                        <p className="font-mono text-white font-bold">₩{stock.price.toLocaleString()}</p>
                        <p className={`text-xs font-bold ${stock.change >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                          {stock.change >= 0 ? '+' : ''}{stock.change}%
                        </p>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <div className="xl:col-span-2">
          {selectedStock ? (
            <div className="sticky top-10">
              <StockDetailChart 
                stock={selectedStock} 
                isInBasket={basket.includes(selectedStock.symbol)}
                onToggleBasket={() => onToggleBasket(selectedStock.symbol)}
              />
            </div>
          ) : (
            <div className="h-full border-2 border-dashed border-slate-800 rounded-3xl flex flex-col items-center justify-center p-12 text-center text-slate-600">
              <span className="text-4xl mb-4">📈</span>
              <p className="text-sm font-medium">종목을 선택하여 <br/>정밀 차트 및 손익비 분석을 시작하세요</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Screener;
