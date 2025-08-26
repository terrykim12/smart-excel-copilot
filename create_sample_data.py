#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
테스트용 샘플 데이터 생성
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def create_sample_data():
    """테스트용 샘플 데이터 생성"""
    np.random.seed(42)
    
    # 기본 데이터
    n_rows = 100
    
    # 날짜 범위
    start_date = datetime(2024, 1, 1)
    dates = [start_date + timedelta(days=i) for i in range(n_rows)]
    
    # 카테고리
    categories = ['전자제품', '의류', '식품', '도서', '스포츠용품']
    
    # 도시
    cities = ['서울', '부산', '대구', '인천', '광주']
    
    # 데이터 생성
    data = {
        '거래ID': [f'T{i:03d}' for i in range(1, n_rows + 1)],
        '주문일': [d.strftime('%Y-%m-%d') for d in dates],
        '카테고리': np.random.choice(categories, n_rows),
        '도시': np.random.choice(cities, n_rows),
        '금액': np.random.randint(1000, 100000, n_rows),
        '수량': np.random.randint(1, 10, n_rows),
        '월': [d.strftime('%Y-%m') for d in dates]
    }
    
    df = pd.DataFrame(data)
    
    # 저장
    output_path = 'data/automation/sample_large.csv'
    df.to_csv(output_path, index=False, encoding='utf-8')
    
    print(f"샘플 데이터 생성 완료: {output_path}")
    print(f"Shape: {df.shape}")
    print(f"컬럼: {list(df.columns)}")
    print("\n처음 5행:")
    print(df.head())
    
    return df

if __name__ == "__main__":
    create_sample_data()
