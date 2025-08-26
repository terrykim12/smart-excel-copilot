"""
이상치 처리 모듈 (M1)
다양한 방법으로 이상치를 탐지하고 처리합니다.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union, Tuple, Iterable
from enum import Enum
import warnings

class OutlierMethod(Enum):
    """이상치 탐지 방법"""
    IQR = "iqr"
    ZSCORE = "zscore"
    ISOLATION_FOREST = "isolation_forest"
    LOF = "lof"
    MANUAL = "manual"

class OutlierAction(Enum):
    """이상치 처리 방법"""
    CLIP = "clip"
    REMOVE = "remove"
    WINSORIZE = "winsorize"
    MARK = "mark"

def detect_outliers(
    df: pd.DataFrame,
    columns: Optional[List[str]] = None,
    method: str = "iqr",
    **kwargs
) -> Dict[str, Any]:
    """
    이상치를 탐지합니다.
    
    Args:
        df: 분석할 데이터프레임
        columns: 분석할 열 (None이면 모든 숫자형 열)
        method: 탐지 방법
        **kwargs: 방법별 추가 매개변수
        
    Returns:
        이상치 탐지 결과
    """
    if columns is None:
        columns = df.select_dtypes(include=[np.number]).columns.tolist()
    
    results = {}
    
    for col in columns:
        if col not in df.columns:
            continue
            
        if not pd.api.types.is_numeric_dtype(df[col]):
            continue
            
        try:
            if method == OutlierMethod.IQR.value:
                outliers = detect_outliers_iqr(df[col], **kwargs)
            elif method == OutlierMethod.ZSCORE.value:
                outliers = detect_outliers_zscore(df[col], **kwargs)
            elif method == OutlierMethod.ISOLATION_FOREST.value:
                outliers = detect_outliers_isolation_forest(df[col], **kwargs)
            else:
                print(f"[outlier] 지원하지 않는 방법: {method}")
                continue
                
            results[col] = outliers
            
        except Exception as e:
            print(f"[outlier] 오류: '{col}' 열 분석 중 {e}")
            continue
    
    return results

def detect_outliers_iqr(
    series: pd.Series,
    multiplier: float = 1.5
) -> Dict[str, Any]:
    """
    IQR 방법으로 이상치를 탐지합니다.
    
    Args:
        series: 분석할 Series
        multiplier: IQR 배수 (기본값: 1.5)
        
    Returns:
        이상치 탐지 결과
    """
    Q1 = series.quantile(0.25)
    Q3 = series.quantile(0.75)
    IQR = Q3 - Q1
    
    lower_bound = Q1 - multiplier * IQR
    upper_bound = Q3 + multiplier * IQR
    
    outliers_mask = (series < lower_bound) | (series > upper_bound)
    outliers = series[outliers_mask]
    
    return {
        "method": "iqr",
        "lower_bound": lower_bound,
        "upper_bound": upper_bound,
        "iqr": IQR,
        "outlier_count": len(outliers),
        "outlier_indices": outliers.index.tolist(),
        "outlier_values": outliers.tolist(),
        "outlier_percentage": len(outliers) / len(series) * 100
    }

def detect_outliers_zscore(
    series: pd.Series,
    threshold: float = 3.0
) -> Dict[str, Any]:
    """
    Z-score 방법으로 이상치를 탐지합니다.
    
    Args:
        series: 분석할 Series
        threshold: Z-score 임계값 (기본값: 3.0)
        
    Returns:
        이상치 탐지 결과
    """
    z_scores = np.abs((series - series.mean()) / series.std())
    outliers_mask = z_scores > threshold
    outliers = series[outliers_mask]
    
    return {
        "method": "zscore",
        "threshold": threshold,
        "outlier_count": len(outliers),
        "outlier_indices": outliers.index.tolist(),
        "outlier_values": outliers.tolist(),
        "outlier_percentage": len(outliers) / len(series) * 100,
        "max_zscore": float(z_scores.max())
    }

def detect_outliers_isolation_forest(
    series: pd.Series,
    contamination: float = 0.1
) -> Dict[str, Any]:
    """
    Isolation Forest 방법으로 이상치를 탐지합니다.
    
    Args:
        series: 분석할 Series
        contamination: 이상치 비율 추정치
        
    Returns:
        이상치 탐지 결과
    """
    try:
        from sklearn.ensemble import IsolationForest
        
        # 2D 배열로 변환
        X = series.values.reshape(-1, 1)
        
        # Isolation Forest 모델 학습
        iso_forest = IsolationForest(contamination=contamination, random_state=42)
        predictions = iso_forest.fit_predict(X)
        
        # -1이 이상치
        outliers_mask = predictions == -1
        outliers = series[outliers_mask]
        
        return {
            "method": "isolation_forest",
            "contamination": contamination,
            "outlier_count": len(outliers),
            "outlier_indices": outliers.index.tolist(),
            "outlier_values": outliers.tolist(),
            "outlier_percentage": len(outliers) / len(series) * 100
        }
        
    except ImportError:
        print("[outlier] 경고: scikit-learn이 설치되지 않아 Isolation Forest를 사용할 수 없습니다.")
        return detect_outliers_iqr(series)

def handle_outliers(
    df: pd.DataFrame,
    outlier_info: Dict[str, Any],
    action: str = "clip",
    **kwargs
) -> pd.DataFrame:
    """
    탐지된 이상치를 처리합니다.
    
    Args:
        df: 처리할 데이터프레임
        outlier_info: 이상치 탐지 결과
        action: 처리 방법
        **kwargs: 방법별 추가 매개변수
        
    Returns:
        이상치가 처리된 데이터프레임
    """
    df_cleaned = df.copy()
    
    for col, info in outlier_info.items():
        if col not in df_cleaned.columns:
            continue
            
        try:
            if action == OutlierAction.CLIP.value:
                df_cleaned[col] = clip_outliers(df_cleaned[col], info)
            elif action == OutlierAction.REMOVE.value:
                df_cleaned = remove_outliers(df_cleaned, col, info)
            elif action == OutlierAction.WINSORIZE.value:
                df_cleaned[col] = winsorize_outliers(df_cleaned[col], info)
            elif action == OutlierAction.MARK.value:
                df_cleaned[f"{col}_is_outlier"] = mark_outliers(df_cleaned[col], info)
            else:
                print(f"[outlier] 지원하지 않는 처리 방법: {action}")
                continue
                
            print(f"[outlier] '{col}' 열: {action} 방법으로 {info['outlier_count']}개 이상치 처리")
            
        except Exception as e:
            print(f"[outlier] 오류: '{col}' 열 처리 중 {e}")
            continue
    
    return df_cleaned

def clip_outliers(
    series: pd.Series,
    outlier_info: Dict[str, Any]
) -> pd.Series:
    """이상치를 경계값으로 클리핑합니다."""
    if outlier_info["method"] == "iqr":
        lower_bound = outlier_info["lower_bound"]
        upper_bound = outlier_info["upper_bound"]
        return series.clip(lower=lower_bound, upper=upper_bound)
    else:
        # 다른 방법의 경우 IQR로 재계산
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        return series.clip(lower=lower_bound, upper=upper_bound)

def remove_outliers(
    df: pd.DataFrame,
    col: str,
    outlier_info: Dict[str, Any]
) -> pd.DataFrame:
    """이상치가 포함된 행을 제거합니다."""
    outlier_indices = outlier_info["outlier_indices"]
    return df.drop(index=outlier_indices)

def winsorize_outliers(
    series: pd.Series,
    outlier_info: Dict[str, Any],
    limits: Tuple[float, float] = (0.05, 0.05)
) -> pd.Series:
    """이상치를 Winsorize 방법으로 처리합니다."""
    try:
        from scipy.stats.mstats import winsorize
        return pd.Series(winsorize(series, limits=limits), index=series.index)
    except ImportError:
        print("[outlier] 경고: scipy가 설치되지 않아 Winsorize를 사용할 수 없습니다.")
        return clip_outliers(series, outlier_info)

def mark_outliers(
    series: pd.Series,
    outlier_info: Dict[str, Any]
) -> pd.Series:
    """이상치 여부를 표시하는 불리언 Series를 반환합니다."""
    outlier_mask = pd.Series(False, index=series.index)
    outlier_mask.loc[outlier_info["outlier_indices"]] = True
    return outlier_mask

def get_outlier_summary(df: pd.DataFrame, outlier_info: Dict[str, Any]) -> Dict[str, Any]:
    """이상치 처리 요약을 반환합니다."""
    total_outliers = sum(info["outlier_count"] for info in outlier_info.values())
    total_rows = len(df)
    
    summary = {
        "total_rows": total_rows,
        "columns_with_outliers": len(outlier_info),
        "total_outliers": total_outliers,
        "outlier_percentage": total_outliers / total_rows * 100,
        "column_details": {}
    }
    
    for col, info in outlier_info.items():
        summary["column_details"][col] = {
            "outlier_count": info["outlier_count"],
            "outlier_percentage": info["outlier_percentage"],
            "method": info["method"]
        }
    
    return summary

def iqr_clip_series(s: pd.Series, k: float = 1.5) -> Tuple[pd.Series, Dict[str, float]]:
    q1 = s.quantile(0.25); q3 = s.quantile(0.75); iqr = q3 - q1
    lo = q1 - k * iqr; hi = q3 + k * iqr
    return s.clip(lower=lo, upper=hi), {"q1": float(q1), "q3": float(q3), "lo": float(lo), "hi": float(hi)}

def outlier(df: pd.DataFrame, rules: Iterable[Dict[str, Any]]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    rules: [{"col":"금액","method":"iqr_clip","k":1.5}, {"col":"수량","method":"zscore_clip","z":3}, ...]
    """
    out = df.copy()
    rep: List[Dict[str, Any]] = []
    for r in rules or []:
        col = r.get("col"); method = (r.get("method") or "").lower()
        if col not in out.columns: 
            rep.append({"col":col,"method":method,"status":"skip:not_found"}); 
            continue
        if method in ("iqr","iqr_clip"):
            s = pd.to_numeric(out[col], errors="coerce")
            s2, stats = iqr_clip_series(s, float(r.get("k", 1.5)))
            n_changed = int(((s2 != s) & s.notna()).sum())
            out[col] = s2
            rep.append({"col":col,"method":"iqr_clip","changed":n_changed, **stats, "status":"ok"})
        elif method in ("z","zscore","zscore_clip"):
            s = pd.to_numeric(out[col], errors="coerce")
            mu, sd = float(s.mean()), float(s.std(ddof=0))
            z = float(r.get("z", 3.0))
            lo, hi = mu - z*sd, mu + z*sd
            s2 = s.clip(lo, hi)
            n_changed = int(((s2 != s) & s.notna()).sum())
            out[col] = s2
            rep.append({"col":col,"method":"zscore_clip","changed":n_changed,"lo":lo,"hi":hi,"status":"ok"})
        else:
            rep.append({"col":col,"method":method,"status":"skip:unknown_method"})
    return out, {"outlier": rep}
