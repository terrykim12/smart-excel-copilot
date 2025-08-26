# app/excel_ops/outlier.py
from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, Iterable, List

def _to_numeric(s: pd.Series) -> pd.Series:
    """안전한 숫자 변환 - Int64 타입 문제 해결"""
    result = pd.to_numeric(s, errors="coerce")
    # Int64 타입이나 정수형의 경우 float64로 변환하여 clip 함수 호환성 확보
    if (hasattr(result.dtype, 'is_numeric') and result.dtype.is_numeric and 
        ('Int' in str(result.dtype) or pd.api.types.is_integer_dtype(result.dtype))):
        return result.astype(np.float64)
    return result

def _cast_back_like(orig: pd.Series, s: pd.Series) -> pd.Series:
    """클리핑으로 나온 수치를 원래 dtype에 최대한 맞춰 돌려놓기.
    - 정수형이면 반올림 후 정수로 캐스팅 (NaN이 있으면 pandas nullable Int64)
    - 그 외는 Float64 그대로 유지
    """
    if pd.api.types.is_integer_dtype(orig.dtype):
        s2 = s.round(0)
        # Int64 타입의 경우 안전하게 처리
        if hasattr(orig.dtype, 'is_numeric') and orig.dtype.is_numeric:
            try:
                if s2.isna().any():
                    return s2.astype("Int64")
                return s2.astype(np.int64)
            except (ValueError, TypeError):
                # 변환 실패 시 float64로 유지
                return s2.astype(np.float64)
        else:
            return s2.astype(np.float64)
    return s  # float/decimal/object 등은 그대로

def iqr_clip_series(s: pd.Series, multiplier: float = 1.5) -> Tuple[pd.Series, Dict[str, float]]:
    # 원본 타입 저장
    orig_dtype = s.dtype
    
    # 안전한 숫자 변환 (Int64 문제 해결)
    s_num = _to_numeric(s)
    
    # clip 함수 호환성을 위해 float64로 확실하게 변환
    if pd.api.types.is_integer_dtype(s_num.dtype) or 'Int' in str(s_num.dtype):
        s_num = s_num.astype(np.float64)
    
    q1 = s_num.quantile(0.25)
    q3 = s_num.quantile(0.75)
    iqr = q3 - q1
    lo = q1 - multiplier * iqr
    hi = q3 + multiplier * iqr
    
    # clip 실행
    clipped = s_num.clip(lower=lo, upper=hi)
    
    # 원본 타입으로 복원 시도
    clipped = _cast_back_like(s, clipped)
    
    return clipped, {"q1": float(q1), "q3": float(q3), "lo": float(lo), "hi": float(hi), "multiplier": float(multiplier)}

def zscore_clip_series(s: pd.Series, z: float = 3.0) -> Tuple[pd.Series, Dict[str, float]]:
    # 원본 타입 저장
    orig_dtype = s.dtype
    
    # 안전한 숫자 변환 (Int64 문제 해결)
    s_num = _to_numeric(s)
    
    # clip 함수 호환성을 위해 float64로 확실하게 변환
    if pd.api.types.is_integer_dtype(s_num.dtype) or 'Int' in str(s_num.dtype):
        s_num = s_num.astype(np.float64)
    
    mu = float(s_num.mean())
    sd = float(s_num.std(ddof=0))
    if sd == 0 or np.isnan(sd):
        return _cast_back_like(s, s_num), {"mean": mu, "std": sd, "lo": mu, "hi": mu, "z": float(z)}
    
    lo, hi = mu - z * sd, mu + z * sd
    
    # clip 실행
    clipped = s_num.clip(lo, hi)
    
    # 원본 타입으로 복원 시도
    clipped = _cast_back_like(s, clipped)
    
    return clipped, {"mean": mu, "std": sd, "lo": lo, "hi": hi, "z": float(z)}

def outlier(df: pd.DataFrame, rules: Iterable[Dict[str, Any]]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    rules 예:
      - {"col":"금액","method":"iqr_clip","multiplier":1.5}
      - {"col":"수량","method":"zscore_clip","z":3}
    * 호환: iqr_clip에서 'k' 별칭도 인식 (k -> multiplier)
    """
    out = df.copy()
    rep: List[Dict[str, Any]] = []

    for r in rules or []:
        col = r.get("col")
        method = (r.get("method") or "").lower()
        if not col or col not in out.columns:
            rep.append({"col": col, "method": method, "status": "skip:not_found"})
            continue

        if method in ("iqr", "iqr_clip"):
            # alias: k -> multiplier
            m = r.get("multiplier", r.get("k", 1.5))
            try:
                m = float(m)
            except Exception:
                m = 1.5
            s2, stats = iqr_clip_series(out[col], multiplier=m)
            n_changed = int(((pd.to_numeric(out[col], errors="coerce") != pd.to_numeric(s2, errors="coerce")) & pd.to_numeric(out[col], errors="coerce").notna()).sum())
            out[col] = s2
            rep.append({"col": col, "method": "iqr_clip", "changed": n_changed, **stats, "status": "ok"})

        elif method in ("z", "zscore", "zscore_clip"):
            z = r.get("z", r.get("threshold", 3.0))
            try:
                z = float(z)
            except Exception:
                z = 3.0
            s2, stats = zscore_clip_series(out[col], z=z)
            n_changed = int(((pd.to_numeric(out[col], errors="coerce") != pd.to_numeric(s2, errors="coerce")) & pd.to_numeric(out[col], errors="coerce").notna()).sum())
            out[col] = s2
            rep.append({"col": col, "method": "zscore_clip", "changed": n_changed, **stats, "status": "ok"})

        else:
            rep.append({"col": col, "method": method, "status": "skip:unknown_method"})

    return out, {"outlier": rep}

# 기존 함수들과의 호환성을 위한 별칭
def detect_outliers(df: pd.DataFrame, columns: List[str], method: str = "iqr", **kwargs) -> Dict[str, Any]:
    """기존 호환성을 위한 함수"""
    rules = [{"col": col, "method": method, **kwargs} for col in columns]
    _, report = outlier(df, rules)
    return report

def handle_outliers(df: pd.DataFrame, outlier_info: Dict[str, Any], action: str = "clip", **kwargs) -> pd.DataFrame:
    """기존 호환성을 위한 함수"""
    # outlier_info에서 rules 형태로 변환
    rules = []
    for col, info in outlier_info.items():
        if isinstance(info, dict) and "method" in info:
            rules.append({"col": col, **info})
    
    if rules:
        df_processed, _ = outlier(df, rules)
        return df_processed
    return df

def get_outlier_summary(df: pd.DataFrame, outlier_info: Dict[str, Any]) -> Dict[str, Any]:
    """기존 호환성을 위한 함수"""
    return outlier_info
