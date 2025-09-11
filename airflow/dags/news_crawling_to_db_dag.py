from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator 
from datetime import timedelta
import pendulum

tz = pendulum.timezone("Asia/Seoul")

# 1. 기사 링크 크롤링
def task_get_article_link(**context):
    from libs.news_article.crawler.linkCrawling import get_article_link
    article_links = get_article_link()
    return article_links 

# 2. 기사 본문 크롤링
def task_build_content_df(**context):
    from libs.news_article.crawler.contentCrawling import build_content_df
    ti = context["ti"]
    article_links = ti.xcom_pull(key="return_value", task_ids="get_article_link")
    urls = [a["url"] for a in article_links]
    content_df_records = build_content_df(urls)
    return content_df_records 

# 3. DB 반영
def task_process_crawled_articles(**context):
    from libs.news_article.db_update.article_db_handler import process_crawled_articles, get_db_connection
    ti = context["ti"]
    records = ti.xcom_pull(key="return_value", task_ids="build_content_df")
    conn = get_db_connection()
    process_crawled_articles(records, conn)

default_args = {"owner": "airflow", "retries": 1, "retry_delay": timedelta(minutes=5)}

with DAG(
    dag_id="news_crawling_to_db_dag",
    schedule_interval="0 7 * * *",
    start_date=tz.datetime(2025, 9, 1, 7, 0),
    catchup=False,
    default_args=default_args,
    timezone=tz,
) as dag:
    get_article_link_task = PythonOperator(
        task_id="get_article_link",
        python_callable=task_get_article_link,
    )
    build_content_df_task = PythonOperator(
        task_id="build_content_df",
        python_callable=task_build_content_df,
    )
    process_crawled_articles_task = PythonOperator(
        task_id="process_crawled_articles",
        python_callable=task_process_crawled_articles,
    )

    trigger_dag2 = TriggerDagRunOperator(
            task_id="trigger_select_top5_and_save_dag",
            trigger_dag_id="select_top5_and_save_dag",
            reset_dag_run=True,              
            wait_for_completion=False,               
            conf={"source": "news_crawling_to_db_dag"},   
        )

    get_article_link_task >> build_content_df_task >> process_crawled_articles_task >> trigger_dag2