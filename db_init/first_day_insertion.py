
import os
import sys
import mysql.connector
import datetime


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../airflow/dags/libs')))

from news_article.crawler.linkCrawling import get_article_link
from news_article.db_update.article_db_handler import get_db_connection


def insert_articles():
    db_conn = get_db_connection()
    cursor = db_conn.cursor()
    articles = get_article_link()
    for article in articles:
        url = article['url']
        ordering = article['ordering']
        category_id = article['category']  # get_article_link()가 category_id(int)를 반환한다고 가정
        crawling_time = article.get('crawling_time', datetime.datetime.now())
        updated_time = article.get('updated_time', datetime.datetime.now())

        # 1. 기사 추가 (중복 url은 skip)
        cursor.execute("SELECT article_id FROM Articles WHERE url = %s", (url,))
        art_row = cursor.fetchone()
        if not art_row:
            cursor.execute(
                "INSERT INTO Articles (url, ordering, crawling_time, updated_time, dup_cnt, is_used) VALUES (%s, %s, %s, %s, %s, %s)",
                (url, ordering, crawling_time, updated_time, 1, 0)
            )
            article_id = cursor.lastrowid
        else:
            article_id = art_row[0]

        # 2. Article_Categories 조합 없으면 추가
        cursor.execute("SELECT 1 FROM Article_Categories WHERE article_id = %s AND category_id = %s", (article_id, category_id))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO Article_Categories (article_id, category_id) VALUES (%s, %s)", (article_id, category_id))

    db_conn.commit()
    cursor.close()
    db_conn.close()

if __name__ == "__main__":
    insert_articles()
