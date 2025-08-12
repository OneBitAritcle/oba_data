from bs4 import BeautifulSoup
import requests
import time
import pandas as pd
import numpy as np
import re
import random
from datetime import datetime


def get_article_link(category):

    """
    Parameter
    - category: 추출하려는 기사의 카테고리 str

    Return
    - links: 카테고리에 해당하는 기사들의 URL 리스트 반환
    """

    main_url = f'https://www.itworld.co.kr/{category}/page/1/'

    r = requests.get(main_url) # requests.get(url)로 요청
    time.sleep(random.randint(1,3)) # 요청시간 랜덤 조정으로 크롤링 차단 방지

    soup = BeautifulSoup(r.text, "html.parser") # html.parser로 파싱
    content_items = soup.select("#article") # select로 태그 선택 # <div class="content-listing-articles" id="article">
    content_items = str(content_items) # 문자열 변환

    pattern = r'href="((?!#)(?![^"]*page/)[^"]+)"' # '#'과 네비게이션 'page/' 제외
    links = re.findall(pattern, content_items) # 링크만 추출
    
    return links # 전체 기사 링크 리턴

def save_to_dataframe(category):
    """
     Parameter
    - category: 추출하려는 기사의 카테고리 str

    Return
    - df: 카테고리에 해당하는 기사들의 '크롤링 날짜', '카테고리', '순서', 'URL'을 저장한 df 반환
    """

    links = get_article_link(category) # 기사 모든 링크 가져오기

    # 데이터 프레임 생성
    today = datetime.now().strftime('%Y-%m-%d %H:%M:%S') # 오늘 날짜, 시간
    category = [category] * len(links) # 카테고리 정보
    article_index = list(range(1, len(links) + 1)) 

    data = {'time': today,
            'category': category,
            'order': article_index,
            'URL': links}
    
    df = pd.DataFrame(data)
    return df


link_df = save_to_dataframe('artificial-intelligence')
print(link_df)
print(len(link_df))


def get_content(link):
    """
    Parameter
    - link: 추출하려는 기사의 URL str
    
    Return
    - article_data: 기사의 제목, 태그, 본문 내용을 담은 딕셔너리 반환
    """

    r = requests.get(link)
    time.sleep(random.randint(1,3)) # 요청시간 랜덤 조정으로 크롤링 차단 방지
    soup = BeautifulSoup(r.text, "html.parser")

    ## 제목 추출
    title = soup.find('h1',{'class': 'article-hero__title'}).text
    # publish_time = soup.find('div',{'class': 'card__info card__info--light'})
    # publish_time = publish_time.find('span').text

    ## 리스트 형태로 받아옴
    tags = soup.find('div',{'class': 'card__tags'})
    tags = [a.get_text(strip=True) for a in tags.find_all('a')]

    # 본문 추출 및 정제
    content = soup.find_all('div',{'class': 'article-column__content'}) 
    
    # 본문 텍스트 정제 및 추출
    ## 딕셔너리 형태 자료 구조
    cleaned_paragraphs = []
    for div in content:
        for tag in div.find_all(['p', 'h2']):
            text = tag.get_text(strip=True)
            if text:
                # 태그 종류에 따라 타입 분류
                if tag.name == 'h2':
                    cleaned_paragraphs.append({'type': 'subtitle', 'text': text})
                elif tag.name == 'p':
                    cleaned_paragraphs.append({'type': 'paragraph', 'text': text})
    
    # # 데이터 프레임 생성
    # article_data = {
    #     'title': title,
    #     'tags': tags,
    #     'content': cleaned_paragraphs
    # }

    return article_data

final = []. to_dat

# print(get_content())

## 최대한 작게 만들고 join 하는 방향으로
## 크롤링 시간 + 카테고리 + order + URL // URL + subcol + contentcol + 작성시간 + 작성자

## 중복제거(기사중복횟수) 하고 1차 적재 (중복체크 컬럼)
## 출처 명시 -> 작성자
## 뉴스 or opinion ... 인지 긁어오기?? 

sub col
['nosubtitle', '미래를 위한 투자', '현재를 위한 투자']

content col
['intro', '뮹침아ㅗ', '아퍼뮤ㅜ아ㅓ퓸']