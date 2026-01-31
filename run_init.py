#!/usr/bin/env python3
"""
리팩토링된 공통 모듈 사용 예: DB 초기화만 수행.
기존 db_manager.py 대신 사용 가능. (기존 파일은 유지)
"""
from src.db import init_dbs

if __name__ == "__main__":
    init_dbs()
    print("뷰 생성이 필요하면: python setup_views.py")
