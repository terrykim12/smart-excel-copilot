from __future__ import annotations
import re
import unicodedata
import logging
import warnings
from typing import Any, List, Optional, Tuple
import numpy as np
import pandas as pd
from dateutil import parser as date_parser
from app.core.utils import ensure_df

# --- precompiled regex (속도 ↑) ---
RE_ISO_DATE     = re.compile(r"^\d{4}-\d{1,2}-\d{1,2}$")
RE_SLASH_DATE   = re.compile(r"^\d{4}/\d{1,2}/\d{1,2}$")
RE_DOT_DATE     = re.compile(r"^\d{4}\.\d{1,2}\.\d{1,2}$")
RE_DT_WITH_TIME = re.compile(r"^\d{4}[-/\.]\d{1,2}[-/\.]\d{1,2}[ T]\d{2}:\d{2}:\d{2}$")
RE_CONTIG_DATE  = re.compile(r"^\d{8}$")  # 새롭게 추가: YYYYMMDD

# 다양한 통화 기호 인식 (₩, 원, $, €, ¥, £ 및 통화 코드)
RE_HAS_CURRENCY = re.compile(
    r"(?:₩|원|KRW|krw|\$|USD|usd|€|EUR|eur|¥|JPY|jpy|£|GBP|gbp)"
)
RE_NUM_KEEP     = re.compile(r"[^\d\.\-]")  # 숫자/소수점/부호만 남김

BOOL_MAP = {
    "예": True, "예요": True, "Y": True, "YES": True, "TRUE": True, "1": True,
    "아니오": False, "아니요": False, "N": False, "NO": False, "FALSE": False, "0": False,
}


def _to_snake(name: str) -> str:
    if name is None:
        return name
    s = str(name).strip()
    s = re.sub(r"[^\w가-힣]+", "_", s, flags=re.UNICODE)
    s = re.sub(r"_{2,}", "_", s).strip("_")
    return s.lower()


def _snake_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [_to_snake(c) for c in out.columns]
    return out


def _trim_spaces(s: pd.Series) -> pd.Series:
    s = s.astype("string")
    s = s.str.strip().str.replace(r"\s+", " ", regex=True)
    return s


def _normalize_bool(s: pd.Series):
    """
    반환: (bool_series: 'boolean' dtype, hit_ratio: float)
    - 매핑된 값은 True/False
    - 매핑 실패는 <NA> (문자열을 섞지 않음)
    """
    su = s.astype("string").str.strip().str.upper()
    mapped = su.map(BOOL_MAP)              # object dtype, 값은 True/False/np.nan
    mask = mapped.notna()
    # 불리언 dtype 시리즈를 만들고, 매핑된 곳만 채움
    out = pd.Series(pd.NA, index=s.index, dtype="boolean")
    # astype(bool)로 Python bool 캐스팅 → boolean dtype에 넣기
    out.loc[mask] = mapped.loc[mask].astype(bool)
    hit = float(mask.mean())
    return out, hit


def _parse_currency_fast(s: pd.Series, currency_split: bool):
    st = s.astype("string")
    has_cur = st.str.contains(RE_HAS_CURRENCY, regex=True, na=False)
    cleaned = st.str.replace(RE_NUM_KEEP, "", regex=True)
    nums = pd.to_numeric(cleaned, errors="coerce")
    if currency_split:
        cur = pd.Series(np.where(has_cur.to_numpy(), "KRW", None), index=s.index, dtype="object")
        return nums, cur, has_cur.mean()
    return nums, None, has_cur.mean()


def _parse_date_fast(
    s: pd.Series, *, keep_time: bool = False, date_fmt: Optional[str] = None
) -> Tuple[pd.Series, float]:
    """
    다양한 문자열 날짜를 인식하는 확장된 파서.
    date_fmt가 제공되면 'YYYYMMDD' 같은 형식을 %Y%M%... 형태로 변환해 우선 적용하고,
    이후 여러 패턴별로 파싱한 뒤 마지막으로 format="mixed" 또는 dateutil 파싱을 시도합니다.
    """
    st = s.astype("string")
    out = pd.Series(pd.NaT, index=s.index, dtype="datetime64[ns]")

    # 사용자 정의 포맷 처리
    if date_fmt:
        fmt = date_fmt.replace("YYYY", "%Y").replace("MM", "%m").replace("DD", "%d")
        try:
            dt = pd.to_datetime(st, format=fmt, errors="coerce")
            out.loc[dt.notna()] = dt
        except Exception:
            pass

    # 간단한 패턴 우선 처리
    mask_time = st.str.match(RE_DT_WITH_TIME, na=False)
    if mask_time.any():
        out.loc[mask_time] = pd.to_datetime(st[mask_time], errors="coerce")

    for regex, fmt in (
        (RE_ISO_DATE, "%Y-%m-%d"),
        (RE_SLASH_DATE, "%Y/%m/%d"),
        (RE_DOT_DATE, "%Y.%m.%d"),
    ):
        mask = st.str.match(regex, na=False)
        if mask.any():
            out.loc[mask] = pd.to_datetime(st[mask], format=fmt, errors="coerce")

    # 연속 날짜 (YYYYMMDD) 처리
    mask_contig = st.str.match(RE_CONTIG_DATE, na=False)
    if mask_contig.any():
        out.loc[mask_contig] = pd.to_datetime(
            st[mask_contig], format="%Y%m%d", errors="coerce"
        )

    # 남은 값은 format="mixed" 또는 dateutil 파싱
    mask_remaining = out.isna()
    if mask_remaining.any():
        try:
            # pandas>=2.0 일부 버전에서 지원
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                general = pd.to_datetime(
                    st[mask_remaining], format="mixed", errors="coerce"
                )
                out.loc[mask_remaining] = general
        except TypeError:
            # fallback: dateutil 개별 파싱(경고 없음)
            def _parse(x: str):
                try:
                    return date_parser.parse(x, dayfirst=False)
                except Exception:
                    return pd.NaT
            
            parsed_dates = st[mask_remaining].map(_parse)
            out.loc[mask_remaining] = parsed_dates

    # 문자열 포맷으로 변환
    if keep_time:
        result = out.dt.strftime("%Y-%m-%d %H:%M:%S")
    else:
        result = out.dt.strftime("%Y-%m-%d")

    hit_ratio = float((~out.isna()).mean())
    return result, hit_ratio


