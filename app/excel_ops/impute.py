"""
결측치 처리 모듈 (M1)
다양한 전략을 사용하여 결측치를 처리합니다.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union, Iterable, Tuple
from enum import Enum

class ImputeStrategy(Enum):
    """결측치 처리 전략"""
    ZERO = "zero"
    MEAN = "mean"
    MEDIAN = "median"
    MODE = "mode"
    FORWARD_FILL = "forward_fill"
    BACKWARD_FILL = "backward_fill"
    INTERPOLATE = "interpolate"
    DROP = "drop"

def handle_missing_values(
    df: pd.DataFrame,
    strategies: Dict[str, Union[str, Dict[str, Any]]],
    drop_threshold: float = 0.5
) -> pd.DataFrame:
    """
    결측치를 지정된 전략에 따라 처리합니다.
    
    Args:
        df: 처리할 데이터프레임
        strategies: 열별 처리 전략
            - 문자열: 전략 이름 (예: "mean", "median")
            - 딕셔너리: 상세 설정 (예: {"strategy": "mean", "fill_value": 0})
        drop_threshold: 열의 결측치 비율이 이 값을 초과하면 열을 삭제
        
    Returns:
        결측치가 처리된 데이터프레임
    """
    df_cleaned = df.copy()
    
    # 결측치 비율이 높은 열 삭제
    missing_ratio = df_cleaned.isnull().sum() / len(df_cleaned)
    cols_to_drop = missing_ratio[missing_ratio > drop_threshold].index.tolist()
    
    if cols_to_drop:
        print(f"[impute] 결측치 비율이 높은 열 삭제: {cols_to_drop}")
        df_cleaned = df_cleaned.drop(columns=cols_to_drop)
    
    # 열별 전략 적용
    for col, strategy in strategies.items():
        if col not in df_cleaned.columns:
            print(f"[impute] 경고: 열 '{col}'을 찾을 수 없습니다.")
            continue
            
        if isinstance(strategy, str):
            strategy_config = {"strategy": strategy}
        else:
            strategy_config = strategy
            
        df_cleaned = apply_impute_strategy(df_cleaned, col, strategy_config)
    
    return df_cleaned

def apply_impute_strategy(
    df: pd.DataFrame,
    col: str,
    config: Dict[str, Any]
) -> pd.DataFrame:
    """
    특정 열에 결측치 처리 전략을 적용합니다.
    
    Args:
        df: 데이터프레임
        col: 처리할 열
        config: 전략 설정
        
    Returns:
        처리된 데이터프레임
    """
    strategy = config.get("strategy", "mean")
    fill_value = config.get("fill_value", None)
    
    if df[col].isnull().sum() == 0:
        return df
    
    before_count = df[col].isnull().sum()
    
    try:
        if strategy == ImputeStrategy.ZERO.value:
            df[col] = df[col].fillna(0)
        elif strategy == ImputeStrategy.MEAN.value:
            if pd.api.types.is_numeric_dtype(df[col]):
                df[col] = df[col].fillna(df[col].mean())
            else:
                print(f"[impute] 경고: '{col}' 열은 숫자형이 아니므로 평균 대체를 건너뜁니다.")
        elif strategy == ImputeStrategy.MEDIAN.value:
            if pd.api.types.is_numeric_dtype(df[col]):
                df[col] = df[col].fillna(df[col].median())
            else:
                print(f"[impute] 경고: '{col}' 열은 숫자형이 아니므로 중앙값 대체를 건너뜁니다.")
        elif strategy == ImputeStrategy.MODE.value:
            mode_value = df[col].mode()
            if len(mode_value) > 0:
                df[col] = df[col].fillna(mode_value[0])
        elif strategy == ImputeStrategy.FORWARD_FILL.value:
            df[col] = df[col].fillna(method='ffill')
        elif strategy == ImputeStrategy.BACKWARD_FILL.value:
            df[col] = df[col].fillna(method='bfill')
        elif strategy == ImputeStrategy.INTERPOLATE.value:
            if pd.api.types.is_numeric_dtype(df[col]):
                df[col] = df[col].interpolate(method='linear')
            else:
                print(f"[impute] 경고: '{col}' 열은 숫자형이 아니므로 보간을 건너뜁니다.")
        elif strategy == ImputeStrategy.DROP.value:
            df = df.dropna(subset=[col])
        else:
            if fill_value is not None:
                df[col] = df[col].fillna(fill_value)
            else:
                print(f"[impute] 경고: 알 수 없는 전략 '{strategy}'")
                return df
        
        after_count = df[col].isnull().sum()
        filled_count = before_count - after_count
        
        if filled_count > 0:
            print(f"[impute] '{col}' 열: {strategy} 전략으로 {filled_count}개 결측치 처리")
            
    except Exception as e:
        print(f"[impute] 오류: '{col}' 열 처리 중 {e}")
        return df
    
    return df

def analyze_missing_patterns(df: pd.DataFrame) -> Dict[str, Any]:
    """
    결측치 패턴을 분석합니다.
    
    Args:
        df: 분석할 데이터프레임
        
    Returns:
        결측치 분석 결과
    """
    missing_info = df.isnull().sum()
    missing_ratio = missing_info / len(df)
    
    # 결측치가 있는 열만 필터링
    cols_with_missing = missing_info[missing_info > 0]
    
    analysis = {
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "columns_with_missing": len(cols_with_missing),
        "missing_columns": cols_with_missing.to_dict(),
        "missing_ratio": missing_ratio.to_dict(),
        "missing_patterns": {}
    }
    
    # 결측치 패턴 분석 (예: 특정 행에만 결측치가 집중되어 있는지)
    if len(cols_with_missing) > 0:
        missing_rows = df[cols_with_missing.index].isnull().sum(axis=1)
        analysis["missing_patterns"]["rows_with_missing"] = {
            "count": int(missing_rows.sum()),
            "max_missing_in_row": int(missing_rows.max()),
            "avg_missing_in_row": float(missing_rows.mean())
        }
    
    return analysis

def suggest_impute_strategies(df: pd.DataFrame) -> Dict[str, str]:
    """
    각 열에 대한 결측치 처리 전략을 제안합니다.
    
    Args:
        df: 분석할 데이터프레임
        
    Returns:
        열별 제안 전략
    """
    suggestions = {}
    
    for col in df.columns:
        if df[col].isnull().sum() == 0:
            continue
            
        col_type = df[col].dtype
        
        if pd.api.types.is_numeric_dtype(col_type):
            # 숫자형: 중앙값 또는 평균
            if df[col].isnull().sum() < len(df) * 0.3:
                suggestions[col] = "median"
            else:
                suggestions[col] = "zero"
        elif pd.api.types.is_datetime64_any_dtype(col_type):
            # 날짜형: 보간 또는 forward fill
            suggestions[col] = "interpolate"
        else:
            # 범주형: 최빈값 또는 forward fill
            if df[col].isnull().sum() < len(df) * 0.5:
                suggestions[col] = "mode"
            else:
                suggestions[col] = "forward_fill"
    
    return suggestions

def impute(df: pd.DataFrame, rules: Iterable[Dict[str, Any]]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    rules: [{"col":"금액","method":"median"}, {"col":"수량","method":"zero"}, {"col":"메모","method":"value","value":""}, ...]
    return: (df_new, report)
    """
    out = df.copy()
    report: List[Dict[str, Any]] = []
    for r in rules or []:
        col = r.get("col")
        method = (r.get("method") or "").lower()
        if col not in out.columns: 
            report.append({"col": col, "method": method, "status": "skip:not_found"}); 
            continue
        s = out[col]
        n_before = int(s.isna().sum())
        if n_before == 0:
            report.append({"col": col, "method": method, "status": "noop"}); 
            continue

        if method in ("zero","0"):
            out[col] = s.fillna(0)
        elif method in ("mean","avg"):
            out[col] = s.fillna(s.astype("Float64").mean(skipna=True))
        elif method == "median":
            out[col] = s.fillna(s.astype("Float64").median(skipna=True))
        elif method in ("mode","most_frequent"):
            try:
                val = s.mode(dropna=True).iloc[0]
                out[col] = s.fillna(val)
            except Exception:
                out[col] = s
        elif method in ("ffill","forward_fill"):
            out[col] = s.fillna(method="ffill")
        elif method in ("bfill","backfill"):
            out[col] = s.fillna(method="bfill")
        elif method in ("value","const"):
            out[col] = s.fillna(r.get("value"))
        else:
            report.append({"col": col, "method": method, "status": "skip:unknown_method"}); 
            continue

        n_after = int(out[col].isna().sum())
        report.append({"col": col, "method": method, "filled": n_before - n_after, "status": "ok"})
    return out, {"impute": report}
