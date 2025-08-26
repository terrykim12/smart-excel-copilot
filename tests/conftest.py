import os
import pytest
import sys

@pytest.fixture(autouse=True, scope="session")
def _force_utf8_env():
    """테스트 세션 전체에 UTF-8 환경을 강제합니다."""
    # 환경 변수 강제 설정
    os.environ["PYTHONIOENCODING"] = "utf-8"
    os.environ["LC_ALL"] = "C.UTF-8"
    os.environ["LANG"] = "C.UTF-8"
    
    # Windows에서 추가 UTF-8 설정
    if os.name == "nt":
        os.environ["PYTHONLEGACYWINDOWSSTDIO"] = "utf-8"
        # Windows 콘솔 인코딩 강제
        if hasattr(sys.stdout, 'reconfigure'):
            try:
                sys.stdout.reconfigure(encoding='utf-8')
                sys.stderr.reconfigure(encoding='utf-8')
            except Exception:
                pass
    
    print(f"✅ UTF-8 환경 설정 완료: PYTHONIOENCODING={os.environ.get('PYTHONIOENCODING')}")
    print(f"✅ LC_ALL={os.environ.get('LC_ALL')}, LANG={os.environ.get('LANG')}")
