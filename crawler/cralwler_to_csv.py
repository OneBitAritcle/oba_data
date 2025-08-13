from bs4 import BeautifulSoup
import requests
import time
import pandas as pd
import numpy as np
import re
import random
from datetime import datetime

# 최소 보강: UA 헤더 (사이트가 UA에 민감할 수 있어요)
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    )
}

def get_article_link(category):
    """
    Parameter
    - category: 추출하려는 기사의 카테고리 str

    Return
    - links: 카테고리에 해당하는 기사들의 URL 리스트 반환
    """

    main_url = f'https://www.itworld.co.kr/{category}/page/1/'

    r = requests.get(main_url, headers=HEADERS)  # 헤더 추가
    time.sleep(random.randint(1,3))  # 요청시간 랜덤 조정으로 크롤링 차단 방지

    soup = BeautifulSoup(r.text, "html.parser")  # html.parser로 파싱
    content_items = soup.select("#article")  # <div class="content-listing-articles" id="article">
    content_items = str(content_items)  # 문자열 변환

    pattern = r'href="((?!#)(?![^"]*page/)[^"]+)"'  # '#'과 네비게이션 'page/' 제외
    links = re.findall(pattern, content_items)  # 링크만 추출
    
    return links  # 전체 기사 링크 리턴

def save_to_dataframe(category):
    """
     Parameter
    - category: 추출하려는 기사의 카테고리 str

    Return
    - df: 카테고리에 해당하는 기사들의 '크롤링 날짜', '카테고리', '순서', 'URL'을 저장한 df 반환
    """

    links = get_article_link(category)  # 기사 모든 링크 가져오기

    # 데이터 프레임 생성
    today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # 오늘 날짜, 시간
    category = [category] * len(links)  # 카테고리 정보
    article_index = list(range(1, len(links) + 1)) 

    data = {'crawling_time': today,
            'category': category,
            'order': article_index,
            'URL': links}
    
    df = pd.DataFrame(data)
    return df

def get_content(links):
    """
    Parameter
    - links: 추출하려는 기사의 URL str
    
    Return
    - article_data: 기사의 제목, 태그, 섹션(소제목/내용리스트)을 담은 데이터 리스트 반환
    """
    extracted_datas = []

    for link in links:
        r = requests.get(link, headers=HEADERS, allow_redirects=True)  # 헤더 + 리다이렉트
        time.sleep(random.randint(1,3))
        soup = BeautifulSoup(r.text, "html.parser")

        # 제목 추출
        title_el = soup.find('h1', {'class': 'article-hero__title'}) or soup.find('h1')
        title = title_el.get_text(strip=True) if title_el else ""

        # 태그 추출
        tags_div = soup.find('div', {'class': 'card__tags'})
        tags = [a.get_text(strip=True) for a in tags_div.find_all('a')] if tags_div else []

        # 작성 시간 추출
        publish_time = ""
        t = soup.find('time')
        if t:
            publish_time = t.get_text(strip=True)
        if not publish_time:
            # 페이지 상단 부근에서 날짜 패턴 찾기 (예: 2025.08.08)
            m = re.search(r"\b(\d{4}\.\d{2}\.\d{2})\b", soup.get_text(" ", strip=True))
            if m:
                publish_time = m.group(1)

        # 작성자 추출
        author = ""
        # 1) 프로필 링크 기반
        a_prof = soup.find('a', href=re.compile(r"/profile/"))
        if a_prof:
            author = a_prof.get_text(strip=True)
        # 2) 추가 탐색: "By " 바로 뒤 텍스트를 탐색 (영문 기사 등)
        if not author:
            full_text = soup.get_text("\n", strip=True)
            m = re.search(r"\bBy\s+([^\n|]+)", full_text)  # 줄바꿈/구분자 전까지
            if m:
                author = m.group(1).strip()


        # 본문 가져오기
        content_divs = soup.find_all('div', {'class': 'article-column__content'})

        # h2/p를 순서대로 읽어서 섹션화
        sub_col = [] #sub_col 초기화
        content_col = [] #contet_col 초기화

        current_sub = 'nosubtitle' 
        current_paras = []

        def flush():
            """
            Function
            : 현재까지 수집된 소제목과 문단을 최종 리스트에 추가하는 함수
            : 새로운 소제목이 나타나거나, 모든 기사 본문 수집이 끝나면 호출됨
            : current_sub에 저장된 소제목과 current_paras에 저장된 문단 리스트를 각 sub_col, content_col에 추가

            - current_paras: 현재 소제목에 속한 문단들의 리스트 
            - sub_col: 모든 기사의 소제목을 저장할 최종 리스트
            - content_col: 모든 기사의 리스트들을 저장할 최종 리스트
            """
            if current_paras:
                sub_col.append(current_sub)
                # 원본 리스트가 변경되지 않도록 리스트의 사본 저장
                content_col.append(current_paras.copy())

        # 서론 첫 문장이 서브 제목으로 들어가지 않도록 수정
        def is_paragraph_like_h2(text: str) -> bool:
            # 길이가 길거나(예: 60자 이상), 문장부호로 끝나면 문단으로 간주
            return (len(text) >= 60) or (text.strip()[-1:] in {'.', '!', '?', '…', '다', '요', '음'})

        for div in content_divs:
            for tag in div.find_all(['h2', 'p']):
                text = tag.get_text(strip=True)
                if not text:
                    continue
                if tag.name == 'h2':
                    # 시작 구간에서 만난 h2가 문장형이면 -> 서론 문단으로 취급
                    if not sub_col and current_sub == 'nosubtitle' and not current_paras and is_paragraph_like_h2(text):
                        current_paras.append(text)
                        continue
                    # 일반적인 소제목 처리
                    flush()
                    current_sub = text
                    current_paras = []
                elif tag.name == 'p':
                    current_paras.append(text)

        # 마지막 섹션 정리
        flush()

        # 본문이 전혀 없을 때 대비
        if not sub_col:
            sub_col = ['nosubtitle']
            content_col = ['']

        article_data = {
            'URL': link,
            'title': title,
            'tags': tags,
            'sub_col': sub_col,
            'content_col': content_col,
            'publish_time': publish_time,
            'author': author
        }

        extracted_datas.append(article_data)

    # 데이터 프레임으로 변경
    extracted_content_df = pd.DataFrame(extracted_datas)

    return extracted_content_df

# 테스트
links = get_article_link('artificial-intelligence')
links_df = save_to_dataframe('artificial-intelligence')
contents = get_content(links)
# 데이터 프레임 저장
links_df.to_csv('./datas/0813_links_df.csv', index=False)
contents.to_csv('./datas/0813_contents_df.csv', index=False)