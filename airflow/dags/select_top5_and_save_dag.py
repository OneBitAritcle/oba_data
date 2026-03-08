
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import timedelta
import pendulum

local_tz = pendulum.timezone("Asia/Seoul")

def task_select_top5_articles(**context):
    from libs.news_article.db_update.article_final_selection import select_top5_articles
    return select_top5_articles()

def task_crawl_and_save_contents(**context):
    from libs.news_article.db_update.article_final_selection import insert_content
    from libs.news_article.crawler.contentCrawling import get_content
    ti = context["ti"]
    articles = ti.xcom_pull(key="return_value", task_ids="select_top5_articles")
    for article in articles:
        content = get_content(article["url"])
        insert_content(article["article_id"], content)

default_args = {"owner": "airflow", "retries": 2, "retry_delay": timedelta(minutes=10)}

with DAG(
    dag_id="select_top5_and_save_dag",
    schedule_interval="0 9 * * *",
    start_date=pendulum.datetime(2025, 9, 1, 9, 0, tz=local_tz),
    catchup=False,
    default_args=default_args,
) as dag:
    select_top5_articles = PythonOperator(
        task_id="select_top5_articles",
        python_callable=task_select_top5_articles,
    )
    crawl_and_save_contents = PythonOperator(
        task_id="crawl_and_save_contents",
        python_callable=task_crawl_and_save_contents,
    )
    select_top5_articles >> crawl_and_save_contents
