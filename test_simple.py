#!/usr/bin/env python3
"""간단한 테스트 스크립트"""

import sys
from pathlib import Path

# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

try:
    from app.io.loader import load_table
    from app.core.profile import profile_dataframe
    from app.excel_ops.clean import level1_clean
    from app.excel_ops.dedupe import dedupe
    
    print("모듈 임포트 성공!")
    
    # 파일 로드 테스트
    df = load_table('data/samples/transactions_utf8.csv')
    print(f"파일 로드 성공: {len(df)}행, {len(df.columns)}열")
    
    # 프로파일링 테스트
    prof = profile_dataframe(df, sample_rows=10000)
    print(f"프로파일링 성공: {len(prof['columns'])}개 열 분석")
    
    # 클리닝 테스트
    df2 = level1_clean(df, currency_split=True, date_fmt='YYYY-MM-DD', drop_empty_rows=True, drop_empty_cols=True)
    print(f"클리닝 성공: {len(df2)}행, {len(df2.columns)}열")
    
    # 중복 제거 테스트
    df3 = dedupe(df2, keys=['거래ID'], keep_policy='last_by:업데이트일')
    print(f"중복 제거 성공: {len(df3)}행")
    
    print("\n모든 테스트 통과! 🎉")
    
except Exception as e:
    print(f"오류 발생: {e}")
    import traceback
    traceback.print_exc()
