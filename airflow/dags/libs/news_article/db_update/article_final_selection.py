"""
article_final_selection.py

이 모듈은 article_db_handler.py에서 처리된 DB 데이터로부터
최종적으로 사용할 기사 5개를 선정하고, 본문을 크롤링하여 Selected_Articles 테이블에 저장하는 역할을 합니다.
- dup_cnt 내림차순 → article_ordering 내림차순 → updated_time 내림차순으로 정렬
- 상위 5개 기사 선정 및 is_used=1로 업데이트
- 기사 링크 본문 크롤링
- 크롤링 결과와 날짜를 Selected_Articles에 저장
"""

import os
import mysql.connector
import json
from dotenv import load_dotenv
load_dotenv()

# DB 연결 함수
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

# 상위 5개 기사 선정 함수
def select_top5_articles():
    """
    Articles 테이블에서
    article_ordering 내림차순 >  dup_cnt 내림차순 > updated_time 내림차순
    순으로 정렬하여 상위 5개 기사(article_id, link) 반환
    """
    db_conn = get_db_connection()
    cursor = db_conn.cursor(dictionary=True)

    # 1. 싱위 5개 기사 선정
    query = """
        SELECT article_id, url
        FROM Articles
        WHERE is_used != 1
        ORDER BY ordering DESC, dup_cnt DESC, updated_time DESC
        LIMIT 5
    """
    cursor.execute(query)
    top_articles = cursor.fetchall()


    # 모든 변경사항 커밋 및 연결 종료
    db_conn.commit()
    cursor.close()
    db_conn.close()
    
    return top_articles

def insert_content(article_id, article_content):
    """
        return {
        "url": url,
        "title": title,
        "tags": tags,
        "publish_time": publish_time,
        "author": author,
        "sub_col": sub_col,
        "content_col": content_col,
    }을 입력받고, Selected_Articles 테이블에 업데이트한다.
    """
    try: 
        db_conn = get_db_connection()
        cursor = db_conn.cursor(dictionary=True)

        # 1. article_id 기준으로 Categories 테이블에서 이름 바로 조회 (JOIN)
        query = """
            SELECT c.category_name
            FROM Article_Categories ac
            JOIN Categories c ON ac.category_id = c.category_id
            WHERE ac.article_id = %s
        """
        cursor.execute(query, (article_id,))
        category_names = [row["category_name"] for row in cursor.fetchall()]

        # 2. JSON 문자열 변환
        categories = json.dumps(category_names, ensure_ascii=False)
        
        # 필수 필드 검증
        required_fields = ["url", "title","sub_col", "content_col", "author", "publish_time"]
        for field in required_fields:
            if not article_content.get(field):
                raise ValueError(f"[article_id={article_id}] 필수 필드 누락: {field}")
            
        # 3. 백엔드에 전달할 테이블 업데이트
        query = """
            INSERT INTO Selected_Articles (
                article_id, serving_date, url, category_name,
                title, sub_col, content_col, author, publish_time
            )
            VALUES (%s, CURDATE(), %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                serving_date = CURDATE(),
                url = VALUES(url),
                category_name = VALUES(category_name),
                title = VALUES(title),
                sub_col = VALUES(sub_col),
                content_col = VALUES(content_col),
                author = VALUES(author),
                publish_time = VALUES(publish_time)
        """
        cursor.execute(query, (
            article_id,
            article_content.get("url", ""),
            categories,
            article_content.get("title", ""),
            json.dumps(article_content.get("sub_col"), ensure_ascii=False),
            json.dumps(article_content.get("content_col"), ensure_ascii=False),
            article_content.get("author", ""),
            article_content.get("publish_time", ""),
        ))

        # 4. is_used 상태 업데이트
        query = """
            UPDATE Articles
            SET is_used = 1
            WHERE article_id = %s
        """
        cursor.execute(query, (article_id,)) 

        db_conn.commit() # 모든 변경사항 커밋

    except Exception as e:
            print(f"article_id: {article_id}에서 오류 발생. {article_content['url']}")
            print(f"⚠️ 오류 메세지: {e}")
            raise
    
    finally:
        # 연결 종료
        cursor.close()
        db_conn.close()

if __name__ == "__main__":
    # 테스트용: DB 갱신 함수 실행
    import sys
    # airflow/dags/libs를 PYTHONPATH에 추가하여 news_article.crawler.contentCrawling import가 정상 동작하도록 함
    libs_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
    if libs_path not in sys.path:
        sys.path.insert(0, libs_path)
    try:
        from news_article.crawler.contentCrawling import get_content
    except ImportError:
        print("[ERROR] get_content 함수를 import할 수 없습니다. 경로/모듈명을 확인하세요.")
        sys.exit(1)

    top_articles = select_top5_articles()

    print(f"[TEST] 크롤링 선정 기사 DB 반영 시작...")

    # 선정된 5개 기사를 하나씩 크롤링 후 insert
    for article in top_articles:
        article_content = get_content(article["url"])
        insert_content(article["article_id"], article_content)

    print("[TEST] DB 반영 완료!")