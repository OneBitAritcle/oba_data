from bs4 import BeautifulSoup
import requests
import time
import pandas as pd
import numpy as np
import re
import random
from datetime import datetime


def get_article_link():
    # ConnectionError방지
    headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "ko-KR,ko;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "TE": "Trailers",
            "DNT": "1",
        }

    # 수집할 기사의 카테고리 
    categories = {'artificial-intelligence': 1,
                    'generative-ai': 2,
                    'cloud-computing':3,
                    'computers-and-peripherals': 4,
                    'data-center': 5,
                    'emerging-technology': 6,
                    'augmented-reality': 7,
                    'enterprise-applications': 8,
                    'it-leadership': 9,
                    'it-management': 10,
                    'mobile': 11,
                    'networking': 12,
                    'android': 13,
                    'windows': 14,
                    'productivity-software': 15,
                    'collaboration-software': 16,
                    'security': 17,
                    'software-development': 18,
                    'vendors-and-providers': 19,
                    'apple': 20
                }
    
    weighted_list = [22.5, 19.6, 16.9, 14.4, 12.1, 10.0, 8.1, 6.4, 4.9, 3.6, 2.5, 1.6, 0.9, 0.4, 0.1]
    crawling_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # 수집 시간은 작업 시작 시 한 번만 기록

    all_article_info = [] # 모든 링크들을 저장할 리스트

    for category, category_id in categories.items():
        main_url = f'https://www.itworld.co.kr/{category}/page/1/'

        try:
            r = requests.get(main_url) # requests.get(url)로 요청
            time.sleep(random.randint(1,3)) # 요청시간 랜덤 조정으로 크롤링 차단 방지

            soup = BeautifulSoup(r.text, "html.parser") # html.parser로 파싱
            
            content_items = soup.select("#article") # select로 태그 선택 : <div class="content-listing-articles" id="article">
            content_items = str(content_items) # 문자열 변환
 
            pattern = r'href="((?!#)(?![^"]*page/)[^"]+)"' # '#'과 네비게이션 'page/' 제외
            links = re.findall(pattern, content_items) # 기사의 링크만 추출

            # 카테고리에서 찾은 링크들을 순회하며, 데이터 조합
            for i, link in enumerate(links):
                article_info = {
                    'category' : category_id,
                    'ordering' : weighted_list[i],
                    'url' : link,
                    'crawling_time': crawling_time
                }
                all_article_info.append(article_info)

        # 예상치 못하게 오류가 발생하면
        except Exception as e:
            print(f"'{category}' 처리 중 에러 발생: {e}") # 해당 오류 원인을 출력하고 
            raise

    return all_article_info # 전체 기사 링크 리턴


"""
    테스트 코드
"""
# import os
# all_article_info = get_article_link()
# article_info_df = pd.DataFrame(all_article_info)

# # 현재 작업 디렉토리에 저장
# file_path = os.path.join(os.getcwd(), "article_links.xlsx")
# article_info_df.to_excel(file_path, index=False, engine="openpyxl")
