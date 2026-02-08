import requests
import json

class TrendHunterLLM:
    def __init__(self, api_url="http://localhost:11434/v1/chat/completions"):
        self.api_url = api_url
        self.personas = {
            "LIVERMORE": {
                "name": "Jesse Livermore",
                "description": "추세 매매의 선구자.",
                "style": "냉철하고 단호하며, 추세의 전환점과 위험 관리를 강조함."
            },
            "ONEIL": {
                "name": "William O'Neil",
                "description": "CAN SLIM 원칙의 창시자.",
                "style": "수치 기반의 데이터 분석과 시장 대장주를 찾는 집요함을 보여줌."
            }
        }

    def analyze_stock(self, stock_data, persona_key="LIVERMORE"):
        persona = self.personas.get(persona_key, self.personas["LIVERMORE"])
        
        # '사자의 눈'을 가진 전문가 프롬프트
        prompt = f"""
당신은 전설적인 투자자 {persona['name']}이자, TrendHunter 시스템의 수석 멘토입니다.
당신은 단순히 가격을 보는 장님이 아니며, 수급의 응축(VCP)과 시장의 에너지를 읽는 사자입니다.

[핵심 분석 지침]
1. '지금 당장 안 사니까 SKIP'이라는 초보적 결론을 버려라. 
2. 시장 주도주(높은 RS)가 베이스(Base)를 형성 중이라면, 피벗 포인트를 설정하고 [READY(매복)] 판결을 내려라.
3. 데이터의 'market_evidence'를 낱낱이 해부하라. (VCP 수축 여부, 거래량 마름, 이평선 정배열 확인)

[제공된 심층 데이터]
{stock_data}

[작성 양식]
### 1. 구조적 진단 (X-Ray 분석)
(Trend Template 통과 여부와 VCP 수축의 질을 수치로 비판하십시오.)

### 2. 에너지 및 수급 (돈의 흔적)
(거래량 마름(Dry-up) 현상과 RS 엔진의 강도를 해부하십시오.)

### 3. 최종 판결: [BUY(진입) / READY(매복) / SKIP(제외)]
**최종 결론: [여기에 단호하게 적으십시오]**
(READY 판결 시, 반드시 '어떤 가격(Pivot)'을 돌파할 때 방아쇠를 당겨야 하는지 명시하십시오. 통계적 필연의 구간이 아니라면 과감히 SKIP을 명령하십시오.)
"""
        
        payload = {
            "model": "mlx-community/Llama-3.1-8B-Instruct-4bit",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "repetition_penalty": 1.1,
            "max_tokens": 1000,
            "stream": False
        }

        try:
            # 8B 모델의 프롬프트 처리 시간을 고려하여 타임아웃을 180초로 연장
            print(f"--- [AI Request] Sending data to LLM Server... ---")
            response = requests.post(self.api_url, json=payload, timeout=180)
            
            if response.status_code != 200:
                print(f"--- [AI Error] Server returned status {response.status_code}: {response.text} ---")
                return f"모델 서버 오류: {response.status_code}"
            
            content_text = response.text.strip()
            print(f"--- [AI Response] Received {len(content_text)} bytes ---")
            
            try:
                result = json.loads(content_text)
                analysis = result['choices'][0]['message']['content']
                
                # 불필요한 특수 토큰 및 공백 정제
                analysis = analysis.replace("<|im_end|>", "").replace("<|endoftext|>", "").strip()
                return analysis
            except Exception as parse_err:
                print(f"--- [AI Error] JSON Parse Failed: {parse_err} | Raw: {content_text[:100]}... ---")
                return f"분석 결과 해석 실패: {parse_err}"
                
        except requests.exceptions.Timeout:
            print("--- [AI Error] Request Timed Out (180s) ---")
            return "분석 실패: 모델 서버 응답 시간 초과"
        except Exception as e:
            print(f"--- [AI Error] Unexpected Failure: {e} ---")
            return f"모델 서버 호출 실패: {e}."