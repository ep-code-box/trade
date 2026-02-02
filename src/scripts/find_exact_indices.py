
import os

def find_exact_offsets(file_path, code, target_val):
    if not os.path.exists(file_path): return
    with open(file_path, mode="rb") as f:
        for line in f:
            if code.encode() in line:
                val_str = str(target_val).encode()
                pos = line.find(val_str)
                print(f"[{code}] 값 '{target_val}'의 바이트 위치: {pos}")
                return pos

print("--- KOSPI 단위/위치 검증 ---")
# 삼성전자 상장주수: 5919637 (천주), ROE: 8.37
find_exact_offsets("kospi_code.mst", "005930", 5919637)
find_exact_offsets("kospi_code.mst", "005930", "8.37")

print("\n--- KOSDAQ 단위/위치 검증 ---")
# 에코프로비엠 상장주수: 97801 (천주), ROE: 3.00 (202509 기준)
find_exact_offsets("kosdaq_code.mst", "247540", 97801)
find_exact_offsets("kosdaq_code.mst", "247540", "3.00")
