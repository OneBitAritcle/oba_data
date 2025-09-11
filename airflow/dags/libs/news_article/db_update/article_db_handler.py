"""
article_db_handler.py

이 모듈은 오늘 크롤링한 기사 데이터를 받아서,
Articles 및 Article_categories DB 테이블과 비교 및 갱신 작업을 수행합니다.
- 기존 기사와 비교하여 ordering 필드와 dup_cnt(중복 카운트) 업데이트
- Article_categories에 없는 새 정보 추가
- 새로운 기사라면 Articles 및 Article_categories에 모두 추가
"""

# DB 연결 및 쿼리 실행 함수
def get_db_connection():
    # DB 연결 객체를 반환
    pass

# Article_categories 테이블에 새 정보 추가 함수
def update_existing_article(new_articles, db_conn):
    """
    기존 기사라면:
    - ordering, dup_cnt 업데이트
    - Article_categories에 카테고리가 없으면 새 카테고리 추가
    """
    pass

# Articles 및 Article_categories 테이블에 새 기사 추가 함수
def insert_new_articles(new_articles, db_conn):
    """
    DB에 없는 새로운 기사라면 Articles, Article_categories 테이블에 모두 추가한다.
    """
    pass

# 전체 프로세스를 실행하는 메인 함수
def process_crawled_articles(crawled_articles):
    """
    오늘 크롤링한 기사들을 받아 DB 갱신을 단일 루프로 처리한다.
    1. DB 연결
    2. 기존 기사 전체 조회
    3. 단일 루프에서 각 기사별로
       - 중복 여부 확인
       - 중복: update_existing_article 호출
       - 신규: insert_new_article 호출
    """
    pass