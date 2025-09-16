from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from datetime import timedelta
import pendulum

tz = pendulum.timezone("Asia/Seoul")

# 1) 링크 수집
def task_get_article_links(**context):
    from libs.news_article.crawler.linkCrawling import get_article_link
    links = get_article_link()
    return links

# 2) Articles 테이블에 적재/업서트
def task_upsert_articles(**context):
    from libs.news_article.db_update.article_db_handler import get_db_connection, process_crawled_articles
    ti = context["ti"]
    links = ti.xcom_pull(key="return_value", task_ids="get_article_links")
    conn = get_db_connection()
    process_crawled_articles(links)

default_args = {"owner": "airflow", "retries": 1, "retry_delay": timedelta(minutes=5)}

with DAG(
    dag_id="news_crawling_to_db_dag",
    schedule="0 7 * * *",
    start_date=tz.datetime(2025, 9, 1, 7, 0),
    catchup=False,
    default_args=default_args,
    timezone=tz,
) as dag:
    get_article_links = PythonOperator(
        task_id="get_article_links",
        python_callable=task_get_article_links,
    )

    upsert_articles_task = PythonOperator(
        task_id="upsert_articles",
        python_callable=task_upsert_articles,
    )

    trigger_dag2 = TriggerDagRunOperator(
        task_id="trigger_select_top5_and_save_dag",
        trigger_dag_id="select_top5_and_save_dag",
        reset_dag_run=True,
        wait_for_completion=False,
        conf={"source": "news_crawling_to_db_dag"},
    )

    get_article_links >> upsert_articles_task >> trigger_dag2
