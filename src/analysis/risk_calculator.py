"""초결벽주의 리스크 관리 계산기: 원금 대비 1% 손실 제한 매수 수량 산출."""

def calculate_position_size(total_equity, entry_price, stop_loss_price, risk_pct=0.01):
    """
    total_equity: 계좌 총 자산
    entry_price: 매수 진입가
    stop_loss_price: 손절가
    risk_pct: 원금 대비 허용 손실 (기본 1%)
    """
    if entry_price <= stop_loss_price:
        return 0, 0, 0
    
    # 1. 이번 매매에서 잃어도 되는 최대 금액 (원금의 1%)
    max_risk_amount = total_equity * risk_pct
    
    # 2. 주당 예상 손실액
    loss_per_share = entry_price - stop_loss_price
    
    # 3. 매수 가능 수량 (최대 손실액 / 주당 손실액)
    quantity = int(max_risk_amount / loss_per_share)
    
    # 4. 총 투입 금액
    position_value = quantity * entry_price
    
    return quantity, position_value, max_risk_amount

def print_risk_guide(name, total_equity, entry_price, stop_loss_price):
    qty, val, risk_amt = calculate_position_size(total_equity, entry_price, stop_loss_price)
    
    print(f"\n[🛡️ {name} 리스크 관리 가이드]")
    print(f" - 계좌 원금: {total_equity:,}원 | 허용 손실(1%): {risk_amt:,}원")
    print(f" - 진입가: {entry_price:,}원 | 손절가: {stop_loss_price:,}원")
    print(f" --------------------------------------------------")
    if qty > 0:
        print(f" 🔥 권장 매수 수량: {qty:,}주")
        print(f" 💰 총 투입 금액:   {val:,}원 (비중: {val/total_equity*100:.1f}%)")
    else:
        print(" ❌ 경고: 손절폭이 너무 커서 1% 원칙으로는 매수가 불가능합니다.")
    print(f" --------------------------------------------------")

if __name__ == "__main__":
    # 샘플 테스트 (원금 1억 기준)
    print_risk_guide("나노엔텍", 100000000, 5160, 4750)
