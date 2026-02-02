
import unittest

def mock_calculate_dps(all_raw_data):
    summary = {}
    for item in all_raw_data:
        code = item.get("sht_cd", "").strip()
        base_dt = item.get("stck_dvdn_base_dt", "").strip()
        dps = int(item.get("per_sto_divi_amt", 0))
        
        if not code or not base_dt or dps <= 0: continue
        if code not in summary: summary[code] = {}
        
        # 중복 제거 핵심 로직
        if base_dt not in summary[code]:
            summary[code][base_dt] = dps
        else:
            summary[code][base_dt] = max(summary[code][base_dt], dps)
            
    result = {code: sum(dates.values()) for code, dates in summary.items()}
    return result

class TestDividendLogic(unittest.TestCase):
    def test_duplicate_base_date(self):
        # 동일한 날짜(20241231)에 공시가 두 번 올라온 경우 (중복)
        raw_data = [
            {"sht_cd": "005930", "stck_dvdn_base_dt": "20241231", "per_sto_divi_amt": 361},
            {"sht_cd": "005930", "stck_dvdn_base_dt": "20241231", "per_sto_divi_amt": 361},
            {"sht_cd": "005930", "stck_dvdn_base_dt": "20240930", "per_sto_divi_amt": 361},
        ]
        res = mock_calculate_dps(raw_data)
        # 361 * 2 = 722원이어야 함 (중복 하나 제거됨)
        self.assertEqual(res["005930"], 722)
        print(f"\n[테스트1 성공] 중복 제거 후 합산: {res['005930']}원 (예상치 722원)")

    def test_different_base_dates(self):
        # 서로 다른 분기 배당인 경우 (정상 합산)
        raw_data = [
            {"sht_cd": "038390", "stck_dvdn_base_dt": "20240630", "per_sto_divi_amt": 400},
            {"sht_cd": "038390", "stck_dvdn_base_dt": "20241231", "per_sto_divi_amt": 600},
        ]
        res = mock_calculate_dps(raw_data)
        self.assertEqual(res["038390"], 1000)
        print(f"[테스트2 성공] 분기 합산: {res['038390']}원 (예상치 1000원)")

if __name__ == "__main__":
    unittest.main()
