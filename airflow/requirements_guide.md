# 📦 requirements.txt 설치 가이드

본 문서는 프로젝트 실행을 위한 Python 의존성 패키지(`requirements.txt`) 설치 방법과 패키지 구성 이유가 작성되어 있습니다.


## Python 버전

- 이 프로젝트는 **Python 3.11** 기준으로 개발되었습니다.
- 다른 버전에서는 호환 문제가 발생할 수 있으니, **가능하면 3.11을 사용해주세요.**
- [공식 설치 링크](https://www.python.org/downloads/)


## requirements.txt 구성

`requirements.txt`에는 다음 항목들이 포함되어 있습니다:

| 분류 | 주요 패키지 | 설명 |
|------|-------------|------|
| 크롤링 | `beautifulsoup4`, `requests` | 기사 리스트 및 상세 내용 수집 |
| 데이터 처리 | `pandas`, `numpy` | 수집한 데이터 정리 |
| MySQL 연동 | `mysqlclient`, `SQLAlchemy`, `sqlparse`, `alembic` | DB 연결 및 ORM |
| 자동화 | `apache-airflow`, `airflow providers` | DAG 스케줄링 및 실행 |


```txt
# Web Crawling
beautifulsoup4==4.13.4
requests==2.31.0

# Data Handling
pandas==2.3.2
numpy==2.3.2

# MySQL 연동 및 ORM
mysqlclient==2.2.4         # MySQL 드라이버
SQLAlchemy==1.4.52         # ORM
sqlparse==0.5.0            # SQL 파싱
alembic==1.13.2            # DB 마이그레이션 도구

# Apache Airflow
apache-airflow[postgres,google]==2.9.3 \
--constraint https://raw.githubusercontent.com/apache/airflow/constraints-2.9.3/constraints-3.11.txt
```

## 설치 및 실행 가이드

### ✅ 가상환경 생성

```bash
# 프로젝트 루트에서 가상환경 생성
python3 -m venv venv

# 가상환경 활성화
# macOS / Linux
source venv/bin/activate

# Windows (CMD)
venv\Scripts\activate
```

### ✅ 의존성 설치

```bash
pip install --upgrade pip

# 전체 requirements 설치
pip install -r requirements.txt
```

※ Airflow는 제약조건 파일을 사용하여 설치되므로, `requirements.txt` 안에서 자동 처리됩니다.

따라서 별도 설치 명령어는 필요하지 않지만, 오류 시 아래의 명령어를 통해 재설치할 수 있습니다:

```bash
pip install 'apache-airflow[postgres,google]==2.9.3' \
--constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.9.3/constraints-3.11.txt"
```


## 📂 Airflow 설정

Airflow 설정, 관리자 계정 생성, 웹서버 실행 등은 airflow_setting.md 문서를 참고해주세요:

👉 [`airflow_setting.md`](./airflow_setting.md)


## 🧩 기타 참고

- 프로젝트 내 `dags/` 디렉토리에 Airflow DAG 파일을 작성하고 자동화할 수 있습니다.
- 따라서, DAG에서 사용할 Python 모듈은 가상환경에 함께 설치되어야 합니다.

### 📌 팀원 모두 동일한 환경에서 작업할 수 있도록 위 가이드에 따라 `venv`, `requirements.txt`, `Airflow`를 설정해주세요!