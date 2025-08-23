"""
해당 파일은 '사용자에게 제공할 5개의 기사를 선정하는 로직'이며 다음과 같은 작업을 수행한다.
1. aritcle_links 테이블에서 전체 link
2. 실행 시점 기준 오늘 크롤링해온 기사와, 1에서 불러온 기사 목록을 합쳐서 중복된 횟수를 센다.
3. 중복된 횟수가 많은 순서대로 정렬한다.
4. 중복수가 많은 기사부터 순차적으로 5개를 사용자에게 제공한다.
    4-1. 만약, 동일한 중복수가 다수 존재한다면 더 최근 기사를 제공한다.
    4-2. 만약, 기사의 날짜도 동일하다면 .... (더 많은 카테고리를 포함한 기사를 선택한다?)
"""

import mysql.connector
from collections import Counter
from datetime import datetime
from typing import List, Dict, Any

# 데이터베이스 설정
## Airflow의 Variable이나 외부 파일로 관리될 수 있음
DB_CONFIG = {
    'user': 'your_user',
    'password': 'your_password',
    'host': 'your_host',
    'database': 'your_database'
}

# ======= 1. 사용자에게 제공되지 않은 기사 불러오기 ======
def fetch_unseen_articles(db_config, table_name):
    """
    Parameters
    - db_config: 접근할 데이터베이스 정보
    - table_name: 데이터베이스 내의 불러올 테이블 명 정의
    """ 
    conn = None
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        # 데이터베이스 PK 확실히 해야함
        query = f"""
        SELECT tb.order, tb.URL, tb.crawlingtime, tb.category
        FROM {table_name} as tb
        """

        cursor.execute(query)
        previous_articles = cursor.fetchall()
        print(f"DEBUG: 미제공 기사 수: {len(previous_articles)}")

        return previous_articles
    
    except mysql.connector.Error as err:
        print(f"데이터베이스 조회 오류: {err}")
        return []
    
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


# ======= 2. 모든 기사를 합친 후 중복 횟수를 세는 함수 ======
def count_article_duplicates(previous_articles, new_articles):
    """
    Parameters
    - previous_articles: 함수 실행 시점 오늘 이전 크롤링해온 기사 중 사용자에게 제공되지 않은 기사 목록
    - new_articles: 함수 실행 시점 오늘 크롤링해온 기사 목록
    """
    all_articles = previous_articles + new_articles

    
