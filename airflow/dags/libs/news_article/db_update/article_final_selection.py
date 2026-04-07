"""
article_final_selection.py (Hybrid: MySQL + MongoDB)

이 모듈은 article_db_handler.py에서 처리된 DB 데이터로부터
최종적으로 사용할 기사 5개를 선정하고, 본문을 크롤링하여 MongoDB에 저장합니다.
- 기사 선정: MySQL (정형 데이터)
- 본문 저장: MongoDB (비정형 텍스트)
- is_used 업데이트: MySQL
"""

import os
import mysql.connector
from pymongo import MongoClient
from datetime import datetime
import json
from dotenv import load_dotenv
load_dotenv()

# MySQL 연결
def get_mysql_connection():
    connect_info = {
        'host': os.environ['OBA_DB_HOST'],
        'database': os.environ['OBA_DB_DATABASE'],
        'user': os.environ['OBA_DB_USER'],
        'password': os.environ['OBA_DB_PASSWORD'],
        'port': int(os.environ.get('OBA_DB_PORT', 3306))
    }
    return mysql.connector.connect(**connect_info)

# MongoDB 연결
def get_mongo_connection():
    mongo_uri = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
    db_name = os.environ.get("MONGO_DB_NAME", "oba")
    client = MongoClient(mongo_uri)
    return client[db_name]

# 상위 5개 기사 선정 함수 (RDS 그대로 유지)
def select_top5_articles():
    """
    Articles 테이블에서
    ordering 내림차순 > dup_cnt 내림차순 > updated_time 내림차순
    순으로 정렬하여 상위 5개 기사(article_id, url) 반환
    """
    db_conn = get_mysql_connection()
    cursor = db_conn.cursor(dictionary=True)

    query = """
        SELECT article_id, url
        FROM Articles
        WHERE is_used != 1
        ORDER BY ordering DESC, dup_cnt DESC, updated_time DESC
        LIMIT 5
    """
    cursor.execute(query)
    top_articles = cursor.fetchall()

    db_conn.commit()
    cursor.close()
    db_conn.close()
    
    return top_articles

# 기사 본문 저장 함수 (MongoDB 저장 + MySQL 상태 업데이트)
def insert_content(article_id, article_content):
    """
    1️⃣ MongoDB에 본문 저장
    2️⃣ MySQL에서 is_used=1로 상태 업데이트
    """
    try:
        # === (0) Category 조회 (MySQL)
        db_conn = get_mysql_connection()
        cursor = db_conn.cursor(dictionary=True)
        query = """
            SELECT c.category_name
            FROM Article_Categories ac
            JOIN Categories c ON ac.category_id = c.category_id
            WHERE ac.article_id = %s
        """
        cursor.execute(query, (article_id,))
        category_names = [row["category_name"] for row in cursor.fetchall()]
        cursor.close()

        # === (1) MongoDB 저장 ===
        mongo_db = get_mongo_connection()
        selected_articles = mongo_db["Selected_Articles"]

        required_fields = ["url", "title", "sub_col", "content_col", "author", "publish_time"]
        for field in required_fields:
            if not article_content.get(field):
                raise ValueError(f"[article_id={article_id}] 필수 필드 누락: {field}")

        data = {
            "article_id": article_id,
            "serving_date": datetime.now().strftime("%Y-%m-%d"),
            "url": article_content.get("url", ""),
            "category_name": category_names,
            "title": article_content.get("title", ""),
            "sub_col": article_content.get("sub_col", ""),
            "content_col": article_content.get("content_col", ""),
            "author": article_content.get("author", ""),
            "publish_time": article_content.get("publish_time", ""),
        }

        selected_articles.update_one(
            {"article_id": article_id},
            {"$set": data},
            upsert=True
        )

        serving_date = datetime.now().strftime("%Y-%m-%d")

        # === (2) MySQL is_used 업데이트 ===
        cursor = db_conn.cursor()
        title = article_content.get("title", "")
        cursor.execute("UPDATE Articles SET is_used = 1, serving_date = %s, title = %s WHERE article_id = %s", (serving_date, title, article_id,))
        db_conn.commit()

        print(f"[✅ SUCCESS] MongoDB 저장 + MySQL 업데이트 완료 (article_id={article_id})")

    except Exception as e:
        print(f"[❌ ERROR] article_id={article_id} 처리 중 오류: {e}")
        raise

    finally:
        cursor.close()
        db_conn.close()


# 테스트용 실행
if __name__ == "__main__":
    import sys
    libs_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
    if libs_path not in sys.path:
        sys.path.insert(0, libs_path)
    try:
        from news_article.crawler.contentCrawling import get_content
    except ImportError:
        print("[ERROR] get_content 함수를 import할 수 없습니다. 경로/모듈명을 확인하세요.")
        sys.exit(1)

    print("[TEST] 상위 5개 기사 선정 중...")
    top_articles = select_top5_articles()

    print(f"[TEST] 선정된 {len(top_articles)}개 기사 본문 MongoDB 저장 시작...")
    for article in top_articles:
        content = get_content(article["url"])
        insert_content(article["article_id"], content)

    print("[TEST] 모든 기사 MongoDB 반영 완료 ✅")
