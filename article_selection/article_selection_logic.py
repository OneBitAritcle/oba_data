from bs4 import BeautifulSoup
import requests
import time
import pandas as pd
import numpy as np
import re
import random
from datetime import datetime

def get_articles_from_categories(categories):
    """
    Parameter
    - categories: 추출하려는 기사 카테고리들이 담긴 리스트 (List[str])

    Return
    - all_articles: 모든 카테고리에 해당하는 기사 정보를 담은 딕셔너리의 리스트
    """
    
    all_articles = []  # 모든 결과를 통합할 빈 리스트
    crawling_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # 수집 시간은 작업 시작 시 한 번만 기록

    # 전달받은 카테고리 리스트를 순회
    for category in categories:
        # 진행 상황을 알 수 있도록 현재 크롤링 중인 카테고리 출력
        print(f"'{category}' 카테고리에서 기사 링크를 수집 중입니다...")
        
        main_url = f'https://www.itworld.co.kr/{category}/page/1/'

        try:
            r = requests.get(main_url)
            r.raise_for_status()  # 200 OK 상태 코드가 아닐 경우 예외 발생
            time.sleep(random.randint(1, 3))

            soup = BeautifulSoup(r.text, "html.parser")
            content_items = soup.select("#article")
            content_items = str(content_items)

            pattern = r'href="((?!#)(?![^"]*page/)[^"]+)"'
            links = re.findall(pattern, content_items)
            
            # 해당 카테고리에서 찾은 링크들을 순회하며 데이터 조합
            for i, link_url in enumerate(links):
                article_data = {
                    'crawling_time': crawling_time,
                    'category': category,
                    'article_order': i + 1,
                    'url': link_url
                }
                # 개별 기사 정보를 최종 결과 리스트에 추가
                all_articles.append(article_data)
        
        except requests.exceptions.RequestException as e:
            # 특정 카테고리에서 에러 발생 시 건너뛰고 다음 카테고리 진행
            print(f"'{category}' 처리 중 에러 발생: {e}")
            continue

    return all_articles

today_crawled_links = get_articles_from_categories(['artificial-intelligence', 'generative-ai'])
df = pd.DataFrame(today_crawled_links)
df.to_csv('today_crawled_links.csv', index=False, encoding='utf-8-sig') 

import mysql.connector

# MySQL 연결 설정
connect_info = {
    'host': 'mydbinstance.cb4iuuq0kuoa.ap-southeast-2.rds.amazonaws.com',
    'database': 'oba_article',
    'user': 'admin',
    'password': 'obaoba12',
    'port': 3306  # 기본 포트
}

def get_top_5_most_duplicated_articles(today_crawled_links):
    """
    오늘 크롤링한 데이터와 기존 데이터를 합쳐서 중복 횟수가 가장 많은 상위 5개 기사를 찾는 함수

    Parameters:
    - today_crawled_links: 오늘 크롤링한 기사 링크 목록 (딕셔너리 리스트 형태)
                        ex. [{'crawling_time': '2025-08-19 15:30:00', 'category': 'IT', 'article_order': 1, 'url': 'http://example.com/article1'}]
    :return: 중복 횟수가 가장 많은 상위 5개 기사 목록
    """
    conn = None
    cursor = None

    try:
        conn = mysql.connector.connect(**connect_info)
        cursor = conn.cursor()

        # 1. 오늘 크롤링한 데이터를 임시 테이블에 저장하기 위한 SQL
        cursor.execute("""
            CREATE TEMPORARY TABLE IF NOT EXISTS today_crawled_temp (
                crawling_time DATETIME NOT NULL,
                category VARCHAR(100) NOT NULL,
                url TEXT NOT NULL,
                article_order INT NOT NULL
            );
        """)

        # 2. Python 리스트의 데이터 임시 테이블에 삽입
        if today_crawled_links:
            insert_temp_query = """
            INSERT INTO today_crawled_temp (crawling_time, category, article_order, url)
            VALUES (%s, %s, %s, %s)
            """
            data_to_insert = [
                (link['crawling_time'], link['category'], link['article_order'], link['url'])
                for link in today_crawled_links
            ]
            cursor.executemany(insert_temp_query, data_to_insert)
            conn.commit()

        # 3. 기존 article_links 테이블의 중복 데이터를 업데이트
        # dup_count 증가, crawling_time 업데이트, category 추가
        # update_query = """
        # UPDATE article_links AS a
        # JOIN today_crawled_temp AS t ON a.url = t.url
        # SET
        #     a.dup_count = a.dup_count + 1,
        #     a.crawling_time = t.crawling_time,
        #     a.category = CASE
        #         -- 기존 카테고리 목록에 새로운 카테고리가 이미 포함되어 있는지 확인합니다.
        #         WHEN FIND_IN_SET(t.category, a.category) > 0 THEN a.category
        #         ELSE CONCAT(a.category, ',', t.category)
        #     END;
        # """
        update_query = """
            INSERT INTO article_links (url, crawling_time, category, article_order, dup_count)
            SELECT 
                url, 
                MAX(crawling_time), 
                GROUP_CONCAT(DISTINCT category), 
                MIN(article_order), 
                COUNT(*) as cnt
            FROM today_crawled_temp
            GROUP BY url
            ON DUPLICATE KEY UPDATE
                dup_count = article_links.dup_count + VALUES(dup_count),
                crawling_time = VALUES(crawling_time),
                category = CASE
                    WHEN FIND_IN_SET(VALUES(category), article_links.category) > 0 THEN article_links.category
                    ELSE CONCAT(article_links.category, ',', VALUES(category))
                END;
        """
        cursor.execute(update_query)
        conn.commit()

        # 4. 기존 테이블에 없는 새로운 링크를 추가
        insert_new_query = """
        INSERT INTO article_links (crawling_time, category, article_order, url, dup_count)
        SELECT
            t.crawling_time,
            t.category,
            t.article_order,
            t.url,
            1 AS dup_count
        FROM today_crawled_temp AS t
        LEFT JOIN article_links AS a ON t.url = a.url
        WHERE a.url IS NULL;
        """
        cursor.execute(insert_new_query)
        conn.commit()

        # 5. 모든 데이터에서 중복 횟수가 가장 많은 상위 5개 링크를 추출 - 구체화 필요
        # if 중복이 없어서 id 기준 정렬이 된다면 그냥 그대로 보여줄 것인가? crawling_time이 가깝거나 먼 것 먼저 보여 줄 것인가?
        select_query = """
        SELECT
            id, crawling_time, category, url, dup_count
        FROM article_links
        ORDER BY dup_count DESC, crawling_time DESC
        LIMIT 5;
        """
        cursor.execute(select_query)
        top_5_articles = cursor.fetchall()

        return top_5_articles

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return []

    finally:
        if conn:
            # 임시 테이블을 삭제합니다.
            if cursor:
                cursor.execute("DROP TEMPORARY TABLE IF EXISTS today_crawled_temp;")
                cursor.close()
            conn.close()

result = get_top_5_most_duplicated_articles(today_crawled_links)
print(result)