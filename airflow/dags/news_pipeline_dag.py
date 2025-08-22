# news_pipeline_dag_mysql_team_schema.py
# DAG using mysql.connector, aligned to teammate's schema (article_links/article_contents, is_used flag)
from __future__ import annotations

import os
import importlib.util
from pathlib import Path
from datetime import datetime, timedelta

import mysql.connector
from airflow import DAG
from airflow.operators.python import PythonOperator

# ---------- Config ----------
# 크롤러 모듈 경로
CRAWLER_MODULE_PATH = os.environ.get(
    "CRAWLER_MODULE_PATH",
    str(Path(__file__).resolve().parent / "libs" / "crawler.py"),
)

MYSQL_CONFIG = {
    "host": os.environ.get("MYSQL_HOST", "localhost"),
    "user": os.environ.get("MYSQL_USER", "user"),
    "password": os.environ.get("MYSQL_PASSWORD", "password"),
    "database": os.environ.get("MYSQL_DB", "oba_article"),
    "port": int(os.environ.get("MYSQL_PORT", 3306)),
}

def _load_func_from_py(filepath: str, func_name: str):
    # 파이썬 함수 가져옴
    spec = importlib.util.spec_from_file_location("user_module", filepath)
        # spec = "이 경로에 파이썬 모듈이 있다" 라는 설명서
    module = importlib.util.module_from_spec(spec)
        # 설명서(spec)를 바탕으로 비어있는 모듈 객체를 하나 만듦
    spec.loader.exec_module(module)
        # 껍데기 모듈에다가 filepath의 실제 코드 내용을 로드해서 실행
    return getattr(module, func_name)   # 모듈 객체 안에 함수/클래스들이 채워짐

def get_conn():
    return mysql.connector.connect(**MYSQL_CONFIG)  # SQL 연결 생성

# ---------- Tasks ----------
def init_schema_task(): # DB 초기화 -> 없으면 생성, 있으면 기존 테이블 사용
    from libs.article_selection import init_schema as init_schema_util
    conn = get_conn()
    try:
        init_schema_util(conn)
    finally:
        conn.close()

def crawl_links_task(**context):    # 카테고리별로 크롤링
    get_articles = _load_func_from_py(CRAWLER_MODULE_PATH, "get_articles_from_categories")
    links = get_articles()
    return links

def upsert_task(**context):     # 신규 URL 삽입 테스크
    from libs.article_selection import upsert_today_links
    links = context["ti"].xcom_pull(task_ids="crawl_links")
    if not links:
        return "no_links"
    conn = get_conn()
    try:
        upsert_today_links(conn, links)
    finally:
        conn.close()
    return "ok"

def select_mark_top5_task(**context):   # Top5 선정하여 is_used=1 마킹
    from libs.article_selection import select_and_mark_top5
    conn = get_conn()
    try:
        top5 = select_and_mark_top5(conn)
    finally:
        conn.close()
    return top5

def log_top5_task(**context):   # 5개 기사 로그에 출력
    top5 = context["ti"].xcom_pull(task_ids="select_mark_top5")
    print("[TOP 5]")
    for i, row in enumerate(top5 or [], start=1):
        print(f"{i}. id={row[0]} dup={row[4]} time={row[1]} cat={row[2]} url={row[3]}")

# ---------- DAG ----------
# 공통 기본 설정
default_args = {
    "owner": "news-team",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

# DAG 정의
with DAG(
    dag_id="news_pipeline",
    description="Daily crawl -> upsert into teammate schema -> mark Top5 via is_used",
    default_args=default_args,
    start_date=datetime(2025, 8, 19),
    schedule=None,   # 수동 실행중. 나중에 이거 바꾸면 매일 한번 자동실행 가능
    catchup=False,
    tags=["news", "rds", "etl"],
) as dag:

    t0 = PythonOperator(
        task_id="init_schema",
        python_callable=init_schema_task,
    )

    t1 = PythonOperator(
        task_id="crawl_links",
        python_callable=crawl_links_task,
    )

    t2 = PythonOperator(
        task_id="upsert_links",
        python_callable=upsert_task,
    )

    t3 = PythonOperator(
        task_id="select_mark_top5",
        python_callable=select_mark_top5_task,
    )

    t4 = PythonOperator(
        task_id="log_top5",
        python_callable=log_top5_task,
    )

    t0 >> t1 >> t2 >> t3 >> t4

# t0: 스키마 준비
# t1: 뉴스 링크 크롤링
# t2: DB에 신규 URL 삽입 (중복 제외)
# t3: Top5 기사 선정 + 마킹
# t4: 로그 출력