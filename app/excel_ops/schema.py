"""
스키마 정렬 모듈 (M1)
여러 데이터프레임의 스키마를 정렬하고 병합을 지원합니다.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union, Tuple
from difflib import SequenceMatcher
import re

def align_schemas(
    dataframes: List[pd.DataFrame],
    strategy: str = "auto",
    mapping: Optional[Dict[str, str]] = None,
    **kwargs
) -> List[pd.DataFrame]:
    """
    여러 데이터프레임의 스키마를 정렬합니다.
    
    Args:
        dataframes: 정렬할 데이터프레임 리스트
        strategy: 정렬 전략 ('auto', 'exact', 'fuzzy', 'manual')
        mapping: 수동 매핑 (열명: 대상열명)
        **kwargs: 전략별 추가 매개변수
        
    Returns:
        스키마가 정렬된 데이터프레임 리스트
    """
    if len(dataframes) < 2:
        return dataframes
    
    print(f"[schema] {len(dataframes)}개 데이터프레임의 스키마 정렬 시작")
    
    if strategy == "auto":
        return auto_align_schemas(dataframes, **kwargs)
    elif strategy == "exact":
        return exact_align_schemas(dataframes, **kwargs)
    elif strategy == "fuzzy":
        return fuzzy_align_schemas(dataframes, **kwargs)
    elif strategy == "manual":
        if mapping is None:
            print("[schema] 경고: 수동 정렬을 위해 mapping이 필요합니다.")
            return dataframes
        return manual_align_schemas(dataframes, mapping, **kwargs)
    else:
        print(f"[schema] 지원하지 않는 전략: {strategy}")
        return dataframes

def auto_align_schemas(
    dataframes: List[pd.DataFrame],
    similarity_threshold: float = 0.6
) -> List[pd.DataFrame]:
    """
    자동으로 스키마를 정렬합니다.
    """
    # 첫 번째 데이터프레임을 기준으로 설정
    reference_df = dataframes[0]
    reference_cols = reference_df.columns.tolist()
    
    aligned_dfs = [reference_df]
    
    for i, df in enumerate(dataframes[1:], 1):
        print(f"[schema] 데이터프레임 {i+1} 정렬 중...")
        
        # 유사도 기반 매핑
        mapping = suggest_column_mapping(reference_cols, df.columns, similarity_threshold)
        
        # 매핑된 열만 선택하고 순서 정렬
        aligned_df = align_dataframe_to_reference(df, reference_cols, mapping)
        aligned_dfs.append(aligned_df)
        
        print(f"[schema] 데이터프레임 {i+1} 정렬 완료: {len(df.columns)} → {len(aligned_df.columns)}열")
    
    return aligned_dfs

def exact_align_schemas(
    dataframes: List[pd.DataFrame],
    case_sensitive: bool = False
) -> List[pd.DataFrame]:
    """
    정확한 이름 매칭으로 스키마를 정렬합니다.
    """
    # 공통 열 찾기
    all_columns = [set(df.columns) for df in dataframes]
    common_columns = set.intersection(*all_columns)
    
    if not case_sensitive:
        # 대소문자 구분 없이 공통 열 찾기
        all_columns_lower = [set(col.lower() for col in df.columns) for df in dataframes]
        common_columns_lower = set.intersection(*all_columns_lower)
        
        # 원본 열명으로 변환
        common_columns = set()
        for col_lower in common_columns_lower:
            for col in dataframes[0].columns:
                if col.lower() == col_lower:
                    common_columns.add(col)
                    break
    
    print(f"[schema] 공통 열 {len(common_columns)}개 발견: {list(common_columns)}")
    
    # 공통 열만 선택하여 정렬
    aligned_dfs = []
    for df in dataframes:
        aligned_df = df[list(common_columns)]
        aligned_dfs.append(aligned_df)
    
    return aligned_dfs

def fuzzy_align_schemas(
    dataframes: List[pd.DataFrame],
    similarity_threshold: float = 0.7
) -> List[pd.DataFrame]:
    """
    퍼지 매칭으로 스키마를 정렬합니다.
    """
    # 첫 번째 데이터프레임을 기준으로 설정
    reference_df = dataframes[0]
    reference_cols = reference_df.columns.tolist()
    
    aligned_dfs = [reference_df]
    
    for i, df in enumerate(dataframes[1:], 1):
        print(f"[schema] 데이터프레임 {i+1} 퍼지 정렬 중...")
        
        # 유사도 기반 매핑
        mapping = suggest_column_mapping(reference_cols, df.columns, similarity_threshold)
        
        # 매핑된 열만 선택하고 순서 정렬
        aligned_df = align_dataframe_to_reference(df, reference_cols, mapping)
        aligned_dfs.append(aligned_df)
        
        print(f"[schema] 데이터프레임 {i+1} 퍼지 정렬 완료")
    
    return aligned_dfs

def manual_align_schemas(
    dataframes: List[pd.DataFrame],
    mapping: Dict[str, str]
) -> List[pd.DataFrame]:
    """
    수동 매핑으로 스키마를 정렬합니다.
    """
    # 첫 번째 데이터프레임을 기준으로 설정
    reference_df = dataframes[0]
    reference_cols = reference_df.columns.tolist()
    
    aligned_dfs = [reference_df]
    
    for i, df in enumerate(dataframes[1:], 1):
        print(f"[schema] 데이터프레임 {i+1} 수동 정렬 중...")
        
        # 수동 매핑 적용
        aligned_df = align_dataframe_to_reference(df, reference_cols, mapping)
        aligned_dfs.append(aligned_df)
        
        print(f"[schema] 데이터프레임 {i+1} 수동 정렬 완료")
    
    return aligned_dfs

def suggest_column_mapping(
    reference_cols: List[str],
    target_cols: List[str],
    threshold: float = 0.6
) -> Dict[str, str]:
    """
    열명 매핑을 제안합니다.
    """
    mapping = {}
    
    for ref_col in reference_cols:
        best_match = None
        best_score = 0
        
        for target_col in target_cols:
            # 문자열 유사도 계산
            similarity = calculate_string_similarity(ref_col, target_col)
            
            if similarity > best_score and similarity >= threshold:
                best_score = similarity
                best_match = target_col
        
        if best_match:
            mapping[ref_col] = best_match
            print(f"[schema] 매핑 제안: '{ref_col}' → '{best_match}' (유사도: {best_score:.2f})")
    
    return mapping

def calculate_string_similarity(str1: str, str2: str) -> float:
    """
    두 문자열의 유사도를 계산합니다.
    """
    # 기본 문자열 유사도
    basic_similarity = SequenceMatcher(None, str1.lower(), str2.lower()).ratio()
    
    # 토큰 기반 유사도
    tokens1 = set(re.findall(r'\w+', str1.lower()))
    tokens2 = set(re.findall(r'\w+', str2.lower()))
    
    if not tokens1 or not tokens2:
        return basic_similarity
    
    token_similarity = len(tokens1.intersection(tokens2)) / len(tokens1.union(tokens2))
    
    # 가중 평균
    return 0.7 * basic_similarity + 0.3 * token_similarity

def align_dataframe_to_reference(
    df: pd.DataFrame,
    reference_cols: List[str],
    mapping: Dict[str, str]
) -> pd.DataFrame:
    """
    데이터프레임을 기준 스키마에 맞춰 정렬합니다.
    """
    aligned_df = pd.DataFrame()
    
    for ref_col in reference_cols:
        if ref_col in mapping:
            target_col = mapping[ref_col]
            if target_col in df.columns:
                aligned_df[ref_col] = df[target_col]
            else:
                # 매핑된 열이 없으면 NaN으로 채움
                aligned_df[ref_col] = pd.Series(dtype=df[target_col].dtype if target_col in df.columns else 'object')
        else:
            # 매핑이 없으면 NaN으로 채움
            aligned_df[ref_col] = pd.Series(dtype='object')
    
    return aligned_df

def merge_aligned_dataframes(
    dataframes: List[pd.DataFrame],
    how: str = "outer",
    **kwargs
) -> pd.DataFrame:
    """
    정렬된 데이터프레임들을 병합합니다.
    """
    if not dataframes:
        return pd.DataFrame()
    
    if len(dataframes) == 1:
        return dataframes[0]
    
    print(f"[schema] {len(dataframes)}개 데이터프레임 병합 시작")
    
    # 첫 번째 데이터프레임부터 순차적으로 병합
    merged_df = dataframes[0]
    
    for i, df in enumerate(dataframes[1:], 1):
        print(f"[schema] 데이터프레임 {i+1} 병합 중...")
        
        # 인덱스 리셋 후 병합
        merged_df = merged_df.reset_index(drop=True)
        df_reset = df.reset_index(drop=True)
        
        merged_df = pd.concat([merged_df, df_reset], ignore_index=True, **kwargs)
        
        print(f"[schema] 데이터프레임 {i+1} 병합 완료: 총 {len(merged_df)}행")
    
    print(f"[schema] 병합 완료: 최종 {len(merged_df)}행, {len(merged_df.columns)}열")
    
    return merged_df

def analyze_schema_compatibility(
    dataframes: List[pd.DataFrame]
) -> Dict[str, Any]:
    """
    여러 데이터프레임의 스키마 호환성을 분석합니다.
    """
    if len(dataframes) < 2:
        return {"compatible": True, "message": "분석할 데이터프레임이 부족합니다."}
    
    analysis = {
        "total_dataframes": len(dataframes),
        "column_counts": [len(df.columns) for df in dataframes],
        "row_counts": [len(df) for len in dataframes],
        "common_columns": [],
        "unique_columns": [],
        "compatibility_score": 0.0,
        "recommendations": []
    }
    
    # 모든 열명 수집
    all_columns = set()
    for df in dataframes:
        all_columns.update(df.columns)
    
    # 공통 열 찾기
    common_columns = set(dataframes[0].columns)
    for df in dataframes[1:]:
        common_columns = common_columns.intersection(set(df.columns))
    
    analysis["common_columns"] = list(common_columns)
    analysis["unique_columns"] = list(all_columns - common_columns)
    
    # 호환성 점수 계산
    if all_columns:
        analysis["compatibility_score"] = len(common_columns) / len(all_columns)
    
    # 권장사항 생성
    if analysis["compatibility_score"] < 0.5:
        analysis["recommendations"].append("스키마 호환성이 낮습니다. 수동 매핑을 고려하세요.")
    
    if len(common_columns) == 0:
        analysis["recommendations"].append("공통 열이 없습니다. 열명을 표준화하거나 수동 매핑이 필요합니다.")
    
    if len(common_columns) > 0:
        analysis["recommendations"].append(f"공통 열 {len(common_columns)}개로 병합 가능합니다.")
    
    return analysis
