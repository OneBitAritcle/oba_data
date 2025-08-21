# article_selection.py (simple)
import mysql.connector

# 테이블 없으면 만들기
def _ensure_tables(conn):
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS article_links (
            id BIGINT PRIMARY KEY,
            crawling_time DATETIME NOT NULL,
            category VARCHAR(100) NOT NULL,
            article_order INT NOT NULL,
            url TEXT NOT NULL,
            dup_count INT DEFAULT 1,
            is_used TINYINT(1) DEFAULT 0
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS article_contents (
            id BIGINT PRIMARY KEY,
            url TEXT NOT NULL,
            title TEXT,
            tags JSON,
            publish_time VARCHAR(50),
            author VARCHAR(100),
            sub_col JSON,
            content_col JSON
        );
    """)
    conn.commit()
    cur.close()

def init_schema(conn):
    # DAG 첫 태스크: 테이블 없으면 생성, 있으면 그대로 사용
    _ensure_tables(conn)

# --- 오늘 크롤 결과 업서트 ---
def upsert_today_links(conn, links):
    """
    오늘 긁은 링크들을 DB에 반영.
    - 이미 있는 URL  : dup_count 증가 + 최신 메타 갱신
    - 처음 보는 URL  : 신규 INSERT (dup_count = 1)
    - 'id' 없는 행은 스킵(로그만 출력)
    """
    cur = conn.cursor()

    # 임시 테이블 생성
    cur.execute("""
        CREATE TEMPORARY TABLE IF NOT EXISTS today_crawled_temp (
            id BIGINT NOT NULL,
            crawling_time DATETIME NOT NULL,
            category VARCHAR(100) NOT NULL,
            article_order INT NOT NULL,
            url TEXT NOT NULL
        ) ENGINE=InnoDB;
    """)

    rows = []
    skipped = 0
    for row in links or []:
        # id를 크롤러가 넣어준다고 가정
        if not all(k in row for k in ("id", "crawling_time", "category", "article_order", "url")):
            skipped += 1
            continue
        rows.append((int(row["id"]), row["crawling_time"], row["category"], int(row["article_order"]), row["url"]))

    if rows:
        cur.executemany("""
            INSERT INTO today_crawled_temp (id, crawling_time, category, article_order, url)
            VALUES (%s, %s, %s, %s, %s)
        """, rows)
        conn.commit()

        #  임시 테이블을 한 번만 읽도록 중간 결과를 물리화 (MySQL 1137 회피)
        # url별 최신 값만 추출 -> new_urls
        cur.execute("DROP TEMPORARY TABLE IF EXISTS new_urls;")
        cur.execute("""
            CREATE TEMPORARY TABLE new_urls AS
            SELECT
              MIN(id) AS id,
              MAX(crawling_time) AS crawling_time,
              SUBSTRING_INDEX(GROUP_CONCAT(category ORDER BY crawling_time DESC), ',', 1) AS category,
              SUBSTRING_INDEX(GROUP_CONCAT(article_order ORDER BY crawling_time DESC), ',', 1) AS article_order,
              url
            FROM today_crawled_temp
            GROUP BY url;
        """)

        # url별 오늘 등장 횟수 -> counts
        cur.execute("DROP TEMPORARY TABLE IF EXISTS counts;")
        cur.execute("""
            CREATE TEMPORARY TABLE counts AS
            SELECT url, COUNT(*) AS today_count
            FROM today_crawled_temp
            GROUP BY url;
        """)
        conn.commit()

        # 1) 기존 URL 업데이트
        cur.execute("""
            UPDATE article_links a
            JOIN new_urls n ON a.url = n.url
            LEFT JOIN counts c ON a.url = c.url
            SET a.dup_count = a.dup_count + COALESCE(c.today_count, 0),
                a.crawling_time = n.crawling_time,
                a.category = n.category,
                a.article_order = n.article_order;
        """)
        conn.commit()

        # 2) 신규 URL 삽입: dup_count = 1 
        cur.execute("""
            INSERT INTO article_links (id, crawling_time, category, article_order, url, dup_count, is_used)
            SELECT n.id, n.crawling_time, n.category, n.article_order, n.url, 1, 0
            FROM new_urls n
            LEFT JOIN article_links a ON a.url = n.url
            WHERE a.url IS NULL;
        """)
        conn.commit()

        # 임시 테이블 정리
        cur.execute("DROP TEMPORARY TABLE IF EXISTS new_urls;")
        cur.execute("DROP TEMPORARY TABLE IF EXISTS counts;")
        cur.execute("DROP TEMPORARY TABLE IF EXISTS today_crawled_temp;")
        conn.commit()

    if skipped:
        print(f"[upsert_today_links] skipped rows (missing id or fields): {skipped}")

    cur.close()

# --- Top5 뽑고 is_used=1 마킹 ---
def select_and_mark_top5(conn):
    cur = conn.cursor()

    # 기존 마킹 초기화
    cur.execute("UPDATE article_links SET is_used = 0 WHERE is_used <> 0;")
    conn.commit()

    cur.execute("""
        SELECT id, crawling_time, category, url, dup_count
        FROM article_links
        ORDER BY dup_count DESC, crawling_time DESC
        LIMIT 5;
    """)
    top5 = cur.fetchall()

    # 선택된 5개 마킹
    if top5:
        ids = [row[0] for row in top5]
        placeholders = ",".join(["%s"] * len(ids))
        cur.execute(f"UPDATE article_links SET is_used = 1 WHERE id IN ({placeholders});", ids)
        conn.commit()

    cur.close()
    return top5

# --------------------------------------------------------------------------------

# """
# CREATE TABLE article_links (
#     id BIGINT PRIMARY KEY,
#     crawling_time DATETIME NOT NULL,
#     category VARCHAR(100) NOT NULL,
#     article_order INT NOT NULL,
#     url TEXT NOT NULL,
#     dup_count INT DEFAULT 1,
#     is_used TINYINT(1) DEFAULT 0
# );

# CREATE TABLE article_contents (
#     id BIGINT PRIMARY KEY,
#     url TEXT NOT NULL,
#     title TEXT,
#     tags JSON,
#     publish_time VARCHAR(50),
#     author VARCHAR(100),
#     sub_col JSON,
#     content_col JSON
# );

# - article_links: 기사 메타데이터 저장 (중복 체크, 오늘 횟수 기록, Top5 마킹)
# - article_contents: 기사 본문/내용 저장
# """

# import mysql.connector
# from typing import Iterable, Dict, Any
# from hashlib import blake2b
# from datetime import datetime


# def _ensure_tables(conn):
#     # 테이블이 없을 경우 생성하기
#     cur = conn.cursor()
#     cur.execute(
#         """
#         CREATE TABLE IF NOT EXISTS article_links (
#             id BIGINT PRIMARY KEY,
#             crawling_time DATETIME NOT NULL,
#             category VARCHAR(100) NOT NULL,
#             article_order INT NOT NULL,
#             url TEXT NOT NULL,
#             dup_count INT DEFAULT 1,
#             is_used TINYINT(1) DEFAULT 0
#         );
#         """
#     )
#     cur.execute(
#         """
#         CREATE TABLE IF NOT EXISTS article_contents (
#             id BIGINT PRIMARY KEY,
#             url TEXT NOT NULL,
#             title TEXT,
#             tags JSON,
#             publish_time VARCHAR(50),
#             author VARCHAR(100),
#             sub_col JSON,
#             content_col JSON
#         );
#         """
#     )
#     conn.commit()
#     cur.close()


# def init_schema(conn):
#     # DAG 첫 태스크에 실행해서 테이블 만들기
#     # 이미 테이블 존재하면 기존 테이블 사용
#     _ensure_tables(conn)


# def _bigint_from_url(url: str) -> int:
#     """
#     URL 기반으로 BIGINT id 생성 (해시 사용).
#     크롤러가 id 안 줄 경우 대비.
#     """
#     h = blake2b(url.encode("utf-8"), digest_size=8).digest()
#     n = int.from_bytes(h, byteorder="big", signed=False)
#     # fit into signed BIGINT (63 bits positive range)
#     return n & ((1 << 63) - 1)


# def upsert_today_links(conn, links: Iterable[Dict[str, Any]]) -> None:
#     """
#     오늘 크롤링된 기사들을 DB에 업서트(삽입/갱신).
#     - 중복이면 dup_count 증가 + 최신 메타 갱신
#     - 신규면 새로 삽입
#     """
#     cur = conn.cursor()

#     # 오늘자 크롤링 임시 테이블
#     cur.execute(
#         """
#         CREATE TEMPORARY TABLE IF NOT EXISTS today_crawled_temp (
#             id BIGINT NOT NULL,
#             crawling_time DATETIME NOT NULL,
#             category VARCHAR(100) NOT NULL,
#             article_order INT NOT NULL,
#             url TEXT NOT NULL
#         ) ENGINE=InnoDB;
#         """
#     )

#     rows = []
#     for row in links:
#         if not all(k in row for k in ("crawling_time", "category", "url", "article_order")):
#             continue
#         _id = row.get("id")
#         if _id is None:
#             _id = _bigint_from_url(row["url"])
#         rows.append((_id, row["crawling_time"], row["category"], int(row["article_order"]), row["url"]))

#     if rows:
#         # 임시테이블에 insert
#         cur.executemany(
#             """
#             INSERT INTO today_crawled_temp (id, crawling_time, category, article_order, url)
#             VALUES (%s, %s, %s, %s, %s)
#             """,
#             rows,
#         )
#         conn.commit()

#         #  url별 최신 시각/카테고리/순서 -> agg_latest
#         cur.execute("DROP TEMPORARY TABLE IF EXISTS agg_latest;")
#         cur.execute(
#             """
#             CREATE TEMPORARY TABLE agg_latest AS
#             SELECT 
#                 url,
#                 MAX(crawling_time) AS max_time,
#                 SUBSTRING_INDEX(GROUP_CONCAT(category ORDER BY crawling_time DESC), ',', 1) AS latest_category,
#                 SUBSTRING_INDEX(GROUP_CONCAT(article_order ORDER BY crawling_time DESC), ',', 1) AS latest_order
#             FROM today_crawled_temp
#             GROUP BY url;
#             """
#         )
#         # url별 오늘 등장 횟수 -> agg_counts
#         cur.execute("DROP TEMPORARY TABLE IF EXISTS agg_counts;")
#         cur.execute(
#             """
#             CREATE TEMPORARY TABLE agg_counts AS
#             SELECT url, COUNT(*) AS today_count
#             FROM today_crawled_temp
#             GROUP BY url;
#             """
#         )
#         conn.commit()

#         # 2) 기존 URL 업데이트
#         cur.execute(
#             """
#             UPDATE article_links AS a
#             JOIN agg_latest l ON a.url = l.url
#             LEFT JOIN agg_counts c ON a.url = c.url
#             SET a.dup_count = a.dup_count + COALESCE(c.today_count, 0),
#                 a.crawling_time = l.max_time,
#                 a.category = l.latest_category,
#                 a.article_order = l.latest_order;
#             """
#         )
#         conn.commit()

#         # 3) 신규 URL 삽입
#         cur.execute(
#             """
#             INSERT INTO article_links (id, crawling_time, category, article_order, url, dup_count, is_used)
#             SELECT
#                 ids.id,
#                 l.max_time,
#                 l.latest_category,
#                 l.latest_order,
#                 l.url,
#                 COALESCE(c.today_count, 1),
#                 0
#             FROM (
#                 SELECT url, MIN(id) AS id
#                 FROM today_crawled_temp
#                 GROUP BY url
#             ) AS ids
#             JOIN agg_latest l ON ids.url = l.url
#             LEFT JOIN agg_counts c ON ids.url = c.url
#             LEFT JOIN article_links a ON a.url = l.url
#             WHERE a.url IS NULL;
#             """
#         )
#         conn.commit()

#         # 4) 임시 테이블 정리
#         cur.execute("DROP TEMPORARY TABLE IF EXISTS agg_latest;")
#         cur.execute("DROP TEMPORARY TABLE IF EXISTS agg_counts;")
#         cur.execute("DROP TEMPORARY TABLE IF EXISTS today_crawled_temp;")
#         conn.commit()

#     cur.close()



# def select_and_mark_top5(conn):
#     """
#     dup_count + crawling_time 기준으로 Top5 뽑기
#     - 기존 is_used는 전부 0으로 초기화
#     - 뽑힌 Top5만 is_used=1로 세팅
#     """
#     cur = conn.cursor()

#     # 기존 마킹 초기화
#     cur.execute("UPDATE article_links SET is_used = 0 WHERE is_used <> 0;")
#     conn.commit()

#     # Top5 조회
#     cur.execute(
#         """
#         SELECT id, crawling_time, category, url, dup_count
#         FROM article_links
#         ORDER BY dup_count DESC, crawling_time DESC
#         LIMIT 5;
#         """
#     )
#     top5 = cur.fetchall()

#     # 마킹
#     if top5:
#         ids = [row[0] for row in top5]
#         fmt = ",".join(["%s"] * len(ids))
#         cur.execute(f"UPDATE article_links SET is_used = 1 WHERE id IN ({fmt});", ids)
#         conn.commit()

#     cur.close()
#     return top5
