
"""
article_db_handler.py

크롤링한 기사 데이터를 받아 Articles, Categories, Article_Categories 테이블을 갱신
1. 기존 기사라면 ordering 누적, dup_cnt 증가, Article_Categories 조합 없으면 추가
2. 신규 기사라면 Articles/Article_Categories/카테고리 모두 추가

동작 요약:
1. 기존 Articles 테이블에 있는 기사(url 기준)라면 ordering 누적, dup_cnt 증가, Article_Categories 조합 없으면 추가
2. 신규 기사라면 Articles/Article_Categories/카테고리 모두 추가

입력 데이터 예시:
    crawled_articles = [
        {
            'url': 'https://news.example.com/1',
            'ordering': 10,
            'category': 3,  # category_id (int)
            'crawling_time': datetime_obj,
            'updated_time': datetime_obj
        },
        ...
    ]
"""

import os
import mysql.connector
import datetime
from dotenv import load_dotenv
load_dotenv()

def get_db_connection():
    """
    환경변수에서 DB 접속 정보를 읽어 MySQL DB 연결 반환
    Returns:
        MySQLConnection 객체
    
    """
    connect_info = {
        'host': os.environ['OBA_DB_HOST'],
        'database': os.environ['OBA_DB_DATABASE'],
        'user': os.environ['OBA_DB_USER'],
        'password': os.environ['OBA_DB_PASSWORD'],
        'port': int(os.environ.get('OBA_DB_PORT', 3306))
    }
    return mysql.connector.connect(**connect_info)

def process_crawled_articles(crawled_articles):
    """
    크롤링한 기사 리스트를 받아 DB를 효율적으로 갱신합니다.
    - 기존 기사: ordering 누적, dup_cnt 증가, Article_Categories 조합 없으면 추가
    - 신규 기사: Articles/Article_Categories/카테고리 모두 추가
    
    Parameters
    - crawled_articles (list[dict]): 크롤링 결과 기사 리스트
            각 dict는 {'url': str, 'ordering': int, 'category': int, ...} 구조
    """
    db_conn = get_db_connection()
    cursor = db_conn.cursor()

    # 1. 기존 기사(Articles) 정보 한 번에 조회 (url 기준)
    cursor.execute("SELECT article_id, url, dup_cnt, ordering FROM Articles")
    url_to_article = {row[1]: {'article_id': row[0], 'dup_cnt': row[2], 'ordering': row[3]} for row in cursor.fetchall()}
    # ex. {{'https://a.com/news1': {'article_id': 1, 'dup_cnt': 2, 'ordering': 15}, ...}

    # 2. 기존 기사-카테고리(Article_Categories) 조합 미리 조회
    cursor.execute("SELECT article_id, category_id FROM Article_Categories")
    existing_pairs = set((row[0], row[1]) for row in cursor.fetchall())

    # 3. 기사별로 분기 처리 (중복/신규)
    for article in crawled_articles:
        url = article['url']
        ordering = article['ordering']
        category_id = article['category']

        crawling_time = article.get('crawling_time')  # datetime 또는 None
        updated_time = datetime.datetime.now()

        # 신규 기사가 이미 Articles에 존재한다면
        if url in url_to_article:
            # === 기존 기사 ===
            article_id = url_to_article[url]['article_id']

            # 확인용 테이블(4checking_articles)에 추가
            # cursor.execute(
            #     "INSERT INTO 4checking_articles (article_id, crawling_time, category_id) VALUES (%s, %s, %s)",
            #     (article_id, crawling_time, category_id)
            # )

            new_dup_cnt = url_to_article[url]['dup_cnt'] + 1 # 중복 횟수 1회 증가

            # ordering 누적, dup_cnt 증가
            cursor.execute(
                "UPDATE Articles SET ordering = ordering + %s, dup_cnt = %s WHERE article_id = %s",
                (ordering, new_dup_cnt, article_id)
            )
            
            url_to_article[url]['dup_cnt'] = new_dup_cnt

            # Article_Categories 조합 없으면 추가
            if (article_id, category_id) not in existing_pairs:
                cursor.execute(
                    "INSERT INTO Article_Categories (article_id, category_id) VALUES (%s, %s)",
                    (article_id, category_id)
                )
                existing_pairs.add((article_id, category_id))


        else: # 신규 기사가 Articles에 존재하지 않는다면
            # === 신규 기사 ===
            cursor.execute(
                "INSERT INTO Articles (url, ordering, crawling_time, updated_time, dup_cnt, is_used) VALUES (%s, %s, %s, %s, %s, %s)",
                (url, ordering, crawling_time, updated_time, 1, 0)
            )

            article_id = cursor.lastrowid

            # 확인용 테이블(4checking_articles)에 추가
            # cursor.execute(
            #     "INSERT INTO 4checking_articles (article_id, crawling_time, category_id) VALUES (%s, %s, %s)",
            #     (article_id, crawling_time, category_id)
            # )

            # 새 기사를 Articles 테이블에 삽입하면, DB가 자동으로 article_id(예: AUTO_INCREMENT)를 생성
            url_to_article[url] = {'article_id': article_id, 'dup_cnt': 1, 'ordering': ordering}

            # Article_Categories 조합 추가
            if (article_id, category_id) not in existing_pairs:
                cursor.execute(
                    "INSERT INTO Article_Categories (article_id, category_id) VALUES (%s, %s)",
                    (article_id, category_id)
                )
                existing_pairs.add((article_id, category_id))

    # 모든 변경사항 커밋 및 연결 종료

    db_conn.commit()
    cursor.close()
    db_conn.close()


if __name__ == "__main__":
    # 테스트용: 크롤러에서 기사 링크 데이터 받아와서 DB 갱신 함수 실행
    import sys
    # airflow/dags/libs를 PYTHONPATH에 추가하여 news_article.crawler.linkCrawling import가 정상 동작하도록 함
    libs_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
    if libs_path not in sys.path:
        sys.path.insert(0, libs_path)
    try:
        from news_article.crawler.linkCrawling import get_article_link
    except ImportError:
        print("[ERROR] get_article_link 함수를 import할 수 없습니다. 경로/모듈명을 확인하세요.")
        sys.exit(1)

    # get_article_link()는 크롤링된 기사 리스트 반환 (예시: [{'url':..., 'ordering':..., 'category':..., ...}, ...])
    crawled_articles = get_article_link()
    print(f"[TEST] 크롤링 기사 {len(crawled_articles)}건 DB 반영 시작...")
    process_crawled_articles(crawled_articles)
    print("[TEST] DB 반영 완료!")
