
from __future__ import annotations
from .intent_schema import Intent
from .intent_llm import parse_with_llm

def parse_rule(text: str) -> Intent:
    t = text.strip().lower()
    rows, values, chart = [], [], None
    filters = {}
    
    if "월" in t or "월별" in t: rows.append("월")
    if "카테고리" in t: rows.append("카테고리")
    if any(k in t for k in ["매출","금액","합계","sum"]): values.append(("금액","sum"))
    if any(k in t for k in ["수량","개수","count"]): values.append(("수량","sum"))
    if any(k in t for k in ["막대","bar"]): chart="bar"
    elif any(k in t for k in ["라인","line"]): chart="line"
    elif any(k in t for k in ["파이","pie"]): chart="pie"
    
    # 필터 인식 (초간단)
    if "서울" in t: filters.setdefault("도시", []).append("서울")
    if "부산" in t: filters.setdefault("도시", []).append("부산")
    if "대구" in t: filters.setdefault("도시", []).append("대구")
    
    return Intent(rows=rows, values=values, chart=chart, filters=filters)

def suggest_pivot_structure(df: pd.DataFrame, text: str = "") -> Dict[str, Any]:
    """데이터 구조를 분석하여 피벗 구성을 제안합니다."""
    suggestions = {
        "rows": [],
        "values": [],
        "chart": "bar"
    }
    
    # 범주형 컬럼 추천 (고유값이 적은 컬럼)
    for col in df.columns:
        if df[col].dtype == 'object' or df[col].dtype.name == 'category':
            unique_count = df[col].nunique()
            if 2 <= unique_count <= 20:  # 적당한 범주 수
                suggestions["rows"].append(col)
    
    # 수치형 컬럼 추천
    numeric_cols = df.select_dtypes(include=['number']).columns
    for col in numeric_cols:
        if col not in ['월', '년', '일']:  # 날짜 관련 제외
            suggestions["values"].append((col, "sum"))
    
    # 차트 타입 자동 추천
    if len(suggestions["rows"]) == 1 and len(suggestions["values"]) == 1:
        suggestions["chart"] = "bar"
    elif len(suggestions["rows"]) > 5:
        suggestions["chart"] = "line"
    elif len(suggestions["rows"]) <= 3:
        suggestions["chart"] = "pie"
    
    return suggestions

def parse(text: str, *, columns=None, parser="auto") -> Intent:
    rule = parse_rule(text)
    if parser == "rule":
        return rule
    if parser == "llm":
        llm = parse_with_llm(text, allowed_columns=columns)
        return llm or rule
    # auto: 규칙 충분하면 규칙, 아니면 LLM
    if rule.rows and rule.values:
        return rule
    llm = parse_with_llm(text, allowed_columns=columns)
    return llm or rule
