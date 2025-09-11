-- 0. DATABASE 생성
CREATE DATABASE oba_article
    DEFAULT CHARACTER SET = 'utf8mb4'

USE oba_article;

-- 1. Articles 테이블: 수집된 모든 기사의 원본 정보를 저장
CREATE TABLE Articles (
    article_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    url VARCHAR(2048) NOT NULL,
    crawling_time DATETIME NOT NULL,
    updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    dup_cnt INT DEFAULT 1,
    ordering DECIMAL NOT NULL, -- 기존 'order'에서 ordering으로 수정
    is_used TINYINT(1) DEFAULT 0, 
    UNIQUE KEY uk_url (url(767)) -- TEXT 컬럼의 UNIQUE 제약조건을 위한 인덱스
);

-- 2. Categories 테이블: 카테고리의 종류 관리
CREATE TABLE Categories (
    category_id INT PRIMARY KEY AUTO_INCREMENT,
    category_name VARCHAR(50) UNIQUE NOT NULL
);

-- 3. Article_Categories 테이블: 기사와 카테고리의 다대다 관계를 연결
CREATE TABLE Article_Categories (
    article_id BIGINT NOT NULL,
    category_id INT NOT NULL,
    PRIMARY KEY (article_id, category_id), -- 복합 기본 키
    FOREIGN KEY (article_id) REFERENCES Articles(article_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (category_id) REFERENCES Categories(category_id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- 4. Selected_Articles 테이블: 최종 선택된 기사의 스냅샷 정보 저장
CREATE TABLE Selected_Articles (
    article_id BIGINT PRIMARY KEY,
    serving_date DATETIME NOT NULL, -- 기존 'date'에서 serving_date로 수정
    url TEXT NOT NULL,
    category_name JSON NOT NULL,
    title TEXT NOT NULL,
    sub_col JSON NOT NULL,
    content_col JSON NOT NULL,
    author VARCHAR(50) NOT NULL,
    publish_time VARCHAR(50) NOT NULL
);