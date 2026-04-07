
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from datetime import timedelta
import pendulum

local_tz = pendulum.timezone("Asia/Seoul")

# 1) 기사 수집
def task_get_article_links(**context):
    from libs.news_article.crawler.linkCrawling import get_article_link
    return get_article_link()   # 기사별 정보 딕셔너리 들어있는 리스트 반환

# 2) DB 적재
def task_upsert_articles(**context):
    from libs.news_article.db_update.article_db_handler import process_crawled_articles
    # ti: Task Instance 객체
    ti = context["ti"]  # 현재 테스크 객체
    links = ti.xcom_pull(key="return_value", task_ids="get_article_links") # XCom에 저장된 데이터 받아오기
    process_crawled_articles(links)

default_args = {"owner": "airflow", "retries": 2, "retry_delay": timedelta(minutes=30)}

with DAG(
    dag_id="news_crawling_to_db_dag",
    schedule_interval="0 7 * * *",   # 매일 오전 7시 실행
    start_date=pendulum.datetime(2025, 9, 1, 7, 0, tz=local_tz),
    catchup=False,
    default_args=default_args,
) as dag:
    # Airflow는 PythonOperator의 return 값을 자동으로 XCom에 저장함
    # (Key: "return_value", Task ID: "get_article_links")
    get_article_links = PythonOperator(
        task_id="get_article_links",
        python_callable=task_get_article_links,
    )
    upsert_articles = PythonOperator(
        task_id="upsert_articles",
        python_callable=task_upsert_articles,
    )

    get_article_links >> upsert_articles
