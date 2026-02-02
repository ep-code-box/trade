
import React, { useState, useEffect } from 'react';
import { KISConfig, TradingRules, AIConfig, ScreenerRules } from '../types';

const DEFAULT_PROMPT = `당신은 세계 최고의 퀀트 트레이딩 전략가이자 'TrendHunter' 시스템의 AI 수석 멘토입니다.
마크 미너비니, 윌리엄 오닐, 제시 리버모어의 철학을 완벽하게 계승합니다.

[분석 지침]
1. 시장의 현 단계(Phase)를 진단하십시오 (축적, 상승, 분산, 하락).
2. 가장 공격적으로 비중을 실어야 할 'Top Sector'를 선정하십시오.
3. 데이터에 기반하여 '결벽주의적' 트레이딩 지시사항(Action Items)을 3개 만드십시오.
4. 전체적인 시장 총평을 '전문적이고 단호한' 어조로 작성하십시오.

반드시 JSON 구조로 응답하십시오.`;

const DEFAULT_SCREENER: ScreenerRules = {
  minRSScore: 70,
  minDistanceLow52w: 25,
  maxDistanceHigh52w: 25,
  requireSmaAlignment: true,
  sma200TrendDays: 30,
  vcpTightnessThreshold: 10,
  volumeDryUpFactor: 50
};

