from bs4 import BeautifulSoup
import requests
import time
import pandas as pd
import numpy as np
import re
import random

def get_article_link(keyword):

    main_url = f'https://www.itworld.co.kr/{keyword}/page/1/'

    r = requests.get(main_url) # requests.get(url)로 요청
    time.sleep(random.randint(1,3)) # 요청시간 랜덤 조정으로 크롤링 차단 방지

    soup = BeautifulSoup(r.text, "html.parser") # html.parser로 파싱
    content_items = soup.select("#article") # select로 태그 선택 # <div class="content-listing-articles" id="article">
    content_items = str(content_items) # 문자열 변환

    pattern = r'href="((?!#)(?![^"]*page/)[^"]+)"' # '#'과 네비게이션 'page/' 제외
    links = re.findall(pattern, content_items) # 링크만 추출
    
    return links # 전체 기사 링크 리턴


def get_content(link):

    r = requests.get(link)
    time.sleep(random.randint(1,3)) # 요청시간 랜덤 조정으로 크롤링 차단 방지
    soup = BeautifulSoup(r.text, "html.parser")

    ## 이건 걍 텍스트요
    title = soup.find('h1',{'class': 'article-hero__title'}).text
    # publish_time = soup.find('div',{'class': 'card__info card__info--light'})
    # publish_time = publish_time.find('span').text

    ## 리스트 형태로 받아옴
    tags = soup.find('div',{'class': 'card__tags'})
    tags = [a.get_text(strip=True) for a in tags.find_all('a')]

    content = soup.find_all('div',{'class': 'article-column__content'}) # 본문 추출
    
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

    return ####