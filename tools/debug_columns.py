#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
컬럼 중복 및 타입 진단 스크립트
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd
from app.io.loader import load_table, detect_encoding

def debug_columns(file_path: str, sheet=None):
    """파일의 컬럼 상태를 진단"""
    print(f"=== 컬럼 진단: {file_path} ===")
    
    # 파일 로드
    enc = detect_encoding(file_path)
    df, meta = load_table(file_path, sheet=sheet, encoding=enc.get("encoding"))
    
    print(f"Shape: {df.shape}")
    print(f"컬럼 목록: {df.columns.tolist()}")
    print(f"컬럼 타입: {df.columns.dtype}")
    print(f"중복 컬럼 존재: {df.columns.duplicated().any()}")
    
    if df.columns.duplicated().any():
        print("중복된 컬럼:")
        for col in df.columns[df.columns.duplicated()]:
            print(f"  - {col}")
    
    # '월' 컬럼 특별 체크
    if '월' in df.columns:
        print(f"\n'월' 컬럼 타입: {type(df['월'])}")
        if not isinstance(df['월'], pd.Series):
            print(f"  '월' 컬럼이 Series가 아님! Shape: {df['월'].shape}")
            print(f"  첫 번째 열만 사용: {df['월'].iloc[:, 0]}")
    
    # 날짜 후보 컬럼들 체크
    date_candidates = ['주문일', 'order_date', 'date', '날짜']
    print(f"\n날짜 후보 컬럼들:")
    for cand in date_candidates:
        if cand in df.columns:
            print(f"  - {cand}: {type(df[cand])}, 샘플: {df[cand].iloc[0] if len(df) > 0 else 'N/A'}")
    
    return df

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python tools/debug_columns.py <파일경로> [시트명]")
        sys.exit(1)
    
    file_path = sys.argv[1]
    sheet = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        df = debug_columns(file_path, sheet)
    except Exception as e:
        print(f"오류: {e}")
        import traceback
        traceback.print_exc()
