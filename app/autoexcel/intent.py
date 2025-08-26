# app/autoexcel/intent.py
import json
import os
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from .intent_schema import Intent
from .intent_llm import parse_with_llm

logger = logging.getLogger(__name__)

def _load_keyword_map(file_path: Optional[str] = None) -> Dict[str, Any]:
    """keyword_map.json을 읽어 동적 매핑을 제공하며, 없을 경우 기본 매핑 사용."""
    default_map = {
        "rows": {
            "월": ["월", "월별", "month"],
            "카테고리": ["카테고리", "카테고리별", "category", "cat"],
            "도시": ["도시", "도시별", "지역", "지역별", "city", "region"],
            "년": ["년", "연", "year"],
            "분기": ["분기", "quarter"],
        },
        "values": {
            "금액": {"keywords": ["매출", "금액", "합계", "sum", "sales", "amount"], "agg": "sum"},
            "수량": {"keywords": ["수량", "개수", "count", "quantity", "qty"], "agg": "sum"},
        },
        "chart": {
            "bar": ["막대", "막대차트", "bar", "bar chart", "column"],
            "line": ["라인", "선", "line", "line chart"],
            "pie": ["파이", "파이차트", "pie", "pie chart"],
        },
        "filters": {
            "도시": {
                "서울": ["서울", "seoul"],
                "부산": ["부산", "busan"],
                "대구": ["대구", "daegu"],
                "인천": ["인천", "incheon"],
                "광주": ["광주", "gwangju"],
            }
        },
    }
    map_path = (
        file_path
        or os.getenv("SEC_KEYWORD_MAP")
        or str(Path(__file__).with_name("keyword_map.json"))
    )
    try:
        with open(map_path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        logger.debug("Failed to load keyword map, using default", exc_info=True)
        return default_map

def parse_rule(text: str, *, keyword_map_path: Optional[str] = None) -> Intent:
    """텍스트를 기반으로 매핑된 규칙을 적용하여 Intent 객체를 생성."""
    t = text.strip().lower()
    mapping = _load_keyword_map(keyword_map_path)
    rows: List[str] = []
    values: List[Tuple[str, str]] = []
    chart: Optional[str] = None
    filters: Dict[str, List[str]] = {}

    # rows 추출
    for col, keywords in mapping.get("rows", {}).items():
        if any(kw.lower() in t for kw in keywords):
            rows.append(col)

    # values 추출
    for col, cfg in mapping.get("values", {}).items():
        if any(kw.lower() in t for kw in cfg.get("keywords", [])):
            values.append((col, cfg.get("agg", "sum")))

    # chart 타입 추출
    for ctype, kws in mapping.get("chart", {}).items():
        if any(kw.lower() in t for kw in kws):
            chart = ctype
            break

    # filters 추출
    for fcol, fvals in mapping.get("filters", {}).items():
        for val, kws in fvals.items():
            if any(kw.lower() in t for kw in kws):
                filters.setdefault(fcol, []).append(val)

    return Intent(rows=rows, values=values, chart=chart, filters=filters)

def parse(text: str, *, columns: Optional[List[str]] = None, parser: str = "auto", keyword_map_path: Optional[str] = None) -> Intent:
    """규칙 기반/LLM 파서를 선택적으로 실행."""
    rule_intent = parse_rule(text, keyword_map_path=keyword_map_path)
    if columns:
        allowed = {c.lower() for c in columns}
        rule_intent.rows = [r for r in rule_intent.rows if r.lower() in allowed]
        rule_intent.values = [(col, agg) for col, agg in rule_intent.values if col.lower() in allowed]

    if parser == "rule":
        return rule_intent
    if parser == "llm":
        return parse_with_llm(text, allowed_columns=columns) or rule_intent

    # auto: 규칙 파서 실패시 LLM 사용
    if rule_intent.rows and rule_intent.values:
        return rule_intent
    return parse_with_llm(text, allowed_columns=columns) or rule_intent
