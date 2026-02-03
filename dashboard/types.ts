
export enum TrackType {
  TRACK_1 = '트랙 1: 추세 추종 (주도주)',
  TRACK_EX = '트랙 EX: 개별 모멘텀',
  TRACK_2 = '트랙 2: 뚜벅이 (고배당)'
}

export enum PositionStatus {
  HEALTHY = '추세 유지',
  CAUTION = '추세 약화',
  VIOLATED = '원칙 위반 (매도)',
  STAGNANT = '기간 조정 (관찰)',
  DEAD_MONEY = '시간 손절 대상'
}

export interface AIConfig {
  apiKey: string;
  systemPrompt: string;
}

export interface KISConfig {
  appKey: string;
  appSecret: string;
  accountNumber: string;
  isRealTrading: boolean;
  vtsUrl: string;
  realUrl: string;
}

// 스크리너 엔진 정밀 설정
export interface ScreenerRules {
  minRSScore: number;
  minDistanceLow52w: number; // 52주 저점 대비 최소 상승폭 (%)
  maxDistanceHigh52w: number; // 52주 고점 대비 최대 거리 (%)
  requireSmaAlignment: boolean; // 정배열 강제 여부 (50 > 150 > 200)
  sma200TrendDays: number; // 200일선 상승 유지 최소 일수
  vcpTightnessThreshold: number; // VCP 마지막 수축 최대폭 (%)
  volumeDryUpFactor: number; // 거래량 급감 기준 (평균 대비 %)
}

export interface TradingRules {
  autoBreakEven: boolean;
  breakEvenTriggerPct: number;
  deadMoneyTimeoutDays: number;
  maxSectorRiskPct: number;
  maxStockRiskPct: number;
  pyramidingLimit: number;
  rsDecayWarning: boolean;
  screener: ScreenerRules; // 추가
}

export interface TrendTemplateStatus {
  priceAbove150_200: boolean;
  sma150Above200: boolean;
  sma200TrendingUp: boolean;
  sma50Above150_200: boolean;
  priceAbove50: boolean;
  above52wLow25: boolean;
  within52wHigh25: boolean;
  rsAbove70: boolean;
}

export interface StockData {
  date?: string;
  symbol: string;
  name: string;
  price: number;
  change: number;
  rsScore: number;
  vcpRatio: number;
  sma200: number;
  sma150: number;
  sma50: number;
  track: TrackType | string;
  dividendYield?: number;
  roe?: number;
  opMargin?: number;
  volumeDryUp: boolean;
  isStage2: boolean;
  sector: string;
  template: TrendTemplateStatus;
  targetPrice: number;
  stopLossPrice: number;
  rationale: string[];
  atr: number; 
  volatility: number;
}

export interface Position {
  symbol: string;
  name: string;
  avgPrice: number;
  currentPrice: number;
  quantity: number;
  initialStopLoss: number;
  trailingStop: number; 
  breakEvenPrice: number;
  targetPrice: number;
  profitRate: number;
  sector: string;
  entryDate: string;
  status: PositionStatus;
  daysHeld: number;
  violations: string[];
  rsTrend: 'rising' | 'flat' | 'falling';
  vitalityScore: number;
}

export interface AccountInfo {
  totalAsset: number;
  depositSeed: number; 
  profitSeed: number;  
  cash: number;
  buyingPower: number;
  totalProfit: number;
  totalProfitRate: number;
  positions: Position[];
  riskPerTradePercent: number;
  maxSectorExposure: number;
}

export interface MarketSummary {
  totalStocks: number;
  marketRS: number;
  activeLeaders: number;
  stage2Ratio: number;
  lastSync: string;
  topSector?: string;
  riskLevel?: string;
}

export interface MentorInsight {
  title: string;
  content: string;
  sentiment: 'bullish' | 'bearish' | 'neutral' | 'warning';
  topSector: string;
  actionItems: string[];
  marketPhase: string;
  error?: string;
}
