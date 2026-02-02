
import { GoogleGenAI, Type } from "@google/genai";
import { StockData, MentorInsight, AIConfig, TradingRules } from "../types";

const DEFAULT_PROMPT = `
당신은 세계 최고의 퀀트 트레이딩 전략가이자 'TrendHunter' 시스템의 AI 수석 멘토입니다.
마크 미너비니, 윌리엄 오닐, 제시 리버모어의 철학을 완벽하게 계승합니다.

[분석 지침]
1. 시장의 현 단계(Phase)를 진단하십시오 (축적, 상승, 분산, 하락).
2. 가장 공격적으로 비중을 실어야 할 'Top Sector'를 선정하십시오.
3. 데이터에 기반하여 '결벽주의적' 트레이딩 지시사항(Action Items)을 3개 만드십시오.
4. 전체적인 시장 총평을 '전문적이고 단호한' 어조로 작성하십시오.

반드시 JSON 구조로 응답하십시오.
`;

export const getMentorAnalysis = async (stocks: StockData[]): Promise<MentorInsight> => {
  const savedAiConfig = localStorage.getItem('th_ai_config');
  const savedRules = localStorage.getItem('th_trading_rules');
  
  const aiConfig: AIConfig = savedAiConfig ? JSON.parse(savedAiConfig) : { apiKey: '', systemPrompt: DEFAULT_PROMPT };
  const rules: TradingRules | null = savedRules ? JSON.parse(savedRules) : null;
  
  const apiKey = aiConfig.apiKey || process.env.API_KEY;
  if (!apiKey) {
    return {
      title: "AI 연결 필요",
      content: "설정 화면에서 Gemini API Key를 입력해주세요.",
      sentiment: "warning",
      topSector: "연결 대기",
      actionItems: ["설정 메뉴 이동", "API Key 입력", "저장"],
      marketPhase: "설정 미완료"
    };
  }

  const ai = new GoogleGenAI({ apiKey });
  const modelName = 'gemini-3-pro-preview';
  
  const summaryContext = stocks.map(s => 
    `종목: ${s.name}(${s.symbol}), RS: ${s.rsScore}, VCP상태: ${s.vcpRatio.toFixed(2)}, 섹터: ${s.sector}, Stage2: ${s.isStage2}`
  ).join('\n');

  // 현재 설정된 탐색 룰 정보를 AI에게 전달하여 문맥 파악 도움
  const ruleContext = rules ? `
[현재 적용 중인 스크리너 룰]
- 최소 RS 점수: ${rules.screener.minRSScore}
- 52주 저점 대비 상승폭: ${rules.screener.minDistanceLow52w}% 이상
- 52주 고점 대비 거리: ${rules.screener.maxDistanceHigh52w}% 이내
- VCP 수축 임계값: ${rules.screener.vcpTightnessThreshold}%
  ` : "기본 미너비니 템플릿 적용 중";

  const finalPrompt = `
    ${aiConfig.systemPrompt || DEFAULT_PROMPT}

    ${ruleContext}

    [대상 데이터]
    ${summaryContext}

    반드시 다음 구조의 JSON으로 응답하십시오:
    {
      "title": "string",
      "content": "string",
      "sentiment": "bullish" | "bearish" | "neutral" | "warning",
      "topSector": "string",
      "actionItems": ["string", "string", "string"],
      "marketPhase": "string"
    }
  `;

  try {
    const response = await ai.models.generateContent({
      model: modelName,
      contents: finalPrompt,
      config: {
        responseMimeType: "application/json",
        responseSchema: {
          type: Type.OBJECT,
          properties: {
            title: { type: Type.STRING },
            content: { type: Type.STRING },
            sentiment: { type: Type.STRING },
            topSector: { type: Type.STRING },
            actionItems: { 
              type: Type.ARRAY,
              items: { type: Type.STRING }
            },
            marketPhase: { type: Type.STRING }
          },
          required: ["title", "content", "sentiment", "topSector", "actionItems", "marketPhase"]
        }
      }
    });

    const data = JSON.parse(response.text || '{}');
    return {
      title: data.title || "전략 집행 리포트",
      content: data.content || "분석 결과를 생성할 수 없습니다.",
      sentiment: (data.sentiment as any) || "neutral",
      topSector: data.topSector || "분석 실패",
      actionItems: data.actionItems || [],
      marketPhase: data.marketPhase || "불명"
    };
  } catch (error: any) {
    const errorMessage = error?.message || String(error);
    const isQuotaError = errorMessage.includes("429") || errorMessage.includes("RESOURCE_EXHAUSTED");

    if (isQuotaError) {
      return {
        title: "API 할당량 초과",
        content: "API 키 할당량이 소진되었습니다. 잠시 후 시도하거나 키를 변경하세요.",
        sentiment: "warning",
        topSector: "Quota Full",
        actionItems: ["60초 대기", "API Key 확인", "새로고침"],
        marketPhase: "제한됨",
        error: "QUOTA_EXHAUSTED"
      };
    }

    return {
      title: "통신 오류",
      content: "AI 엔진 연결 실패",
      sentiment: "warning",
      topSector: "N/A",
      actionItems: ["연결 확인", "재시도"],
      marketPhase: "Offline"
    };
  }
};
