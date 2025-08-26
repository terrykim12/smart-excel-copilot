
from __future__ import annotations
from typing import Dict, Any
from .engines import pick_engine
from .engines_openpyxl import create_pivot_chart_openpyxl

def run_chart(path: str, target_sheet: str, chart_type: str, data_range: str, title: str, style: Dict[str, Any], out_path: str|None=None):
    """기존 엔진을 사용하여 차트를 생성합니다."""
    eng = pick_engine(path)
    try:
        res = eng.create_chart(target_sheet, chart_type, data_range, title, style)
        eng.save_as(out_path or path)
        return res
    finally:
        eng.close()

def run_pivot_chart_openpyxl(path_in: str, path_out: str, src_sheet: str, tgt_sheet: str, rows: list, values: list, chart_type: str = "bar"):
    """openpyxl 엔진을 사용하여 피벗 차트를 생성합니다."""
    return create_pivot_chart_openpyxl(path_in, path_out, src_sheet, tgt_sheet, rows, values, chart_type)
