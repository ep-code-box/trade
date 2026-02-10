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
        """로컬 상주 서버(Llama-3.1-8B)를 통한 폴백 분석 실행"""
        persona = self.personas.get(persona_key, self.personas["LIVERMORE"])
        
        # 사자의 눈 (Lion's Eye) 프롬프트 - 8B 모델 최적화
        prompt = f"""
당신은 전설적인 투자자 {persona['name']}이자, TrendHunter 시스템의 수석 멘토입니다.
당신은 수급의 응축(VCP)과 시장의 에너지를 읽어내는 사자입니다.

[분석 대상 데이터]
{stock_data}

[작성 가이드]
1. 완벽한 구조(VCP 수축 및 정배열)가 아니면 무조건 [SKIP] 혹은 [READY] 하십시오.
2. 각 항목 뒤에는 반드시 줄바꿈(\\n\\n)을 넣어 가독성을 확보하십시오.
3. 최종 판결은 [BUY(진입) / READY(매복) / SKIP(제외)] 중 하나로 단호하게 내리십시오.
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
            # 로컬 추론 부하를 고려하여 타임아웃 180초 설정
            response = requests.post(self.api_url, json=payload, timeout=180)
            if response.status_code != 200:
                return f"로컬 모델 서버 오류: {response.status_code}"
            
            content_text = response.text.strip()
            result = json.loads(content_text)
            analysis = result['choices'][0]['message']['content']
            
            # 특수 토큰 정제
            analysis = analysis.replace("<|im_end|>", "").replace("<|endoftext|>", "").strip()
            return analysis
        except Exception as e:
            return f"로컬 분석 실패: {e}"