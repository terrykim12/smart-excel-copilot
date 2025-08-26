import chardet
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd

def ensure_df(x):
    """(df, …) 형태가 오면 df만 뽑아 전달"""
    if isinstance(x, tuple) and len(x) > 0 and isinstance(x[0], pd.DataFrame):
        return x[0]
    return x

def detect_encoding(file_path: str) -> Dict[str, Any]:
    """파일의 인코딩을 감지합니다."""
    with open(file_path, 'rb') as f:
        raw_data = f.read()
        result = chardet.detect(raw_data)
        return result

def load_table(file_path: str, sheet: Optional[str] = None, encoding: Optional[str] = None) -> tuple:
    """테이블을 로드합니다."""
    # 기본 구현 - 실제로는 app.io.loader의 load_table을 사용
    import pandas as pd
    if file_path.endswith('.csv'):
        df = pd.read_csv(file_path, encoding=encoding or 'utf-8')
    else:
        df = pd.read_excel(file_path, sheet_name=sheet)
    return df, {"encoding": encoding or "utf-8"}

def write_table(df, file_path: str, sheet: str = "Sheet1", encoding: str = "utf-8"):
    """테이블을 저장합니다."""
    import pandas as pd
    if file_path.endswith('.csv'):
        df.to_csv(file_path, index=False, encoding=encoding)
    else:
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=sheet, index=False)