def level1_clean(
    df: pd.DataFrame,
    trim: bool = True,
    date_fmt: str = "YYYY-MM-DD",
    currency_split: bool = True,
    drop_empty: bool = True,
    preserve_time_cols = ("업데이트일",),
    return_logs: bool = False,
):
    """FastPath 클리닝. 기존 시그니처 호환.
    preserve_time_cols: 시각까지 보존할 컬럼명 리스트 (기본: ['업데이트일'])
    return_logs: True면 (df, type_info, normalize_log) 반환, False면 df만 반환
    """
    df = ensure_df(df)            # ★ 들어오는 게 튜플이어도 방어
    if preserve_time_cols is None:
        preserve_time_cols = ["업데이트일"]

    out = df.copy()

    # 0) 열 이름 표준화
    out = _snake_columns(out)
    # 디버깅 메시지는 logging을 사용해 출력 (필요 시만)
    logger = logging.getLogger(__name__)
    logger.debug("Columns after snake_case: %s", list(out.columns))
    logger.debug("Columns repr: %s", repr(list(out.columns)))

    # 1) 문자열 트림
    if trim:
        for c in out.columns:
            if pd.api.types.is_object_dtype(out[c]) or pd.api.types.is_string_dtype(out[c]):
                out[c] = _trim_spaces(out[c])

    # 2) 불리언 표준화
    for c in out.columns:
        if pd.api.types.is_object_dtype(out[c]) or pd.api.types.is_string_dtype(out[c]):
            bool_series, hit = _normalize_bool(out[c])
            # 열 전체의 90% 이상이 불리언으로 매핑되는 경우에만 불리언 컬럼으로 채택
            if hit > 0.9:
                out[c] = bool_series
            # 그렇지 않으면 원본 유지 (섞지 않음)

    # 3) 통화/숫자 표준화 (벡터화)
    for c in out.columns:
        s = out[c]
        if pd.api.types.is_string_dtype(s) or pd.api.types.is_object_dtype(s):
            nums, cur, hit = _parse_currency_fast(s, currency_split)
            # 통화/숫자 히트율로 판단
            try:
                conv = pd.to_numeric(s.str.replace(",", "", regex=False), errors="coerce")
            except Exception:
                conv = pd.Series(index=s.index, dtype=float)
            if hit > 0.2 or conv.notna().mean() > 0.5:
                # 통화가 더 설득력 있으면 채택
                if hit >= 0.2 and nums.notna().sum() >= conv.notna().sum():
                    out[c] = nums
                    if currency_split:
                        out[f"{c}__currency"] = cur
                else:
                    out[c] = conv

    # 4) 날짜 표준화 (포맷 분기) - boolean, date, currency/number 순으로 처리
    for c in out.columns:
        s = out[c]
        if pd.api.types.is_string_dtype(s) or pd.api.types.is_object_dtype(s):
            keep_time = any(_to_snake(c) == _to_snake(x) for x in preserve_time_cols)
            parsed, hit = _parse_date_fast(s, keep_time=keep_time, date_fmt=date_fmt)
            if hit > 0.6:
                out[c] = parsed
                logger.debug(f"Date parsing for column '{c}': hit_ratio={hit:.3f}")

    # 5) 빈 행/열 제거
    if drop_empty:
        out = out.dropna(how="all")
        out = out.dropna(axis=1, how="all")

    type_info = {}        # 필요시 채워 사용
    normalize_log = {}    # 필요시 채워 사용
    if return_logs:
        return out, type_info, normalize_log
    return out

def standardize(df, date_fmt="YYYY-MM-DD", currency_split=True, trim=True, drop_empty=True):
    """
    레거시 호환용: (df, type_info, normalize_log)를 반환
    """
    out = level1_clean(
        df,
        trim=trim,
        date_fmt=date_fmt,
        currency_split=currency_split,
        drop_empty=drop_empty,
        return_logs=True,
    )
    return out  # (df, type_info, normalize_log)
