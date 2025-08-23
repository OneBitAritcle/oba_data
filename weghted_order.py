def weighted_order(article_num, p=2):
    """
    기사 크롤링 순위 1번부터 15번까지의 거듭제곱 방식 가중치 계산 리스트 제작
    ---------------------------------------------------------
    Parameter
    - article_num: 추출받아온 기사의 개수
    - p: 거듭제곱 지수, 기본값은 2

    Return
    - weighted_list: 거듭제곱 방식으로 계산한 가중치 리스트 전체
    """
    weighted_list = []

    for i in range(1, article_num+1):
        weight = round((16 - i) ** p * 0.1, 2)
        weighted_list.append(weight)
        
    return weighted_list

print(weighted_order(15))
