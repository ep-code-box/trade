
import React, { useState, useEffect } from 'react';
import { StockData, MentorInsight } from '../types';
import StockChart from './StockChart';
import { MOCK_MARKET_SUMMARY } from '../mockData';

interface DashboardProps {
  stocks: StockData[];
  summary: any; // MarketSummary 확장
  insight: MentorInsight | null;
  loading: boolean;
  onRetry: () => void;
}

const Dashboard: React.FC<DashboardProps> = ({ stocks, summary, insight, loading, onRetry }) => {
  const [logs, setLogs] = useState<string[]>(["[SYSTEM] TrendHunter Engine Initializing..."]);
  const leadersCount = summary.activeLeaders || 0;
  const stage2Ratio = summary.stage2Ratio || 0;

  return (
    <div className="space-y-8 animate-in fade-in duration-700 pb-12">
      <section className="grid grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6">
        <StatCard title="Stage 2 Ratio" value={`${stage2Ratio}%`} sub={`시장 강세 흐름`} trend={stage2Ratio > 20 ? "up" : "neutral"} />
        <StatCard title="Active Leaders" value={`${leadersCount}개`} sub="스크리너 통과 종목" trend={leadersCount > 5 ? "up" : "neutral"} />
        <StatCard title="Risk Level" value={summary.riskLevel || "SAFE"} sub={`Alpha: ${summary.marketRS}`} trend={summary.riskLevel === "SAFE" ? "up" : "warning"} />
        <StatCard title="Key Sector" value={summary.topSector || "None"} sub="장세 주도 테마" trend="warning" />
      </section>

      <section className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-slate-900/60 border border-slate-800 rounded-3xl p-8 shadow-2xl relative overflow-hidden backdrop-blur-xl group">
            <div className="absolute top-0 left-0 w-1.5 h-full bg-blue-600 shadow-[0_0_15px_rgba(37,99,235,0.5)]"></div>
            <h3 className="text-xl font-bold mb-6 flex items-center justify-between">
              시장 리더 퍼포먼스 (RS Alpha)
            </h3>
            <div className="h-[300px]">
              <StockChart stocks={stocks} />
            </div>
          </div>

          <div className="bg-black/80 border border-slate-800/50 rounded-2xl p-4 font-mono text-[11px] h-40 overflow-hidden shadow-inner">
            <div className="flex items-center justify-between mb-3 pb-2 border-b border-slate-800/50">
              <span className="text-slate-600 font-bold uppercase tracking-widest">System Engine Log</span>
              <span className="text-green-500/80 flex items-center gap-1.5 font-bold tracking-tighter">
                <span className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse"></span> LIVE
              </span>
            </div>
            <div className="space-y-1.5">
              {logs.map((log, idx) => (
                <div key={idx} className={`${log.includes('SUCCESS') || log.includes('READY') ? 'text-blue-400' : 'text-slate-400'}`}>
                  <span className="text-slate-700 mr-2">[{new Date().toLocaleTimeString()}]</span>
                  {log}
                </div>
              ))}
              <div className="animate-pulse text-blue-500">_</div>
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 flex flex-col h-full shadow-2xl relative overflow-hidden">
            <div className="flex items-center justify-between mb-8">
               <h3 className="text-xl font-bold flex items-center gap-2">🧠 AI 전략 리포트</h3>
               {insight && !loading && (
                 <span className={`px-2 py-0.5 rounded-md text-[9px] font-bold border ${getSentimentColor(insight.sentiment)}`}>
                   {insight.sentiment.toUpperCase()}
                 </span>
               )}
            </div>

            {loading ? (
              <div className="flex-1 flex flex-col items-center justify-center space-y-4">
                <div className="w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                <p className="text-[10px] text-slate-500 font-bold uppercase animate-pulse">Gemini 퀀트 엔진 분석 중...</p>
              </div>
            ) : insight ? (
              <div className="flex-1 space-y-8 flex flex-col">
                <div className="space-y-4">
                  <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                    <span className="text-[10px] font-bold text-slate-500 uppercase">Market Phase</span>
                    <span className="text-xs font-bold text-blue-400">{insight.marketPhase}</span>
                  </div>
                  <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                    <span className="text-[10px] font-bold text-slate-500 uppercase">Top Sector</span>
                    <span className="text-xs font-bold text-emerald-400">{insight.topSector}</span>
                  </div>
                </div>

                <div className="p-5 rounded-2xl bg-slate-800/40 border border-slate-700/50">
                  <p className="text-slate-300 text-xs leading-relaxed italic opacity-90">
                    "{insight.content}"
                  </p>
                </div>

                <div className="space-y-4 flex-1">
                   <h4 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Action Items</h4>
                   <div className="space-y-3">
                      {insight.actionItems.map((item, idx) => (
                        <div key={idx} className="flex items-start gap-3 text-xs text-slate-300">
                           <span className="w-4 h-4 bg-blue-600/20 border border-blue-500/30 rounded flex items-center justify-center text-[8px] text-blue-400 font-bold shrink-0">
                             {idx + 1}
                           </span>
                           <span className="leading-tight">{item}</span>
                        </div>
                      ))}
                   </div>
                </div>

                <button 
                  onClick={onRetry}
                  className="w-full py-3 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-400 text-[10px] font-bold rounded-xl transition-all mb-4 uppercase tracking-tighter"
                >
                  리포트 새로고침 (Refresh)
                </button>

                <div className="mt-auto pt-4 border-t border-slate-800">
                  <p className="text-[9px] text-slate-600 font-medium">
                    * AI 멘토의 분석은 실시간으로 요청 시에만 생성됩니다.
                  </p>
                </div>
              </div>
            ) : (
              <div className="flex-1 flex flex-col items-center justify-center text-center space-y-6">
                <div className="w-16 h-16 bg-blue-600/10 rounded-full flex items-center justify-center text-3xl">🤖</div>
                <div>
                  <h4 className="text-sm font-bold text-white mb-2">AI 퀀트 멘토링 준비됨</h4>
                  <p className="text-[10px] text-slate-500 leading-relaxed px-4">
                    현재 스크리닝된 {stocks.length}개 주도주 데이터를 바탕으로<br/>
                    Gemini AI가 시장 국면과 전략 리포트를 생성합니다.
                  </p>
                </div>
                <button 
                  onClick={onRetry}
                  className="px-8 py-3 bg-blue-600 hover:bg-blue-500 text-white text-[10px] font-bold rounded-xl shadow-lg shadow-blue-900/30 transition-all active:scale-95 uppercase tracking-widest"
                >
                  AI 분석 리포트 생성
                </button>
              </div>
            )}
          </div>
        </div>
      </section>
    </div>
  );
};

const StatCard = ({ title, value, sub, trend }: { title: string, value: string, sub: string, trend: 'up'|'down'|'neutral'|'warning' }) => (
  <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl hover:bg-slate-800/40 transition-all shadow-xl">
    <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-3">{title}</p>
    <div className="flex items-baseline justify-between">
      <h2 className="text-2xl font-bold text-white font-mono">{value}</h2>
      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
        trend === 'up' ? 'text-green-400 border-green-500/20 bg-green-500/10' : 
        trend === 'down' ? 'text-red-400 border-red-500/20 bg-red-500/10' : 
        'text-blue-400 border-blue-500/20 bg-blue-500/10'
      }`}>●</span>
    </div>
    <p className="text-[11px] text-slate-500 mt-2 font-medium">{sub}</p>
  </div>
);

export default Dashboard;
