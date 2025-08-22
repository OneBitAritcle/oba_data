"""Crawler module (test code removed).
Expose function: get_articles_from_categories(categories: list[str]) -> list[dict]
Each dict MUST contain keys: crawling_time (str "%Y-%m-%d %H:%M:%S"), category, article_order (int), url.
"""
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

def get_articles_from_categories():
    """
    Parameter
    - categories: 추출하려는 기사 카테고리들이 담긴 리스트 (List[str])

    Return
    - all_articles: 모든 카테고리에 해당하는 기사 정보를 담은 딕셔너리의 리스트
    """
    
    categories = {'artificial-intelligence':'01',
                  'generative-ai':'02',
                  'cloud-computing':'03',
                  'computers-and-peripherals':'04',
                  'data-center':'05',
                  'emerging-technology':'06',
                  'augmented-reality':'07',
                  'enterprise-applications':'08',
                  'it-leadership':'09',
                  'it-management':'10',
                  'mobile':'11',
                  'networking':'12',
                  'android':'13',
                  'windows':'14',
                  'productivity-software':'15',
                  'collaboration-software':'16',
                  'security':'17',
                  'software-development':'18',
                  'vendors-and-providers':'19',
                  'apple':'20'
                }
    
    all_articles = []  # 모든 결과를 통합할 빈 리스트
    crawling_day = datetime.now().strftime('%Y%m%d')
    crawling_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # 수집 시간은 작업 시작 시 한 번만 기록

    # 전달받은 카테고리 리스트를 순회
    for category in categories.key():
        # 진행 상황을 알 수 있도록 현재 크롤링 중인 카테고리 출력
        print(f"'{category}' 카테고리에서 기사 링크를 수집 중입니다...")
        
        main_url = f'https://www.itworld.co.kr/{category}/page/1/'

        try:
            r = requests.get(main_url, headers=HEADERS)
            r.raise_for_status()  # 200 OK 상태 코드가 아닐 경우 예외 발생
            time.sleep(random.randint(1, 3))

            soup = BeautifulSoup(r.text, "html.parser")
            content_items = soup.select("#article")
            content_items = str(content_items)

            pattern = r'href="((?!#)(?![^"]*page/)[^"]+)"'
            links = re.findall(pattern, content_items)
            
            # 해당 카테고리에서 찾은 링크들을 순회하며 데이터 조합
            for i, link_url in enumerate(links):
                article_id = f'{crawling_day}{categories[category]}{str(i+1).zfill(2)}'
                article_data = {
                    'id': int(article_id), # ex) 2508220113
                    'crawling_time': crawling_time,
                    'category': category,
                    'article_order': i + 1,
                    'url': link_url
                }
                # 개별 기사 정보를 최종 결과 리스트에 추가
                all_articles.append(article_data)
        
        except requests.exceptions.RequestException as e:
            # 특정 카테고리에서 에러 발생 시 건너뛰고 다음 카테고리 진행
            print(f"'{category}' 처리 중 에러 발생: {e}")
            continue

    return all_articles

# def save_to_dataframe(category):
#     """
#      Parameter
#     - category: 추출하려는 기사의 카테고리 str

#     Return
#     - df: 카테고리에 해당하는 기사들의 '크롤링 날짜', '카테고리', '순서', 'URL'을 저장한 df 반환
#     """

#     links = get_article_link(category)  # 기사 모든 링크 가져오기

#     # 데이터 프레임 생성
#     today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # 오늘 날짜, 시간
#     category = [category] * len(links)  # 카테고리 정보
#     article_index = list(range(1, len(links) + 1)) 

#     data = {'crawling_time': today,
#             'category': category,
#             'order': article_index,
#             'URL': links}
    
#     df = pd.DataFrame(data)
#     return df

# def get_content(links):
#     """
#     Parameter
#     - links: 추출하려는 기사의 URL str
    
#     Return
#     - article_data: 기사의 제목, 태그, 섹션(소제목/내용리스트)을 담은 데이터 리스트 반환
#     """
#     extracted_datas = []

#     for link in links:
#         r = requests.get(link, headers=HEADERS, allow_redirects=True)  # 헤더 + 리다이렉트
#         time.sleep(random.randint(1,3))
#         soup = BeautifulSoup(r.text, "html.parser")

