
from __future__ import annotations
from typing import List, Dict, Any
from .engines import pick_engine

def run_pivot(path: str, source_sheet: str, target_sheet: str, rows: List[str], columns: List[str], values: List[str], filters: Dict[str, list], data_range: str|None, out_path: str|None=None):
    eng = pick_engine(path)
    try:
        res = eng.create_pivot(source_sheet, target_sheet, rows, columns, values, filters, data_range)
        eng.save_as(out_path or path)
        return res
    finally:
        eng.close()
