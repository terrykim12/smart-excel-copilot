#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from autoexcel.engines_com import create_pivot_chart

def test_chart_creation():
    """차트 생성 기능을 테스트합니다."""
    
    # 테스트 파일 경로
    input_file = "data/automation/auto_demo.xlsx"
    output_file = "data/out/test_chart_output.xlsx"
    
    # 출력 디렉토리 생성
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    print("=== 차트 생성 테스트 시작 ===")
    print(f"입력 파일: {input_file}")
    print(f"출력 파일: {output_file}")
    
    try:
        # 피벗 차트 생성 테스트
        create_pivot_chart(
            path_in=input_file,
            path_out=output_file,
            src_sheet="Sheet1",  # 첫 번째 시트
            tgt_sheet="피벗차트",
            rows=["주문일"],  # 행 필드
            values=[("금액", "sum")],  # 값 필드
            chart_type="bar"  # 막대 차트
        )
        
        print(f"✅ 차트 생성 성공! 출력 파일: {output_file}")
        
        # 파일 존재 확인
        if os.path.exists(output_file):
            print(f"✅ 출력 파일이 정상적으로 생성되었습니다.")
            file_size = os.path.getsize(output_file)
            print(f"파일 크기: {file_size:,} bytes")
        else:
            print("❌ 출력 파일이 생성되지 않았습니다.")
            
    except Exception as e:
        print(f"❌ 차트 생성 실패: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = test_chart_creation()
    if success:
        print("\n🎉 모든 테스트가 성공적으로 완료되었습니다!")
    else:
        print("\n💥 테스트 중 오류가 발생했습니다.")
        sys.exit(1)
