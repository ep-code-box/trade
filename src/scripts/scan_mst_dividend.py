
import os

def scan_samsung_dividend(file_path, target_values):
    if not os.path.exists(file_path):
        return
    
    with open(file_path, mode="r", encoding="cp949") as f:
        for line in f:
            if "005930" in line: # 삼성전자
                print(f"--- 삼성전자 원시 데이터 스캔 (길이: {len(line)}) ---")
                # 10자 단위로 잘라서 출력하며 타겟 값 탐색
                for i in range(0, len(line), 1):
                    chunk = line[i:i+10]
                    for target in target_values:
                        if str(target) in chunk:
                            print(f"포착! 위치 {i} 근처: '{chunk}' (타겟: {target})")
                break

print("[KOSPI 스캔 시작]")
# 삼성전자의 최근 배당금 후보군: 1444(연간), 361(분기), 1503(특별포함) 등
scan_samsung_dividend("kospi_code.mst", [1444, 361, 1503, 1668])
