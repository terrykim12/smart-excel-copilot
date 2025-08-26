# tests/test_intent.py
import pytest
import pandas as pd
from app.autoexcel.intent import parse_rule, parse, _load_keyword_map


class TestIntentParsing:
    """자연어 의도 파싱 테스트"""
    
    def test_basic_row_extraction(self):
        """기본 행 추출 테스트"""
        text = "월별 카테고리별 매출 분석"
        intent = parse_rule(text)
        
        assert "월" in intent.rows
        assert "카테고리" in intent.rows
        assert len(intent.rows) == 2
    
    def test_value_extraction(self):
        """값 추출 테스트"""
        text = "금액과 수량을 합계로 보여줘"
        intent = parse_rule(text)
        
        assert ("금액", "sum") in intent.values
        assert ("수량", "sum") in intent.values
        assert len(intent.values) == 2
    
    def test_chart_type_extraction(self):
        """차트 타입 추출 테스트"""
        text = "막대차트로 보여줘"
        intent = parse_rule(text)
        
        assert intent.chart == "bar"
    
    def test_filter_extraction(self):
        """필터 추출 테스트"""
        text = "서울과 부산 지역의 매출을 보여줘"
        intent = parse_rule(text)
        
        assert "도시" in intent.filters
        assert "서울" in intent.filters["도시"]
        assert "부산" in intent.filters["도시"]
    
    def test_complex_query(self):
        """복합 쿼리 테스트"""
        text = "월별 카테고리별 매출을 막대차트로 보여주고, 서울과 부산만 필터링해줘"
        intent = parse_rule(text)
        
        assert "월" in intent.rows
        assert "카테고리" in intent.rows
        assert ("금액", "sum") in intent.values
        assert intent.chart == "bar"
        assert "서울" in intent.filters.get("도시", [])
        assert "부산" in intent.filters.get("도시", [])
    
    def test_english_keywords(self):
        """영어 키워드 테스트"""
        text = "monthly sales by category in bar chart"
        intent = parse_rule(text)
        
        assert "월" in intent.rows
        assert "카테고리" in intent.rows
        assert ("금액", "sum") in intent.values
        assert intent.chart == "bar"
    
    def test_mixed_language(self):
        """혼합 언어 테스트"""
        text = "월별 category별 sales를 bar chart로"
        intent = parse_rule(text)
        
        assert "월" in intent.rows
        assert "카테고리" in intent.rows
        assert ("금액", "sum") in intent.values
        assert intent.chart == "bar"


class TestIntentWithColumns:
    """컬럼 제약 조건이 있는 의도 파싱 테스트"""
    
    def test_column_filtering(self):
        """컬럼 필터링 테스트"""
        text = "월별 카테고리별 매출 분석"
        columns = ["월", "도시", "금액"]  # 카테고리 없음
        
        intent = parse(text, columns=columns)
        
        assert "월" in intent.rows
        assert "카테고리" not in intent.rows  # 필터링됨
        assert ("금액", "sum") in intent.values
    
    def test_no_matching_columns(self):
        """매칭되는 컬럼이 없는 경우 테스트"""
        text = "존재하지 않는 컬럼 분석"
        columns = ["월", "도시", "금액"]
        
        intent = parse(text, columns=columns)
        
        assert len(intent.rows) == 0
        assert len(intent.values) == 0


class TestParserSelection:
    """파서 선택 테스트"""
    
    def test_rule_parser(self):
        """규칙 파서 테스트"""
        text = "월별 매출"
        intent = parse(text, parser="rule")
        
        assert "월" in intent.rows
        assert ("금액", "sum") in intent.values
    
    def test_auto_parser_fallback(self):
        """자동 파서 폴백 테스트"""
        text = "복잡한 자연어 쿼리"  # 규칙에 매칭되지 않음
        intent = parse(text, parser="auto")
        
        # 규칙 파서가 실패하면 LLM으로 폴백 (LLM이 없으면 빈 결과)
        assert isinstance(intent.rows, list)
        assert isinstance(intent.values, list)


class TestKeywordMap:
    """키워드 맵 테스트"""
    
    def test_default_keyword_map(self):
        """기본 키워드 맵 테스트"""
        mapping = _load_keyword_map()
        
        assert "rows" in mapping
        assert "values" in mapping
        assert "chart" in mapping
        assert "filters" in mapping
        
        # 기본 키워드들이 포함되어 있는지 확인
        assert "월" in mapping["rows"]
        assert "카테고리" in mapping["rows"]
        assert "금액" in mapping["values"]
        assert "bar" in mapping["chart"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
