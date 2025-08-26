from __future__ import annotations
import math, re, unicodedata
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

NUMERIC_RE = re.compile(r"^[\s+-]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?\s*$")
CURRENCY_RE = re.compile(r"(?i)^(?P<prefix>krw|₩|원)?\s*(?P<num>[\d,]+(?:\.\d+)?)\s*(?P<suffix>원)?$")
# 비캡처 그룹 사용 + 다양한 포맷 힌트
DATE_HINT_RE = re.compile(r'(?:\d{4}[-/\.]\d{1,2}[-/\.]\d{1,2}|(?:\d{1,2}[-/]\d{1,2}[-/]\d{2})|년|월|일|:)')
CURRENCY_HINT_RE = re.compile(r'(?:₩|원|KRW|krw|USD|usd|\$|€|£)')
NUMERIC_HINT_RE = re.compile(r'(?:^\d+[,\.]\d+$|^\d+$)')
BOOL_HINT_RE = re.compile(r'(?:예|아니오|Y|N|YES|NO|TRUE|FALSE|True|False|true|false|1|0)')

BOOL_TRUE = {"true","t","1","y","yes","예","ㅇ","응"}
BOOL_FALSE = {"false","f","0","n","no","아니오","아니요","ㄴ","ㄴㄴ"}

@dataclass
class ColumnProfile:
    name: str
    nonnull: int
    nulls: int
    nunique: int
    sample_values: List[Any]
    type_candidates: List[Tuple[str, float]]  # [(type, confidence)]
    stats: Optional[Dict[str, float]] = None  # numeric only

def _normalize_text(x: Any) -> str:
    if pd.isna(x):
        return ""
    s = str(x)
    s = unicodedata.normalize("NFKC", s).strip()
    return s

def _has_date_hint(series: pd.Series) -> pd.Series:
    s = series.astype("string")
    return s.str.contains(DATE_HINT_RE, regex=True, na=False)

def _infer_candidates(series: pd.Series, sample_n: int = 1000) -> List[Tuple[str,float]]:
    """타입 추론 후보들을 점수와 함께 반환"""
    candidates = []
    
    s_str = series.astype(str)
    total = len(s_str)
    
    def ratio(mask: pd.Series) -> float:
        return float(mask.sum())/total if total else 0.0
    
    # 날짜 후보
    has_date_hint = _has_date_hint(series)
    p_date = ratio(has_date_hint)
    if p_date > 0.1:  # 10% 이상이 날짜 힌트를 가지면
        candidates.append(("datetime", p_date * 0.8))  # 날짜는 확신도 낮춤

    # boolean
    lower = s_str.str.lower()
    is_bool = lower.isin(BOOL_TRUE | BOOL_FALSE)
    p_bool = ratio(is_bool)

    # currency / numeric
    is_currency = s_str.str.match(CURRENCY_RE)
    p_currency = ratio(is_currency)

    is_numeric_like = s_str.str.match(NUMERIC_RE)
    p_numeric = ratio(is_numeric_like)

    # date hint
    has_date_hint = s_str.astype(str).str.contains(DATE_HINT_RE, regex=True, na=False)
    p_date = ratio(has_date_hint)

    # 결과 정렬 (높은 점수 순)
    candidates.extend([
        ("boolean", p_bool),
        ("currency", p_currency),
        ("numeric", p_numeric),
        ("datetime", p_date),
    ])
    
    candidates.sort(key=lambda x: x[1], reverse=True)
    
    # 기본값 추가
    if not candidates or candidates[0][1] < 0.5:
        candidates.append(("string", 1.0))
    
    return candidates[:3]  # 상위 3개만 반환

def _numeric_stats(series: pd.Series) -> Optional[Dict[str,float]]:
    # best-effort parsing for numeric-like strings
    try:
        s = pd.to_numeric(series.dropna().astype(str).str.replace(",", "", regex=False), errors="coerce")
        s = s.dropna()
        if s.empty:
            return None
        desc = s.describe()
        out = {k: float(desc[k]) for k in ["count","mean","std","min","25%","50%","75%","max"] if k in desc}
        return out
    except Exception:
        return None

def profile_dataframe(df: pd.DataFrame, sample_rows: Optional[int] = 50000) -> Dict[str, Any]:
    if sample_rows and len(df) > sample_rows:
        sample = df.sample(sample_rows, random_state=42)
    else:
        sample = df

    profiles: List[ColumnProfile] = []
    for col in sample.columns:
        s = sample[col]
        nonnull = int(s.notna().sum())
        nulls = int(s.isna().sum())
        nunique = int(s.nunique(dropna=True))
        sample_vals = s.head(5).tolist()

        candidates = _infer_candidates(s)
        stats = _numeric_stats(s) if any(t=="numeric" and p>0.5 for t,p in candidates) else None

        profiles.append(ColumnProfile(
            name=str(col),
            nonnull=nonnull,
            nulls=nulls,
            nunique=nunique,
            sample_values=sample_vals,
            type_candidates=candidates,
            stats=stats
        ))

    # summary metrics
    res = {
        "n_rows": int(len(df)),
        "n_cols": int(df.shape[1]),
        "columns": [p.__dict__ for p in profiles],
    }
    return res
