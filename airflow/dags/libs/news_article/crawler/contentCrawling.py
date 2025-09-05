from bs4 import BeautifulSoup
import requests
import time
import pandas as pd
import numpy as np
import re
import random

def get_content(url):
    time.sleep(random.uniform(1.0, 3.0))
    r = requests.get(url, timeout=(5, 15))
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    # 제목
    title_el = soup.find("h1", {"class": re.compile(r"article-hero__title")}) or soup.find("h1")
    title = title_el.get_text(strip=True) if title_el else ""

    # 태그
    tags_div = soup.find("div", {"class": re.compile(r"card__tags")})
    tags = [a.get_text(strip=True) for a in tags_div.find_all("a")] if tags_div else []

    # 발행일
    publish_time = ""
    t = soup.find("time")
    if t:
        publish_time = t.get_text(strip=True)
    if not publish_time:
        m = re.search(r"\b(\d{4}\.\d{2}\.\d{2})\b", soup.get_text(" ", strip=True))
        if m:
            publish_time = m.group(1)

    # 작성자
    author = ""
    a_prof = soup.find("a", href=re.compile(r"/profile/"))
    if a_prof:
        author = a_prof.get_text(strip=True)
    if not author:
        full_text = soup.get_text("\n", strip=True)
        m = re.search(r"\bBy\s+([^\n|]+)", full_text)
        if m:
            author = m.group(1).strip()

    # 본문 섹션
        # 섹션 제목: h2
        # 본문 문단: p
    content_divs = soup.find_all("div", {"class": re.compile(r"article-column__content")})
    sub_col, content_col = [], []
    current_sub, current_paras = "nosubtitle", []

    # 문단 묶기
    # 문단들을 하나의 소제목 그룹으로 저장하기 위한 작업
    def flush():
        if current_paras:
            sub_col.append(current_sub)
            content_col.append(current_paras[:])

    # 첫 문단을 h2태그에 쓰는 경우 확인
    # 해당 h2태그가 소제목일지, 문단일지 구분할 필요 있음
    def looks_like_paragraph(text):
        text = text.strip()
        return (len(text) >= 60) or (text[-1:] in [".","!","?","…","다","요"])

    # div(h2/p) 순회
    for div in content_divs:
        for tag in div.find_all(["h2","p"]):
            text = tag.get_text(strip=True)
            if not text:    # 내용 없으면 넘기기
                continue
            if tag.name == "h2":    # 소제목인 경우
                if not sub_col and current_sub == "nosubtitle" and not current_paras and looks_like_paragraph(text):
                    current_paras.append(text)
                    continue
                flush()     # 지금까지 모은 문단들 하나의 섹션으로 확정
                current_sub = text  # 새로운 소제목 시작
                current_paras = []
            else:  # 일반 문단일 경우
                current_paras.append(text)
    
    
    flush()     # 반복 이후에도 마지막 소제목 밑에 문단 남아있을 수 있음
                # 라스트 flush

    if not sub_col:
        sub_col, content_col = ["nosubtitle"], [[]]

    return {
        "url": url,
        "title": title,
        "tags": tags,
        "publish_time": publish_time,
        "author": author,
        "sub_col": sub_col,
        "content_col": content_col,
    }

# 여러 기사 url 리스트 받아서 DataFrame으로 확인
def build_content_df(urls):
    rows = []
    for u in urls:
        try:
            rows.append(get_content(u))
        except Exception as e:
            print(f"{u} -> {e}")
            raise
    return pd.DataFrame(
        rows, 
        columns=["url","title","tags","publish_time","author","sub_col","content_col"]
        )


# 테스트
# urls = ["https://www.itworld.co.kr/article/4050262", "https://www.itworld.co.kr/article/4050189"]
# df = build_content_df(urls)
# df.to_csv("test.csv", index=False, encoding="utf-8-sig")