const SettingsView: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'broker' | 'ai' | 'screener' | 'risk'>('screener');
  
  const [kisConfig, setKisConfig] = useState<KISConfig>({
    appKey: '', appSecret: '', accountNumber: '', isRealTrading: false,
    vtsUrl: 'https://openapivts.koreainvestment.com:29443',
    realUrl: 'https://openapi.koreainvestment.com:9443'
  });

  const [aiConfig, setAiConfig] = useState<AIConfig>({
    apiKey: '', systemPrompt: DEFAULT_PROMPT
  });

  const [rules, setRules] = useState<TradingRules>({
    autoBreakEven: true, breakEvenTriggerPct: 10, deadMoneyTimeoutDays: 30,
    maxSectorRiskPct: 2.5, maxStockRiskPct: 1.0, pyramidingLimit: 3, rsDecayWarning: true,
    screener: DEFAULT_SCREENER
  });

  useEffect(() => {
    const savedAi = localStorage.getItem('th_ai_config');
    const savedRules = localStorage.getItem('th_trading_rules');
    if (savedAi) setAiConfig(JSON.parse(savedAi));
    if (savedRules) setRules(JSON.parse(savedRules));
  }, []);

  const saveAll = () => {
    localStorage.setItem('th_ai_config', JSON.stringify(aiConfig));
    localStorage.setItem('th_trading_rules', JSON.stringify(rules));
    alert('모든 전략 및 시스템 설정이 로컬 DB에 저장되었습니다.');
  };

  const resetScreener = () => {
    if (window.confirm('스크리너 룰을 미너비니 표준값으로 초기화하시겠습니까?')) {
      setRules({ ...rules, screener: DEFAULT_SCREENER });
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-20">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <h2 className="text-3xl font-bold text-white tracking-tight">System Configuration</h2>
          <p className="text-slate-500 text-sm mt-1">TrendHunter 엔진의 모든 파라미터를 제어합니다.</p>
        </div>
        <button 
          onClick={saveAll}
          className="px-8 py-3 bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold rounded-xl shadow-lg shadow-blue-900/40 transition-all active:scale-95"
        >
          설정 일괄 저장
        </button>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-2 p-1 bg-slate-900/50 rounded-2xl border border-slate-800 w-fit">
        {[
          { id: 'screener', label: '스크리너 룰', icon: '🔍' },
          { id: 'risk', label: '리스크 관리', icon: '🛡️' },
          { id: 'ai', label: 'AI 전략 멘토', icon: '🧠' },
          { id: 'broker', label: '증권사 연동', icon: '🏦' },
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`px-5 py-2.5 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
              activeTab === tab.id ? 'bg-slate-800 text-white shadow-lg' : 'text-slate-500 hover:text-slate-300'
            }`}
          >
            <span>{tab.icon}</span>
            {tab.label}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-8">
        {/* 스크리너 룰 탭 */}
        {activeTab === 'screener' && (
          <div className="space-y-6 animate-in fade-in duration-300">
            <div className="bg-slate-900 border border-slate-800 rounded-3xl p-8 space-y-8 shadow-2xl relative overflow-hidden">
              <div className="absolute top-0 right-0 p-8 opacity-10 pointer-events-none text-8xl">🔍</div>
              <div className="flex justify-between items-center">
                <h3 className="text-xl font-bold text-white">Screener Engine Logic</h3>
                <button onClick={resetScreener} className="text-[10px] text-slate-500 hover:text-blue-400 font-bold uppercase tracking-widest border border-slate-800 px-3 py-1 rounded-lg">Reset to Minervini</button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
                <div className="space-y-6">
                  <h4 className="text-[11px] font-bold text-blue-500 uppercase tracking-widest border-b border-slate-800 pb-2">Trend Template</h4>
                  <RangeInput 
                    label="최소 RS 점수 (Rel. Strength)" 
                    value={rules.screener.minRSScore} 
                    min={0} max={99} 
                    onChange={v => setRules({...rules, screener: {...rules.screener, minRSScore: v}})}
                  />
                  <RangeInput 
                    label="52주 저점 대비 최소 상승 (%)" 
                    value={rules.screener.minDistanceLow52w} 
                    min={0} max={100} 
                    onChange={v => setRules({...rules, screener: {...rules.screener, minDistanceLow52w: v}})}
                  />
                  <RangeInput 
                    label="52주 고점 대비 최대 거리 (%)" 
                    value={rules.screener.maxDistanceHigh52w} 
                    min={0} max={50} 
                    onChange={v => setRules({...rules, screener: {...rules.screener, maxDistanceHigh52w: v}})}
                  />
                </div>

                <div className="space-y-6">
                  <h4 className="text-[11px] font-bold text-emerald-500 uppercase tracking-widest border-b border-slate-800 pb-2">VCP & Technicals</h4>
                  <RangeInput 
                    label="VCP 수축 임계값 (%)" 
                    value={rules.screener.vcpTightnessThreshold} 
                    min={1} max={30} 
                    onChange={v => setRules({...rules, screener: {...rules.screener, vcpTightnessThreshold: v}})}
                  />
                  <RangeInput 
                    label="거래량 급감 기준 (평균 대비 %)" 
                    value={rules.screener.volumeDryUpFactor} 
                    min={10} max={100} 
                    onChange={v => setRules({...rules, screener: {...rules.screener, volumeDryUpFactor: v}})}
                  />
                  <div className="flex items-center justify-between p-4 bg-slate-800/40 rounded-2xl border border-slate-700/50">
                    <div>
                      <p className="text-xs font-bold text-slate-300">SMA 정배열 강제</p>
                      <p className="text-[10px] text-slate-500 mt-1">50일 &gt; 150일 &gt; 200일선 유지 필수</p>
                    </div>
                    <button 
                      onClick={() => setRules({...rules, screener: {...rules.screener, requireSmaAlignment: !rules.screener.requireSmaAlignment}})}
                      className={`w-12 h-6 rounded-full p-1 transition-all ${rules.screener.requireSmaAlignment ? 'bg-blue-600' : 'bg-slate-700'}`}
                    >
                      <div className={`w-4 h-4 bg-white rounded-full transition-all ${rules.screener.requireSmaAlignment ? 'translate-x-6' : 'translate-x-0'}`}></div>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* 리스크 관리 탭 */}
        {activeTab === 'risk' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 animate-in fade-in duration-300">
            <RuleToggle 
              title="본절가 자동 이동 (Break-even)"
              desc="수익권 진입 시 손절가를 평단가로 자동 상향합니다."
              active={rules.autoBreakEven}
              onToggle={() => setRules({...rules, autoBreakEven: !rules.autoBreakEven})}
            />
            <RuleToggle 
              title="RS 쇠퇴 사전 경보"
              desc="상대강도(RS) 탄력이 죽기 시작하면 비중 축소를 권고합니다."
              active={rules.rsDecayWarning}
              onToggle={() => setRules({...rules, rsDecayWarning: !rules.rsDecayWarning})}
            />
            <div className="bg-slate-900 border border-slate-800 rounded-3xl p-8 space-y-6 shadow-2xl">
              <h4 className="text-[11px] font-bold text-slate-500 uppercase tracking-widest border-b border-slate-800 pb-2">Risk Parameters</h4>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-xs text-slate-400">1종목 최대 리스크 (%)</span>
                  <input 
                    type="number" 
                    className="w-20 bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-right font-mono text-blue-400" 
                    value={rules.maxStockRiskPct} 
                    onChange={e => setRules({...rules, maxStockRiskPct: parseFloat(e.target.value)})} 
                  />
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-slate-400">섹터 노출 한도 (%)</span>
                  <input 
                    type="number" 
                    className="w-20 bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-right font-mono text-blue-400" 
                    value={rules.maxSectorRiskPct} 
                    onChange={e => setRules({...rules, maxSectorRiskPct: parseFloat(e.target.value)})} 
                  />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* AI 설정 탭 */}
        {activeTab === 'ai' && (
          <div className="bg-slate-900 border border-slate-800 rounded-3xl p-8 space-y-6 shadow-2xl animate-in fade-in duration-300">
            <div className="space-y-2">
              <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest px-1 flex items-center justify-between">
                Gemini API Key
                <a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noreferrer" className="text-blue-500 lowercase hover:underline">Get key →</a>
              </label>
              <input 
                type="password" 
                className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-sm font-mono text-white focus:border-blue-500 outline-none transition-all"
                value={aiConfig.apiKey}
                onChange={(e) => setAiConfig({...aiConfig, apiKey: e.target.value})}
              />
            </div>
            <div className="space-y-2">
              <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest px-1">System Strategy Prompt</label>
              <textarea 
                rows={10}
                className="w-full bg-slate-950 border border-slate-800 rounded-2xl px-5 py-4 text-xs font-mono text-slate-300 focus:border-blue-500 outline-none transition-all leading-relaxed"
                value={aiConfig.systemPrompt}
                onChange={(e) => setAiConfig({...aiConfig, systemPrompt: e.target.value})}
              />
            </div>
          </div>
        )}

        {/* 증권사 연동 탭 */}
        {activeTab === 'broker' && (
          <div className="bg-slate-900 border border-slate-800 rounded-3xl p-8 space-y-8 shadow-2xl animate-in fade-in duration-300">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div className="space-y-2">
                <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest px-1">Brokerage Mode</label>
                <div className="flex p-1 bg-slate-800 rounded-xl">
                  <button 
                    onClick={() => setKisConfig({...kisConfig, isRealTrading: false})}
                    className={`flex-1 py-2 text-xs font-bold rounded-lg transition-all ${!kisConfig.isRealTrading ? 'bg-blue-600 text-white' : 'text-slate-500'}`}
                  >
                    모의 (VTS)
                  </button>
                  <button 
                    onClick={() => setKisConfig({...kisConfig, isRealTrading: true})}
                    className={`flex-1 py-2 text-xs font-bold rounded-lg transition-all ${kisConfig.isRealTrading ? 'bg-red-600 text-white' : 'text-slate-500'}`}
                  >
                    실전 (REAL)
                  </button>
                </div>
              </div>
              <div className="space-y-2">
                <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest px-1">Account Number</label>
                <input 
                  type="text" 
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-sm font-mono text-white focus:border-blue-500 outline-none transition-all"
                  value={kisConfig.accountNumber}
                  onChange={(e) => setKisConfig({...kisConfig, accountNumber: e.target.value})}
                />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

const RangeInput = ({ label, value, min, max, onChange }: { label: string, value: number, min: number, max: number, onChange: (v: number) => void }) => (
  <div className="space-y-3">
    <div className="flex justify-between items-center">
      <span className="text-xs font-bold text-slate-400">{label}</span>
      <span className="text-xs font-mono text-blue-400 font-bold">{value}%</span>
    </div>
    <input 
      type="range" min={min} max={max} value={value} 
      onChange={e => onChange(parseInt(e.target.value))}
      className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-blue-600"
    />
  </div>
);

const RuleToggle = ({ title, desc, active, onToggle }: { title: string, desc: string, active: boolean, onToggle: () => void }) => (
  <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 flex flex-col justify-between hover:border-blue-500/30 transition-all shadow-xl">
    <div className="space-y-2 mb-4">
      <h4 className="text-sm font-bold text-white">{title}</h4>
      <p className="text-[10px] text-slate-500 leading-relaxed">{desc}</p>
    </div>
    <div className="flex justify-end">
      <button 
        onClick={onToggle}
        className={`w-10 h-5 rounded-full p-1 transition-all ${active ? 'bg-blue-600' : 'bg-slate-800'}`}
      >
        <div className={`w-3 h-3 bg-white rounded-full transition-all ${active ? 'translate-x-5' : 'translate-x-0'}`}></div>
      </button>
    </div>
  </div>
);

export default SettingsView;
