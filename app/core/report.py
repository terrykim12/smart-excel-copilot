from __future__ import annotations
import json, os, time
from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional
import pandas as pd

def _log_dir() -> str:
    # Windows 우선: %LOCALAPPDATA%
    d = os.getenv('LOCALAPPDATA')
    if not d:
        # fallback
        d = os.path.join(os.path.expanduser('~'), '.smart_excel', 'logs')
    else:
        d = os.path.join(d, 'SmartExcelCopilot', 'logs')
    os.makedirs(d, exist_ok=True)
    return d

@dataclass
class PreprocessReport:
    src_path: str
    out_path: str
    n_rows_before: int
    n_rows_after: int
    n_cols_before: int
    n_cols_after: int
    notes: Dict[str, Any]

def save_report(rep: PreprocessReport) -> str:
    ts = time.strftime('%Y%m%d_%H%M%S')
    path = os.path.join(_log_dir(), f'preprocess_report_{ts}.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(asdict(rep), f, ensure_ascii=False, indent=2)
    return path

def basic_diff_metrics(before: pd.DataFrame, after: pd.DataFrame) -> Dict[str, Any]:
    return {
        'nulls_before': int(before.isna().sum().sum()),
        'nulls_after': int(after.isna().sum().sum()),
        'duplicates_before': int(before.duplicated().sum()),
        'duplicates_after': int(after.duplicated().sum()),
    }
