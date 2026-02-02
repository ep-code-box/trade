
import { StockData, TrackType, MarketSummary, AccountInfo, PositionStatus } from './types';

export const MOCK_MARKET_SUMMARY: MarketSummary = {
  totalStocks: 2540,
  marketRS: 74,
  activeLeaders: 124,
  stage2Ratio: 12.5,
  lastSync: new Date().toLocaleString('ko-KR')
};

export const MOCK_ACCOUNT: AccountInfo = {
  totalAsset: 125400000,
  depositSeed: 95000000,
  profitSeed: 30400000,
  cash: 35000000,
  buyingPower: 45000000,
  totalProfit: 12450000,
  totalProfitRate: 11.2,
  riskPerTradePercent: 1.0,
  maxSectorExposure: 2.5,
  positions: [
    {
      symbol: '000660',
      name: 'SK하이닉스',
      avgPrice: 165000,
      currentPrice: 185200,
      quantity: 150,
      initialStopLoss: 158000,
      trailingStop: 178000,
      breakEvenPrice: 165000,
      targetPrice: 220000,
      profitRate: 12.24,
      sector: '반도체',
      entryDate: '2024-01-15',
      status: PositionStatus.HEALTHY,
      daysHeld: 45,
      violations: [],
      rsTrend: 'rising',
      vitalityScore: 92
    },
    {
      symbol: '042700',
      name: '한미반도체',
      avgPrice: 135000,
      currentPrice: 154200,
      quantity: 200,
      initialStopLoss: 128000,
      trailingStop: 148000,
      breakEvenPrice: 135000,
      targetPrice: 195000,
      profitRate: 14.22,
      sector: '반도체장비',
      entryDate: '2024-02-10',
      status: PositionStatus.CAUTION,
      daysHeld: 20,
      violations: ["기관 수급 이탈 징후", "RS 탄력 둔화"],
      rsTrend: 'falling',
      vitalityScore: 68
    },
    {
      symbol: '005930',
      name: '삼성전자',
      avgPrice: 78000,
      currentPrice: 74000,
      quantity: 300,
      initialStopLoss: 75000,
      trailingStop: 75000,
      breakEvenPrice: 78000,
      targetPrice: 95000,
      profitRate: -5.12,
      sector: '반도체',
      entryDate: '2024-02-20',
      status: PositionStatus.VIOLATED,
      daysHeld: 10,
      violations: ["손절가 하향 이탈"],
      rsTrend: 'falling',
      vitalityScore: 12
    }
  ]
};

const defaultTemplate = {
  priceAbove150_200: true,
  sma150Above200: true,
  sma200TrendingUp: true,
  sma50Above150_200: true,
  priceAbove50: true,
  above52wLow25: true,
  within52wHigh25: true,
  rsAbove70: true
};

export const MOCK_STOCKS: StockData[] = [
  {
    symbol: '000660',
    name: 'SK하이닉스',
    price: 185200,
    change: 2.15,
    rsScore: 98,
    vcpRatio: 0.28,
    sma200: 162000,
    sma150: 171000,
    sma50: 181000,
    track: TrackType.TRACK_1,
    volumeDryUp: true,
    isStage2: true,
    sector: '반도체',
    template: { ...defaultTemplate },
    targetPrice: 215000,
    stopLossPrice: 172000,
    rationale: ["HBM 주도주", "RS 98", "완벽한 정배열"],
    atr: 5400,
    volatility: 3.2
  },
  {
    symbol: '042700',
    name: '한미반도체',
    price: 154200,
    change: 4.52,
    rsScore: 99,
    vcpRatio: 0.12,
    sma200: 98000,
    sma150: 121000,
    sma50: 145000,
    track: TrackType.TRACK_1,
    volumeDryUp: true,
    isStage2: true,
    sector: '반도체장비',
    template: { ...defaultTemplate },
    targetPrice: 195000,
    stopLossPrice: 142000,
    rationale: ["VCP 3차 수축", "상대강도 최고치"],
    atr: 8200,
    volatility: 5.4
  }
];
