
from __future__ import annotations
from .engines import pick_engine

def run_formula(path: str, sheet: str, a1_range: str, formula: str, fill_down: bool, named_range: str|None, out_path: str|None=None):
    eng = pick_engine(path)
    try:
        res = eng.write_formula(sheet, a1_range, formula, fill_down=fill_down, named_range=named_range)
        eng.save_as(out_path or path)
        return res
    finally:
        eng.close()
