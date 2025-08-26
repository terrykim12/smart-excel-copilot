import re
from typing import List, Dict, Any

def _to_snake(text: str) -> str:
    """한글/공백/대소문자를 스네이크 케이스로 변환"""
    # 한글 제거, 공백을 언더스코어로, 대문자를 소문자로
    text = re.sub(r'[가-힣]', '', text)  # 한글 제거
    text = re.sub(r'\s+', '_', text.strip())  # 공백을 언더스코어로
    text = re.sub(r'([a-z])([A-Z])', r'\1_\2', text)  # camelCase를 snake_case로
    text = text.lower()
    text = re.sub(r'[^a-z0-9_]', '', text)  # 특수문자 제거
    text = re.sub(r'_+', '_', text)  # 연속 언더스코어를 하나로
    return text.strip('_')

def normalize_column_names(columns: List[str]) -> Dict[str, str]:
    """컬럼명을 정규화하고 매핑 딕셔너리 반환"""
    mapping = {}
    for col in columns:
        normalized = _to_snake(col)
        mapping[normalized] = col
        mapping[col] = col  # 원본도 보존
    return mapping

def map_intent_to_columns(intent_rows: List[str], intent_values: List[tuple], 
                         available_columns: List[str]) -> Dict[str, Any]:
    """의도를 실제 컬럼에 매핑"""
    mapping = normalize_column_names(available_columns)
    
    # 매핑된 결과
    mapped_rows = []
    mapped_values = []
    
    # rows 매핑
    for row in intent_rows:
        if row in mapping:
            mapped_rows.append(mapping[row])
        else:
            # 부분 매칭 시도
            for col in available_columns:
                if row.lower() in col.lower() or col.lower() in row.lower():
                    mapped_rows.append(col)
                    break
    
    # values 매핑
    for col, agg in intent_values:
        if col in mapping:
            mapped_values.append((mapping[col], agg))
        else:
            # 부분 매칭 시도
            for available_col in available_columns:
                if col.lower() in available_col.lower() or available_col.lower() in col.lower():
                    mapped_values.append((available_col, agg))
                    break
    
    return {
        "rows": mapped_rows,
        "values": mapped_values,
        "mapping": mapping
    }
