# Changelog

## v0.5.0-rc1
- M0.5 완전 구현(프로파일링/레벨1 클리닝/중복/레시피 재실행)
- 120k clean 16.3s → 1.78s 최적화(날짜/통화/불리언 FastPath)

## v0.5.0 (M0.5 완료)

- 프로파일링: 타입 추론(숫자/통화/날짜/불리언), 샘플 통계 제공
- 레벨1 클리닝: 열명 표준화, 공백 정리, 통화/숫자/날짜/불리언 표준화, 빈 행/열 제거
- 중복 제거: 키 자동 매핑(snake_case), keep=first/last/last_by:<열>
- CLI: profile, clean, dedupe, impute, outlier, schema 추가
- 레시피 시스템(M2 스켈레톤): 저장/목록/로드 구조, replay 준비
- 성능: 50k 행 기준 clean ~6s, 전체 ~6.6s(@SSD)
- 안정성: 정규식 경고 제거(비캡처 그룹), 키 매핑 견고화
