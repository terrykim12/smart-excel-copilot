from __future__ import annotations
import io, os, codecs
from pathlib import Path
from typing import Optional, Tuple
import pandas as pd
import chardet
from typing import Dict, Any

def _try_read_csv(path: Path, encoding: str) -> pd.DataFrame:
    return pd.read_csv(path, encoding=encoding)

def _detect_csv_encoding(path: Path) -> str:
    # 매우 단순한 감지: UTF-8-SIG 우선, 안되면 cp949
    try:
        with open(path, 'rb') as f:
            raw = f.read(4096)
        if raw.startswith(codecs.BOM_UTF8):
            return 'utf-8-sig'
    except Exception:
        pass
    # pandas 시도
    for enc in ('utf-8', 'utf-8-sig', 'cp949'):
        try:
            pd.read_csv(path, encoding=enc, nrows=5)
            return enc
        except Exception:
            continue
    return 'utf-8'

def detect_encoding(file_path: str) -> Dict[str, Any]:
    """파일의 인코딩을 감지합니다."""
    with open(file_path, 'rb') as f:
        raw_data = f.read()
        result = chardet.detect(raw_data)
        return result

def load_table(file_path: str, sheet: Optional[str] = None, encoding: Optional[str] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """CSV 또는 Excel 파일을 로드합니다."""
    if not encoding:
        detected = detect_encoding(file_path)
        encoding = detected.get('encoding', 'utf-8')
    
    try:
        if file_path.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file_path, sheet_name=sheet)
        else:
            df = pd.read_csv(file_path, encoding=encoding)
        
        return df, {"encoding": encoding, "detected": detected if not encoding else None}
    except Exception as e:
        raise Exception(f"파일 로드 실패: {file_path}, 오류: {str(e)}")

def save_table(df: pd.DataFrame, src_path: str, suffix: str = "_clean") -> str:
    p = Path(src_path)
    out_path = str(p.with_name(p.stem + suffix + p.suffix))
    if p.suffix.lower() in {'.csv', '.txt'}:
        df.to_csv(out_path, index=False)
    elif p.suffix.lower() in {'.xlsx', '.xls'}:
        df.to_excel(out_path, index=False)
    else:
        df.to_csv(out_path + '.csv', index=False)
        out_path = out_path + '.csv'
    return out_path

def write_table(df: pd.DataFrame, path: str, sheet: str | None = None):
    """테이블을 파일로 저장합니다."""
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    if p.suffix.lower() in (".xlsx", ".xls"):
        df.to_excel(p, index=False, sheet_name=(sheet or "Sheet1"))
    else:
        df.to_csv(p, index=False, encoding="utf-8-sig")
