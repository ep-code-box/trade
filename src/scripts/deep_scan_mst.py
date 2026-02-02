
import os
import re

def find_numbers_in_mst(file_path, code):
    if not os.path.exists(file_path): return
    with open(file_path, mode="r", encoding="cp949") as f:
        for line in f:
            if code in line:
                print(f"\n[{code}] 전체 데이터 (길이:{len(line)}):")
                print(line)
                # 숫자가 연속된 부분을 모두 찾아 위치와 함께 출력
                for m in re.finditer(r'\d+', line):
                    val = int(m.group())
                    if 100 < val < 100000: # 배당금 가능 범위
                        print(f"위치 {m.start():>3}~{m.end():>3}: 값 {val:>8}")

print("[KOSPI 숫자 필드 전수 조사]")
find_numbers_in_mst("kospi_code.mst", "005930") # 삼성전자
print("\n[현대차 조사]")
find_numbers_in_mst("kospi_code.mst", "005380") # 현대차

