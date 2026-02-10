"""
TrendHunter 지능형 패턴 분석 모듈
[Constitution 6.A] Atomic Logic 적용: 캔들 및 차트 패턴 전담
"""
import pandas as pd

def check_candle_pattern(row):
    """망치형 및 상승장악형 패턴 체크"""
    if not row.get('open') or not row.get('close'): return None
    
    body = abs(row['close'] - row['open'])
    upper_shadow = row['high'] - max(row['open'], row['close'])
    lower_shadow = min(row['open'], row['close']) - row['low']
    
    # 1. 망치형 (Hammer): 하락 추세 끝이나 눌림목에서 유효
    if body > 0 and lower_shadow >= body * 1.5 and upper_shadow <= body * 0.5 and row['close'] > row['open']:
        return "🔨HAMMER"
        
    return None

def is_vcp_tight(vcp_score, rs_master):
    """미너비니의 VCP 응축 기준 검증 (RS 점수에 따른 가변 필터)"""
    if rs_master >= 96:
        return round(vcp_score, 3) <= 0.06 # 괴물주는 6%까지 허용
    return round(vcp_score, 3) <= 0.04     # 일반 주도주는 4% 이내 엄격 적용
