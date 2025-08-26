#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
자연어 파서 테스트
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

def test_intent_parsing():
    """의도 파싱 테스트"""
    print("=== 자연어 의도 파싱 테스트 ===")
    
    try:
        from app.autoexcel.intent import parse
        
        test_cases = [
            "월별 카테고리 매출 피벗 만들고 막대차트",
            "카테고리별 수량 합계를 라인차트로",
            "지역별 매출을 파이차트로 보여줘"
        ]
        
        for text in test_cases:
            print(f"\n입력: {text}")
            intent = parse(text)
            print(f"결과: {intent}")
            
    except Exception as e:
        print(f"오류: {e}")

def test_llm_fallback():
    """LLM 백업 테스트"""
    print("\n=== LLM 백업 테스트 ===")
    
    try:
        from app.autoexcel.intent_llm import parse_with_llm
        
        test_text = "복잡한 요청: 월별 지역별 카테고리별 매출과 수량을 피벗으로 만들고 막대차트와 라인차트를 모두 생성해줘"
        print(f"입력: {test_text}")
        
        # 컬럼 힌트가 있는 경우
        columns = ['월', '지역', '카테고리', '매출', '수량']
        result = parse_with_llm(test_text, allowed_columns=columns)
        if result:
            print(f"LLM 결과 (컬럼 힌트 포함): {result}")
        else:
            print("LLM 파싱 실패 - 규칙 파서로 폴백")
            
    except Exception as e:
        print(f"LLM 테스트 오류: {e}")

def test_parser_selection():
    """파서 선택 테스트"""
    print("\n=== 파서 선택 테스트 ===")
    
    try:
        from app.autoexcel.intent import parse
        
        test_text = "월별 카테고리 매출 피벗 만들고 막대차트"
        columns = ['월', '카테고리', '매출', '수량']
        
        print(f"입력: {test_text}")
        print(f"컬럼: {columns}")
        
        # 규칙 파서
        rule_result = parse(test_text, columns=columns, parser="rule")
        print(f"규칙 파서: {rule_result}")
        
        # LLM 파서
        llm_result = parse(test_text, columns=columns, parser="llm")
        print(f"LLM 파서: {llm_result}")
        
        # 자동 파서
        auto_result = parse(test_text, columns=columns, parser="auto")
        print(f"자동 파서: {auto_result}")
        
    except Exception as e:
        print(f"파서 선택 테스트 오류: {e}")

if __name__ == "__main__":
    test_intent_parsing()
    test_llm_fallback()
    test_parser_selection()
