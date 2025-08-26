
from __future__ import annotations
import os, json, time, datetime as dt
from typing import Dict, Any, List
import pandas as pd
from ..core.report import _log_dir
from .pivot import run_pivot
from .charts import run_chart

def weekly_report(path: str, source_sheet: str, target_sheet: str, start: str, end: str, include: List[str], export: List[str]) -> Dict[str, Any]:
    # 간단한 요약표: 기간 내 금액/수량 합계
    df = pd.read_excel(path, sheet_name=source_sheet)
    date_col = None
    for c in df.columns:
        if "일" in c or "날짜" in c:
            date_col = c; break
    if date_col:
        s = pd.to_datetime(df[date_col], errors="coerce")
        mask = (s >= pd.to_datetime(start)) & (s <= pd.to_datetime(end))
        df_period = df[mask].copy()
    else:
        df_period = df.copy()

    summary = {
        "매출합계": float(pd.to_numeric(df_period.get("금액", pd.Series(dtype=float)), errors="coerce").fillna(0).sum()),
        "수량합계": float(pd.to_numeric(df_period.get("수량", pd.Series(dtype=float)), errors="coerce").fillna(0).sum()),
        "행수": int(len(df_period)),
        "기간": f"{start}~{end}",
    }

    # 피벗 & 차트
    run_pivot(path, source_sheet, "피벗_매출", rows=["월","카테고리"], columns=[], values=["금액:sum","수량:sum"], filters={}, data_range=None, out_path=path)
    run_chart(path, "차트_매출", "bar", "피벗_매출!A1:D30", "월별 카테고리 매출", {"legend":"right","data_labels":True}, out_path=path)

    # 로그 저장
    ts = time.strftime("%Y%m%d_%H%M%S")
    rep = {
        "action": "report_weekly",
        "source": {"path": path, "sheet": source_sheet},
        "target": {"sheet": target_sheet},
        "summary": summary,
        "notes": {"engine": "auto"},
        "timestamp": ts,
    }
    log_path = os.path.join(_log_dir(), f"autoexcel_report_{ts}.json")
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(rep, f, ensure_ascii=False, indent=2)
    return {"log": log_path, "summary": summary}
