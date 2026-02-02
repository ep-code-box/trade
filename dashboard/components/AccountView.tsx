
import React, { useState } from 'react';
import { MOCK_ACCOUNT } from '../mockData';
import { Position, PositionStatus } from '../types';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, Cell, PieChart, Pie } from 'recharts';

const AccountView: React.FC = () => {
  const [selectedPosition, setSelectedPosition] = useState<Position | null>(null);

  const sectorRisk = MOCK_ACCOUNT.positions.reduce((acc, pos) => {
    const riskAmount = (pos.avgPrice - (pos.trailingStop || pos.initialStopLoss)) * pos.quantity;
    acc[pos.sector] = (acc[pos.sector] || 0) + Math.max(0, riskAmount);
    return acc;
  }, {} as Record<string, number>);

  const sectorData = Object.entries(sectorRisk).map(([name, value]) => ({
    name,
    value,
    percent: (value / MOCK_ACCOUNT.depositSeed) * 100
  }));

  const totalHeatAmount = Object.values(sectorRisk).reduce((a, b) => a + b, 0);
  const totalHeatPercent = (totalHeatAmount / MOCK_ACCOUNT.depositSeed) * 100;

  const getStatusColor = (status: PositionStatus) => {
    switch (status) {
      case PositionStatus.HEALTHY: return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20';
      case PositionStatus.CAUTION: return 'text-orange-400 bg-orange-500/10 border-orange-500/20';
      case PositionStatus.VIOLATED: return 'text-red-400 bg-red-500/10 border-red-500/20';
      case PositionStatus.DEAD_MONEY: return 'text-purple-400 bg-purple-500/10 border-purple-500/20';
      default: return 'text-slate-400';
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-500 pb-20">
      {/* 초결벽주의 리스크 요약 */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 flex flex-col justify-between shadow-2xl relative overflow-hidden group">
          <div className="absolute -right-4 -top-4 w-24 h-24 bg-blue-600/5 rounded-full blur-2xl group-hover:bg-blue-600/10 transition-all"></div>
          <div>
            <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1">Expectancy Ratio</p>
            <h2 className="text-3xl font-bold font-mono text-white">1 : 3.2</h2>
          </div>
          <p className="text-[10px] text-slate-500 mt-4 leading-relaxed">
            평균 손절 대비 수익비. <br/>
            <span className="text-emerald-500">결벽주의 기준 합격</span>
          </p>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 flex flex-col justify-between shadow-2xl">
          <div>
            <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1">Portfolio Heat</p>
            <h2 className={`text-3xl font-bold font-mono ${totalHeatPercent > 6 ? 'text-red-500' : 'text-blue-400'}`}>
              {totalHeatPercent.toFixed(2)}%
            </h2>
          </div>
          <div className="mt-4 pt-4 border-t border-slate-800 flex items-center justify-between">
             <span className="text-[9px] text-slate-500">Max SL Impact</span>
             <span className="text-[10px] font-bold text-white">₩{totalHeatAmount.toLocaleString()}</span>
          </div>
        </div>

        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-2xl overflow-hidden">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-sm font-bold text-slate-400">Sector Risk Concentration</h3>
            <span className="text-[10px] text-red-500 font-bold uppercase tracking-tighter">Limit: {MOCK_ACCOUNT.maxSectorExposure}%</span>
          </div>
          <div className="h-16 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart layout="vertical" data={sectorData}>
                <XAxis type="number" hide domain={[0, MOCK_ACCOUNT.maxSectorExposure * 1.5]} />
                <YAxis dataKey="name" type="category" stroke="#475569" fontSize={10} width={70} axisLine={false} tickLine={false} />
                <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                  {sectorData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.percent > MOCK_ACCOUNT.maxSectorExposure ? '#ef4444' : '#3b82f6'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* 보유 포지션 관리 테이블 */}
      <div className="bg-slate-900 border border-slate-800 rounded-3xl overflow-hidden shadow-2xl">
        <div className="p-6 border-b border-slate-800 bg-slate-800/20 flex justify-between items-center">
          <h3 className="font-bold text-lg flex items-center gap-2">
            <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
            Trend Vitality Audit
          </h3>
          <div className="flex gap-4">
             <div className="flex items-center gap-2 text-[10px] font-bold text-slate-500">
                <span className="w-2 h-2 bg-emerald-500 rounded-sm"></span> HEALTHY
             </div>
             <div className="flex items-center gap-2 text-[10px] font-bold text-slate-500">
                <span className="w-2 h-2 bg-purple-500 rounded-sm"></span> STAGNANT
             </div>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead className="bg-slate-800/40 text-[10px] font-bold text-slate-500 uppercase tracking-widest">
              <tr>
                <th className="px-8 py-5">Asset / Vitality</th>
                <th className="px-6 py-5">Status / RS</th>
                <th className="px-6 py-5">Trailing Stop</th>
                <th className="px-6 py-5">Profit / RR</th>
                <th className="px-8 py-5 text-right">Timer</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50">
              {MOCK_ACCOUNT.positions.map(pos => (
                <tr 
                  key={pos.symbol} 
                  className={`hover:bg-blue-600/5 transition-colors cursor-pointer ${selectedPosition?.symbol === pos.symbol ? 'bg-blue-600/10' : ''}`}
                  onClick={() => setSelectedPosition(pos)}
                >
                  <td className="px-8 py-5">
                    <div className="flex flex-col gap-2">
                      <span className="font-bold text-white text-md">{pos.name}</span>
                      <div className="w-20 h-1 bg-slate-800 rounded-full overflow-hidden">
                        <div 
                          className={`h-full transition-all ${pos.vitalityScore > 80 ? 'bg-emerald-500' : pos.vitalityScore > 50 ? 'bg-orange-500' : 'bg-red-500'}`} 
                          style={{ width: `${pos.vitalityScore}%` }}
                        ></div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-5">
                    <div className="flex flex-col gap-1">
                      <span className={`px-2 py-0.5 rounded-md text-[9px] font-bold border inline-block w-fit ${getStatusColor(pos.status)}`}>
                        {pos.status}
                      </span>
                      <span className={`text-[10px] font-bold ${pos.rsTrend === 'rising' ? 'text-emerald-500' : 'text-red-500'}`}>
                        RS {pos.rsTrend.toUpperCase()}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-5 font-mono text-xs text-slate-300">
                    ₩{pos.trailingStop.toLocaleString()}
                  </td>
                  <td className="px-6 py-5">
                    <div className="flex flex-col">
                      <span className={`text-sm font-mono font-bold ${pos.profitRate >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                        {pos.profitRate >= 0 ? '+' : ''}{pos.profitRate}%
                      </span>
                      <span className="text-[10px] text-slate-500">R:R 1:{((pos.targetPrice - pos.avgPrice) / (pos.avgPrice - pos.initialStopLoss)).toFixed(1)}</span>
                    </div>
                  </td>
                  <td className="px-8 py-5 text-right">
                    <div className="flex flex-col items-end">
                      <span className="text-xs font-mono text-white">{pos.daysHeld}d</span>
                      {pos.daysHeld > 30 && pos.profitRate < 5 && (
                        <span className="text-[9px] text-purple-400 font-bold">DEAD MONEY ⏳</span>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* 상세 관리 패널 (Audit) */}
      {selectedPosition && (
        <div className="bg-slate-900 border border-blue-600/30 rounded-3xl p-8 animate-in slide-in-from-bottom-4 shadow-[0_0_50px_rgba(37,99,235,0.1)] relative">
          <div className="absolute top-8 right-8 flex gap-2">
            <button onClick={() => setSelectedPosition(null)} className="p-2 bg-slate-800 rounded-full text-slate-500 hover:text-white transition-all">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-12">
            <div className="space-y-8">
              <div>
                <h3 className="text-3xl font-bold text-white mb-1">{selectedPosition.name}</h3>
                <p className="text-blue-500 font-mono text-xs">{selectedPosition.symbol} / {selectedPosition.sector}</p>
              </div>
              
              <div className="space-y-4">
                 <div className="p-4 bg-slate-800/40 rounded-2xl border border-slate-700/50">
                    <p className="text-[10px] font-bold text-slate-500 uppercase mb-3">Trend Vitality</p>
                    <div className="flex items-end gap-3">
                       <span className={`text-4xl font-bold font-mono ${selectedPosition.vitalityScore > 70 ? 'text-emerald-400' : 'text-orange-400'}`}>
                         {selectedPosition.vitalityScore}
                       </span>
                       <span className="text-xs text-slate-500 pb-1">/ 100</span>
                    </div>
                 </div>
              </div>
            </div>

            <div className="md:col-span-2 space-y-8">
              <h4 className="text-xs font-bold text-slate-500 uppercase tracking-widest border-b border-slate-800 pb-2">Management Protocol</h4>
              <div className="grid grid-cols-2 gap-6">
                <AuditItem 
                  title="본절 보존 (Break-even)" 
                  status={selectedPosition.profitRate > 10 ? 'ACTIVE' : 'WAITING'} 
                  desc="수익 10% 돌파 시 스탑을 평단가로 이동"
                />
                <AuditItem 
                  title="변동성 익절 (Chandelier)" 
                  status={selectedPosition.rsTrend === 'falling' ? 'DANGER' : 'HEALTHY'} 
                  desc="최고점 대비 2.5*ATR 하락 시 전량 매도"
                />
                <AuditItem 
                  title="상대강도(RS) 모니터" 
                  status={selectedPosition.rsTrend === 'rising' ? 'STRENGTH' : 'WEAKNESS'} 
                  desc="시장 대비 상승 탄력 유지 여부"
                />
                <AuditItem 
                  title="시간 손절 (Dead Money)" 
                  status={selectedPosition.daysHeld > 30 && selectedPosition.profitRate < 5 ? 'EXPIRED' : 'VALID'} 
                  desc="진입 후 30일 내 5% 미수익 시 교체"
                />
              </div>
            </div>

            <div className="space-y-6">
              <h4 className="text-xs font-bold text-slate-500 uppercase tracking-widest border-b border-slate-800 pb-2">Execution</h4>
              <div className="space-y-3">
                <button className="w-full py-4 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-2xl shadow-lg shadow-blue-900/20 transition-all active:scale-95">
                  피라미딩 (비중 확대)
                </button>
                <button className={`w-full py-4 bg-slate-800 border ${selectedPosition.status === PositionStatus.VIOLATED ? 'border-red-500/50 text-red-400' : 'border-slate-700 text-slate-400'} font-bold rounded-2xl transition-all`}>
                  부분 익절 (25% 매도)
                </button>
                <button className="w-full py-4 border border-red-500/30 text-red-500 hover:bg-red-500/10 font-bold rounded-2xl transition-all">
                  전량 청산 (Market Exit)
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const AuditItem = ({ title, status, desc }: { title: string, status: string, desc: string }) => (
  <div className="p-4 bg-slate-800/20 border border-slate-800 rounded-2xl space-y-2">
    <div className="flex justify-between items-center">
      <span className="text-[11px] font-bold text-slate-400">{title}</span>
      <span className={`text-[9px] font-bold px-2 py-0.5 rounded-full ${
        ['ACTIVE', 'HEALTHY', 'STRENGTH', 'VALID'].includes(status) ? 'bg-emerald-500/10 text-emerald-500' : 'bg-red-500/10 text-red-500'
      }`}>
        {status}
      </span>
    </div>
    <p className="text-[10px] text-slate-600 leading-tight">{desc}</p>
  </div>
);

export default AccountView;
