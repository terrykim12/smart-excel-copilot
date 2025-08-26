# tests/test_clean.py
import pytest
import pandas as pd
import numpy as np
from app.excel_ops.clean import _parse_date_fast, level1_clean


class TestDateParsing:
    """날짜 파싱 기능 테스트"""
    
    def test_iso_date_format(self):
        """ISO 형식 날짜 파싱 테스트"""
        s = pd.Series(["2024-01-01", "2024-12-31", "invalid"])
        result, hit_ratio = _parse_date_fast(s, keep_time=False)
        
        assert hit_ratio > 0.5
        assert result.iloc[0] == "2024-01-01"
        assert result.iloc[1] == "2024-12-31"
        assert pd.isna(result.iloc[2])
    
    def test_slash_date_format(self):
        """슬래시 형식 날짜 파싱 테스트"""
        s = pd.Series(["2024/01/01", "2024/12/31"])
        result, hit_ratio = _parse_date_fast(s, keep_time=False)
        
        assert hit_ratio > 0.9
        assert result.iloc[0] == "2024-01-01"
        assert result.iloc[1] == "2024-12-31"
    
    def test_dot_date_format(self):
        """점 형식 날짜 파싱 테스트"""
        s = pd.Series(["2024.01.01", "2024.12.31"])
        result, hit_ratio = _parse_date_fast(s, keep_time=False)
        
        assert hit_ratio > 0.9
        assert result.iloc[0] == "2024-01-01"
        assert result.iloc[1] == "2024-12-31"
    
    def test_contiguous_date_format(self):
        """연속 날짜 형식 (YYYYMMDD) 파싱 테스트"""
        s = pd.Series(["20240101", "20241231", "invalid"])
        result, hit_ratio = _parse_date_fast(s, keep_time=False)
        
        assert hit_ratio > 0.5
        assert result.iloc[0] == "2024-01-01"
        assert result.iloc[1] == "2024-12-31"
        assert pd.isna(result.iloc[2])
    
    def test_custom_date_format(self):
        """사용자 정의 날짜 형식 파싱 테스트"""
        s = pd.Series(["20240101", "20241231"])
        result, hit_ratio = _parse_date_fast(s, keep_time=False, date_fmt="YYYYMMDD")
        
        assert hit_ratio > 0.9
        assert result.iloc[0] == "2024-01-01"
        assert result.iloc[1] == "2024-12-31"
    
    def test_datetime_with_time(self):
        """시간이 포함된 날짜 파싱 테스트"""
        s = pd.Series(["2024-01-01 10:00:00", "2024-12-31 23:59:59"])
        result, hit_ratio = _parse_date_fast(s, keep_time=True)
        
        assert hit_ratio > 0.9
        assert "10:00:00" in result.iloc[0]
        assert "23:59:59" in result.iloc[1]
    
    def test_mixed_date_formats(self):
        """혼합 날짜 형식 파싱 테스트"""
        s = pd.Series(["2024-01-01", "2024/12/31", "2024.06.15", "20240615"])
        result, hit_ratio = _parse_date_fast(s, keep_time=False)
        
        assert hit_ratio > 0.9
        assert result.iloc[0] == "2024-01-01"
        assert result.iloc[1] == "2024-12-31"
        assert result.iloc[2] == "2024-06-15"
        assert result.iloc[3] == "2024-06-15"


class TestLevel1Clean:
    """Level1 클리닝 기능 테스트"""
    
    def test_date_column_processing(self):
        """날짜 컬럼 처리 테스트"""
        df = pd.DataFrame({
            "날짜": ["2024-01-01", "2024/12/31", "2024.06.15"],
            "금액": ["1000원", "2000₩", "3000"],
            "도시": ["서울", "부산", "대구"]
        })
        
        result = level1_clean(df, date_fmt="YYYY-MM-DD")
        
        # 날짜 컬럼이 표준화되었는지 확인
        assert "날짜" in result.columns
        # 금액 컬럼이 숫자로 변환되었는지 확인
        assert pd.api.types.is_numeric_dtype(result["금액"])
    
    def test_currency_processing(self):
        """통화 처리 테스트"""
        df = pd.DataFrame({
            "금액": ["₩1000", "1000원", "$50", "€30", "¥100"]
        })
        
        result = level1_clean(df, currency_split=True)
        
        # 통화 컬럼이 생성되었는지 확인
        assert "금액__currency" in result.columns
        # 금액이 숫자로 변환되었는지 확인
        assert pd.api.types.is_numeric_dtype(result["금액"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
