#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time, json, pathlib
import pandas as pd
from numpy.random import default_rng
from app.report.template import build_report

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "logs" / "perf"
OUT.mkdir(parents=True, exist_ok=True)

def synth(n=500_000, seed=42):
    """50만 행 합성 데이터 생성"""
    rng = default_rng(seed)
    dates = pd.date_range("2024-01-01", periods=200, freq="D")
    
    df = pd.DataFrame({
        "거래ID": rng.integers(0, n//2, size=n),
        "주문일": rng.choice(dates, size=n).astype(str),
        "카테고리": rng.choice(["A", "B", "C", "D"], size=n),
        "도시": rng.choice(["서울", "부산", "대구", "인천"], size=n),
        "금액": rng.integers(1000, 500000, size=n),
        "수량": rng.integers(1, 10, size=n),
    })
    
    return df

def main():
    """메인 실행 함수"""
    print("=== 50만 행 스트레스 테스트 시작 ===")
    
    # 1. 합성 데이터 생성
    t0 = time.perf_counter()
    df = synth()
    t1 = time.perf_counter()
    
    print(f"✅ 합성 데이터 생성 완료: {len(df):,}행 x {len(df.columns)}열")
    print(f"데이터 생성 시간: {t1-t0:.3f}초")
    
    # 2. 보고서 생성
    print("📊 보고서 생성 중...")
    t2 = time.perf_counter()
    
    rep = build_report(
        df, 
        str(ROOT/"data/report/stress_500k.xlsx"),
        title="50만 행 스트레스 테스트 보고서",
        period="2024-01-01 ~ 2024-07-20",
        owner="Stress Test Tool",
        rows=["주문일", "카테고리"],
        values=[("금액", "sum"), ("수량", "sum")],
        chart_type="bar"
    )
    
    t3 = time.perf_counter()
    
    print(f"✅ 보고서 생성 완료: {rep['out']}")
    print(f"보고서 생성 시간: {t3-t2:.3f}초")
    
    # 3. 성능 결과 정리
    out = {
        "rows": len(df),
        "columns": len(df.columns),
        "t_generate_s": round(t1-t0, 3),
        "t_report_s": round(t3-t2, 3),
        "t_total_s": round(t3-t0, 3),
        "pivot_shape": rep["pivot_shape"],
        "output_file": rep["out"],
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # 4. 로그 파일 저장
    p = OUT / f"stress_{int(time.time())}.json"
    p.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    
    print(f"\n📈 성능 결과:")
    print(f"  - 데이터 생성: {out['t_generate_s']}초")
    print(f"  - 보고서 생성: {out['t_report_s']}초")
    print(f"  - 총 소요시간: {out['t_total_s']}초")
    print(f"  - 피벗 형태: {out['pivot_shape']}")
    print(f"  - 로그 저장: {p}")
    
    return out

if __name__ == "__main__":
    try:
        result = main()
        print(f"\n🎉 스트레스 테스트 완료!")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"\n💥 스트레스 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
