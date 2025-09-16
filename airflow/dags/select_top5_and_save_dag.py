from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import timedelta
import pendulum

tz = pendulum.timezone("Asia/Seoul")

# 1) Articles에서 Top5 선정
def task_select_top5_articles(**context):
    from libs.news_article.db_update.article_final_selection import get_db_connection, select_top5_articles
    conn = get_db_connection()
    selected = select_top5_articles(conn)
    return selected

# 2) Article_Categories
def task_ensure_categories_and_mapping(**context):
    from libs.news_article.db_update.article_final_selection import get_db_connection, save_selected_articles
    ti = context["ti"]
    selected = ti.xcom_pull(key="return_value", task_ids="select_top5_articles")
    conn = get_db_connection()
    # 카테고리 upsert 및 매핑은 save_selected_articles에서 처리한다고 가정
    save_selected_articles(selected, conn)
    return selected

# 3) 본문 크롤링 (선정된 5건만)
def task_crawl_article_contents(**context):
    from libs.news_article.db_update.article_final_selection import crawl_article_contents
    ti = context["ti"]
    selected = ti.xcom_pull(key="return_value", task_ids="ensure_categories_and_mapping")
    urls = [a["url"] for a in selected]
    contents = crawl_article_contents(urls)  # 크롤러 재사용
    # article_id와 매핑해서 다음 단계로 전달
    paired = [{"article_id": a["article_id"], "url": a["url"], "category_name": a["category_name"], "content": c}
              for a, c in zip(selected, contents)]
    return paired

# 4) Selected_Articles 스냅샷 저장 + Articles.is_used=1 업데이트
def task_save_selected_snapshot(**context):
    from libs.news_article.db_update.article_final_selection import get_db_connection, save_selected_articles, update_is_used_for_selected
    ti = context["ti"]
    paired = ti.xcom_pull(key="return_value", task_ids="crawl_article_contents")
    conn = get_db_connection()
    # save_selected_articles: Selected_Articles(article_id, serving_date, url, category_name(JSON), title, sub_col(JSON), content_col(JSON), author, publish_time) insert
    save_selected_articles(paired, conn)
    ids = [p["article_id"] for p in paired]
    update_is_used_for_selected(ids, conn)

default_args = {"owner": "airflow", "retries": 1, "retry_delay": timedelta(minutes=5)}

with DAG(
    dag_id="select_top5_and_save_dag",
    schedule=None,  # DAG1에서만 트리거
    start_date=tz.datetime(2025, 9, 1, 7, 30),
    catchup=False,
    default_args=default_args,
    timezone=tz,
) as dag:
    select_top5_articles = PythonOperator(
        task_id="select_top5_articles",
        python_callable=task_select_top5_articles,
    )
    ensure_categories_and_mapping_task = PythonOperator(
        task_id="ensure_categories_and_mapping",
        python_callable=task_ensure_categories_and_mapping,
    )
    crawl_article_contents_task = PythonOperator(
        task_id="crawl_article_contents",
        python_callable=task_crawl_article_contents,
    )
    save_selected_snapshot_task = PythonOperator(
        task_id="save_selected_snapshot",
        python_callable=task_save_selected_snapshot,
    )

    select_top5_articles >> ensure_categories_and_mapping_task >> crawl_article_contents_task >> save_selected_snapshot_task
