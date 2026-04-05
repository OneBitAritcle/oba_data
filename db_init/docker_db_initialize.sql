-- Docker 초기화용 (db_initialize.sql 기반, 세미콜론 수정)

-- 0. DATABASE 생성
CREATE DATABASE IF NOT EXISTS oba_article
    DEFAULT CHARACTER SET = 'utf8mb4';

USE oba_article;

-- 1. Articles 테이블
CREATE TABLE Articles (
    article_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    url VARCHAR(2048) NOT NULL,
    crawling_time DATETIME NOT NULL,
    updated_time DATETIME NOT NULL,
    dup_cnt INT DEFAULT 1,
    ordering DECIMAL(10, 1) NOT NULL,
    is_used TINYINT(1) DEFAULT 0,
    serving_date DATE DEFAULT NULL,
    UNIQUE KEY uk_url (url(767))
);

-- 2. Categories 테이블
CREATE TABLE Categories (
    category_id INT PRIMARY KEY AUTO_INCREMENT,
    category_name VARCHAR(50) UNIQUE NOT NULL
);

-- 3. Article_Categories 테이블
CREATE TABLE Article_Categories (
    article_id BIGINT NOT NULL,
    category_id INT NOT NULL,
    PRIMARY KEY (article_id, category_id),
    FOREIGN KEY (article_id) REFERENCES Articles(article_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (category_id) REFERENCES Categories(category_id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- 6. Backend 데이터베이스 생성
CREATE DATABASE IF NOT EXISTS oba_backend
    DEFAULT CHARACTER SET = 'utf8mb4';

USE oba_backend;

-- 7. users 테이블
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

-- 8. Incorrect_Articles 테이블
CREATE TABLE Incorrect_Articles (
    user_id BIGINT NOT NULL,
    sol_date DATETIME NOT NULL DEFAULT (CURRENT_DATE),
    article_id BIGINT NOT NULL,
    PRIMARY KEY (user_id, article_id),
    CONSTRAINT fk_incorrect_articles_user
        FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE CASCADE
);

-- 9. Incorrect_Quiz 테이블
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
