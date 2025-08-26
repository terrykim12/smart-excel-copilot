from __future__ import annotations
from typing import List, Optional, Any, Dict, Union, Tuple, Iterable
import re
import pandas as pd
from app.core.utils import ensure_df


def _to_snake(name: str) -> str:
    if name is None:
        return name
    s = str(name).strip()
    s = re.sub(r"[^\w가-힣]+", "_", s, flags=re.UNICODE)
    s = re.sub(r"_{2,}", "_", s).strip("_")
    return s.lower()


def _normalize_cols(cols):
    return { _to_snake(c): c for c in cols }


def _map_keys(df: pd.DataFrame, keys: List[str]) -> List[str]:
    canon2real = _normalize_cols(df.columns)
    mapped: List[str] = []
    miss: List[str] = []
    for k in keys:
        canon = _to_snake(k)
        real = canon2real.get(canon)
        if real is None:
            miss.append(k)
        else:
            mapped.append(real)
    if miss:
        raise KeyError(f"dedupe 키를 찾을 수 없습니다: {miss} / 사용 가능 열: {list(df.columns)}")
    return mapped


def _map_many(df: pd.DataFrame, keys: Union[str, List[str]]) -> List[str]:
    if isinstance(keys, str):
        return _map_keys(df, [keys])
    return _map_keys(df, keys)


def _map_one(df: pd.DataFrame, key: str) -> str:
    return _map_keys(df, [key])[0]


def dedupe(df: pd.DataFrame, keys: Union[str, List[str]], keep: str = "last") -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    keys: 중복 판단 키 목록(사용자 입력형). 내부에서 실제 컬럼명으로 매핑함.
    keep: 'first' | 'last' | 'last_by:<열명>'
    """
    df = ensure_df(df)  # ★ 방어
    out = df.copy()
    if not keys or (isinstance(keys, (list, tuple)) and len(keys) == 0):
        before = len(out)
        result = out.drop_duplicates(keep=("last" if keep == "last" else "first"))
        return result, {"keys": "ALL", "removed": before - len(result), "keep": keep}

    keys_real = _map_many(out, keys)
    before = len(out)

    if isinstance(keep, str) and keep.startswith("last_by:"):
        by_raw = keep.split(":", 1)[1]
        by_real = _map_one(out, by_raw)
        result = (
            out.sort_values(by=[by_real] + keys_real, ascending=[False] + [True]*len(keys_real))
               .drop_duplicates(subset=keys_real, keep="first")
        )
        return result, {"keys": keys_real, "removed": before - len(result), "keep": keep, "sorted_by": by_real}

    result = out.sort_values(keys_real).drop_duplicates(subset=keys_real, keep=("last" if keep == "last" else "first"))
    return result, {"keys": keys_real, "removed": before - len(result), "keep": keep}
