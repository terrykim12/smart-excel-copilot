# app/core/logging.py
import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
) -> None:
    """
    애플리케이션 전체의 로깅을 설정합니다.
    
    Args:
        level: 로깅 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 로그 파일 경로 (None이면 콘솔만 출력)
        log_format: 로그 포맷 문자열
        max_bytes: 로그 파일 최대 크기
        backup_count: 백업 파일 개수
    """
    # 루트 로거 설정
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # 기존 핸들러 제거
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 포맷터 생성
    formatter = logging.Formatter(log_format)
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # 파일 핸들러 (지정된 경우)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 로테이팅 파일 핸들러
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # 외부 라이브러리 로깅 레벨 조정
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("openpyxl").setLevel(logging.WARNING)
    
    # 설정 완료 로그
    logger = logging.getLogger(__name__)
    logger.info(f"Logging setup completed. Level: {level}")
    if log_file:
        logger.info(f"Log file: {log_file}")


def get_logger(name: str) -> logging.Logger:
    """
    모듈별 로거를 반환합니다.
    
    Args:
        name: 보통 __name__을 사용
        
    Returns:
        설정된 로거 인스턴스
    """
    return logging.getLogger(name)


def log_function_call(func):
    """
    함수 호출을 로깅하는 데코레이터입니다.
    
    Usage:
        @log_function_call
        def my_function(arg1, arg2):
            return arg1 + arg2
    """
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"{func.__name__} returned: {result}")
            return result
        except Exception as e:
            logger.error(f"{func.__name__} failed with error: {e}", exc_info=True)
            raise
    return wrapper


def log_performance(func):
    """
    함수 실행 시간을 로깅하는 데코레이터입니다.
    
    Usage:
        @log_performance
        def slow_function():
            time.sleep(1)
    """
    import time
    
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"{func.__name__} executed in {execution_time:.4f} seconds")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} failed after {execution_time:.4f} seconds: {e}", exc_info=True)
            raise
    return wrapper


# 환경 변수 기반 자동 설정
if os.getenv("SEC_LOG_LEVEL"):
    setup_logging(
        level=os.getenv("SEC_LOG_LEVEL"),
        log_file=os.getenv("SEC_LOG_FILE")
    )