#         # 제목 추출
#         title_el = soup.find('h1', {'class': 'article-hero__title'}) or soup.find('h1')
#         title = title_el.get_text(strip=True) if title_el else ""

#         # 태그 추출
#         tags_div = soup.find('div', {'class': 'card__tags'})
#         tags = [a.get_text(strip=True) for a in tags_div.find_all('a')] if tags_div else []

#         # 작성 시간 추출
#         publish_time = ""
#         t = soup.find('time')
#         if t:
#             publish_time = t.get_text(strip=True)
#         if not publish_time:
#             # 페이지 상단 부근에서 날짜 패턴 찾기 (예: 2025.08.08)
#             m = re.search(r"\b(\d{4}\.\d{2}\.\d{2})\b", soup.get_text(" ", strip=True))
#             if m:
#                 publish_time = m.group(1)

#         # 작성자 추출
#         author = ""
#         # 1) 프로필 링크 기반
#         a_prof = soup.find('a', href=re.compile(r"/profile/"))
#         if a_prof:
#             author = a_prof.get_text(strip=True)
#         # 2) 추가 탐색: "By " 바로 뒤 텍스트를 탐색 (영문 기사 등)
#         if not author:
#             full_text = soup.get_text("\n", strip=True)
#             m = re.search(r"\bBy\s+([^\n|]+)", full_text)  # 줄바꿈/구분자 전까지
#             if m:
#                 author = m.group(1).strip()


#         # 본문 가져오기
#         content_divs = soup.find_all('div', {'class': 'article-column__content'})

#         # h2/p를 순서대로 읽어서 섹션화
#         sub_col = [] #sub_col 초기화
#         content_col = [] #contet_col 초기화

#         current_sub = 'nosubtitle' 
#         current_paras = []

#         def flush():
#             """
#             Function
#             : 현재까지 수집된 소제목과 문단을 최종 리스트에 추가하는 함수
#             : 새로운 소제목이 나타나거나, 모든 기사 본문 수집이 끝나면 호출됨
#             : current_sub에 저장된 소제목과 current_paras에 저장된 문단 리스트를 각 sub_col, content_col에 추가

#             - current_paras: 현재 소제목에 속한 문단들의 리스트 
#             - sub_col: 모든 기사의 소제목을 저장할 최종 리스트
#             - content_col: 모든 기사의 리스트들을 저장할 최종 리스트
#             """
#             if current_paras:
#                 sub_col.append(current_sub)
#                 # 원본 리스트가 변경되지 않도록 리스트의 사본 저장
#                 content_col.append(current_paras.copy())

#         # 서론 첫 문장이 서브 제목으로 들어가지 않도록 수정
#         def is_paragraph_like_h2(text: str) -> bool:
#             # 길이가 길거나(예: 60자 이상), 문장부호로 끝나면 문단으로 간주
#             return (len(text) >= 60) or (text.strip()[-1:] in {'.', '!', '?', '…', '다', '요', '음'})

#         for div in content_divs:
#             for tag in div.find_all(['h2', 'p']):
#                 text = tag.get_text(strip=True)
#                 if not text:
#                     continue
#                 if tag.name == 'h2':
#                     # 시작 구간에서 만난 h2가 문장형이면 -> 서론 문단으로 취급
#                     if not sub_col and current_sub == 'nosubtitle' and not current_paras and is_paragraph_like_h2(text):
#                         current_paras.append(text)
#                         continue
#                     # 일반적인 소제목 처리
#                     flush()
#                     current_sub = text
#                     current_paras = []
#                 elif tag.name == 'p':
#                     current_paras.append(text)

#         # 마지막 섹션 정리
#         flush()

#         # 본문이 전혀 없을 때 대비
#         if not sub_col:
#             sub_col = ['nosubtitle']
#             content_col = ['']

#         article_data = {
#             'URL': link,
#             'title': title,
#             'tags': tags,
#             'sub_col': sub_col,
#             'content_col': content_col,
#             'publish_time': publish_time,
#             'author': author
#         }

#         extracted_datas.append(article_data)

#     # 데이터 프레임으로 변경
#     extracted_content_df = pd.DataFrame(extracted_datas)

#     return extracted_content_df
