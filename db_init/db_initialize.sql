-- 0. DATABASE 생성
CREATE DATABASE oba_article
    DEFAULT CHARACTER SET = 'utf8mb4'

USE oba_article;

-- 1. Articles 테이블: 수집된 모든 기사의 원본 정보를 저장
CREATE TABLE Articles (
    article_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    url VARCHAR(2048) NOT NULL,
    crawling_time DATETIME NOT NULL,
    updated_time DATETIME NOT NULL,
    dup_cnt INT DEFAULT 1,
    ordering DECIMAL(10, 1) NOT NULL, -- 기존 'order'에서 ordering으로 수정
    is_used TINYINT(1) DEFAULT 0, 
    serving_date DATE DEFAULT NULL,
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

-- 4. Selected_Articles 테이블: 최종 선택된 기사의 스냅샷 정보 저장 -> mongoDB로 이관
-- CREATE TABLE Selected_Articles (
--     article_id BIGINT PRIMARY KEY,
--     serving_date DATE NOT NULL, -- 기존 'date'에서 serving_date로 수정
--     url TEXT NOT NULL,
--     category_name JSON NOT NULL,
--     title TEXT NOT NULL,
--     sub_col JSON NOT NULL,
--     content_col JSON NOT NULL,
--     author VARCHAR(50) NOT NULL,
--     publish_time VARCHAR(50) NOT NULL
-- );

-- 5. 4checking_articles 테이블: 데이터 적재 확인을 위한 임시 테이블
-- CREATE TABLE 4checking_articles (
--     article_id BIGINT NOT NULL,
--     crawling_time DATETIME NOT NULL,
--     category_id INT NOT NULL,
--     FOREIGN KEY (article_id) REFERENCES Articles(article_id) ON DELETE CASCADE ON UPDATE CASCADE,
--     FOREIGN KEY (category_id) REFERENCES Categories(category_id) ON DELETE CASCADE ON UPDATE CASCADE
-- );

-- 6. Backend 테이터 베이스 생성 
CREATE DATABASE oba_backend
    DEFAULT CHARACTER SET = 'utf8mb4'

-- 데이터 베이스 선택
USE oba_backend;

-- 7. users 테이블: 사용자 메타 데이터 저장
CREATE TABLE users (
    user_id bigint NOT NULL,
    identifier varchar(255) NOT NULL,
    email varchar(255) NOT NULL,
    name varchar(255) NOT NULL,
    picture varchar(512) NOT NULL,
    provider varchar(50) NOT NULL,
    role varchar(50) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at DATETIME DEFAULT NULL,
    is_deleted TINYINT(1) NOT NULL,
    PRIMARY KEY (user_id)
);

-- 8. Incorrect_Articles 테이블: 사용자별 틀린 퀴즈가 존재하는 기사 정보 저장
CREATE TABLE Incorrect_Articles (
    user_id BIGINT NOT NULL,
    sol_date DATETIME NOT NULL DEFAULT (CURRENT_DATE),
    article_id BIGINT NOT NULL,
    PRIMARY KEY (user_id, article_id),
    CONSTRAINT fk_incorrect_articles_user
        FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE CASCADE
);

-- 9. Incorrect_Quiz 테이블: 사용자별 틀린 기사에 대한 퀴즈 정답 여부 저장
CREATE TABLE Incorrect_Quiz (
    user_id BIGINT NOT NULL,
    article_id BIGINT NOT NULL,
    quiz1 TINYINT(1) NOT NULL,
    quiz2 TINYINT(1) NOT NULL,
    quiz3 TINYINT(1) NOT NULL,
    quiz4 TINYINT(1) NOT NULL,
    quiz5 TINYINT(1) NOT NULL,
    PRIMARY KEY (user_id, article_id),
    CONSTRAINT fk_incorrect_quiz_article
        FOREIGN KEY (user_id, article_id)
        REFERENCES Incorrect_Articles(user_id, article_id)
        ON DELETE CASCADE
); 


