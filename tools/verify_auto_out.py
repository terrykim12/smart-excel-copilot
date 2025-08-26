#!/usr/bin/env python3
"""
피벗 결과 검증 스크립트
CLI로 생성된 피벗 결과를 확인하고 분석합니다.
"""

import pandas as pd
import json
import sys
from pathlib import Path

def verify_pivot_result(excel_path, sheet_name="피벗_결과"):
    """피벗 결과를 검증하고 분석합니다."""
    try:
        # Excel 파일 읽기
        df = pd.read_excel(excel_path, sheet_name=sheet_name)
        print(f"✅ 피벗 결과 로드 성공: {excel_path}")
        print(f"📊 피벗 형태: {df.shape[0]}행 x {df.shape[1]}컬럼")
        print(f"🏷️  컬럼: {list(df.columns)}")
        print()
        
        # 데이터 미리보기
        print("📋 데이터 미리보기:")
        print(df.head(10).to_string(index=False))
        print()
        
        # 월별 요약
        if '월' in df.columns:
            print("📅 월별 요약:")
            month_summary = df.groupby('월').agg({
                col: 'sum' for col in df.columns if col != '월'
            }).round(2)
            print(month_summary)
            print()
        
        # 카테고리별 요약
        if '카테고리' in df.columns:
            print("🏷️  카테고리별 요약:")
            cat_summary = df.groupby('카테고리').agg({
                col: 'sum' for col in df.columns if col not in ['월', '카테고리']
            }).round(2)
            print(cat_summary)
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return False

def main():
    if len(sys.argv) != 2:
        print("사용법: python tools/verify_auto_out.py <excel_file>")
        print("예시: python tools/verify_auto_out.py data/automation/auto_out.xlsx")
        sys.exit(1)
    
    excel_path = sys.argv[1]
    
    if not Path(excel_path).exists():
        print(f"❌ 파일을 찾을 수 없습니다: {excel_path}")
        sys.exit(1)
    
    print(f"🔍 피벗 결과 검증 중: {excel_path}")
    print("=" * 50)
    
    success = verify_pivot_result(excel_path)
    
    if success:
        print("✅ 검증 완료!")
    else:
        print("❌ 검증 실패!")
        sys.exit(1)

if __name__ == "__main__":
    main()
