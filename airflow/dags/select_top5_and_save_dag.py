from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import timedelta
import pendulum

tz = pendulum.timezone("Asia/Seoul")

# 1. 상위 5개 기사 선정
def task_select_top5_articles(**context):
    from libs.news_article.db_update.article_final_selection import select_top5_articles, get_db_connection
    db_conn = get_db_connection()
    selected_articles = select_top5_articles(db_conn)
    return selected_articles

# 2. is_used 업데이트
def task_update_is_used_for_selected(**context):
    from libs.news_article.db_update.article_final_selection import update_is_used_for_selected, get_db_connection
    ti = context["ti"]
    selected_articles = ti.xcom_pull(key="return_value", task_ids="select_top5_articles")
    article_ids = [a["article_id"] for a in selected_articles]
    db_conn = get_db_connection()
    update_is_used_for_selected(article_ids, db_conn)
    return selected_articles

# 3. 본문 크롤링
def task_crawl_article_contents(**context):
    from libs.news_article.db_update.article_final_selection import crawl_article_contents
    ti = context["ti"]
    selected_articles = ti.xcom_pull(key="return_value", task_ids="update_is_used")
    urls = [a["url"] for a in selected_articles]
    contents = crawl_article_contents(urls)
    # contents는 urls 순서를 따르도록 구현되어 있다고 가정
    paired = [{"article_id": a["article_id"], "content": c} for a, c in zip(selected_articles, contents)]
    return paired

# 4. 저장
def task_save_selected_articles(**context):
    from libs.news_article.db_update.article_final_selection import save_selected_articles, get_db_connection
    ti = context["ti"]
    paired = ti.xcom_pull(key="return_value", task_ids="crawl_article_contents")
    db_conn = get_db_connection()
    save_selected_articles(paired, db_conn)

default_args = {"owner": "airflow", "retries": 1, "retry_delay": timedelta(minutes=5)}
with DAG(
    dag_id="select_top5_and_save_dag",
    schedule=None,
    start_date=tz.datetime(2025, 9, 1, 7, 30),
    catchup=False,
    default_args=default_args,
    timezone=tz,
) as dag:
    select_top5_articles_task = PythonOperator(
        task_id="select_top5_articles",
        python_callable=task_select_top5_articles,
    )
    update_is_used_task = PythonOperator(
        task_id="update_is_used",
        python_callable=task_update_is_used_for_selected,
    )
    crawl_article_contents_task = PythonOperator(
        task_id="crawl_article_contents",
        python_callable=task_crawl_article_contents,
    )
    save_selected_articles_task = PythonOperator(
        task_id="save_selected_articles",
        python_callable=task_save_selected_articles,
    )

    select_top5_articles_task >> update_is_used_task >> crawl_article_contents_task >> save_selected_articles_task