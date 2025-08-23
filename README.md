# 🧪 OBA Data Engineering

한입 기사(OBA: One Bite Article) **데이터 엔지니어링 레포지토리**입니다.  
사용자의 뉴스 소비 및 퀴즈 풀이 데이터를 기반으로,  
**자동 수집, 정제, 저장, 분석**이 가능한 실시간 데이터 파이프라인을 구축합니다.

---

## 📌 프로젝트 개요

OBA 데이터 파이프라인은 다음을 목표로 합니다:

- 사용자에게 제공할 뉴스 기사 선별 후 크롤링
- 수집된 데이터는 **Python**으로 전처리
- 전처리된 데이터는 **PostgreSQL/RDS**에 저장
- 사용자/시스템 로그를 수집하여 DataBase에 저장 및 분석
- 시각화 도구(**Metabase, Kibana**)를 통해 운영 지표 및 로그 분석
- **Airflow DAG**을 통해 수집 → 처리 → 저장을 자동화

---

## 🎯 주요 기능

1. **뉴스 데이터 수집**
   - News API or 웹 크롤러를 통한 기사 수집 (하루 5건 이상)
   - 제목, 본문, 카테고리 등 메타 데이터 포함

2. **(논의필요) 실시간 로그 수집** 
   - Kafka Producer (백엔드) → Kafka Cluster → Kafka Consumer (Python)

3. **데이터 정제 및 전처리**
   - Pandas 또는 Spark로 HTML 제거, 파생 컬럼 생성, 정규화 등 처리
   - 대량 처리 시 Spark Streaming 활용 가능

4. **데이터 적재**
   - PostgreSQL (정형 데이터 저장)
   - S3 (백업 및 대용량 로그 저장)

5. **파이프라인 자동화**
   - Apache Airflow로 DAG 관리 및 스케줄링
   - 실패 감지 및 Slack 알림 연동

6. **시각화 및 모니터링**
   - Metabase: 사용자 지표, 퀴즈 통계 등
   - Kibana (선택): 실시간 로그 모니터링, 에러 분석

---

## ⚙️ 아키텍처 구성

[사용자/백엔드]
↓
Kafka Producer
↓
Kafka Cluster
↓
Kafka Consumer (Python)
↓
Airflow DAG 실행
├─ Spark or Pandas (전처리)
├─ PostgreSQL 적재
└─ S3 백업
↓
Metabase / Kibana


- 모든 구성은 **Docker** 환경에서 통합 실행 가능
- **Airflow는 DAG Scheduler + UI + Worker로 분리 컨테이너 실행**
- EC2 단일 서버 or 로컬에서도 운영 가능 (Docker Compose 사용)

---

## 🚀 향후 확장 계획

- 사용자 로그 기반 **통계/추천/랭킹 테이블** 구축
- 실시간 로그를 분석하여 **AI 모델 피드백 루프 구성**
- Spark 기반 **대용량 배치 처리 + ML 파이프라인 연동**
- S3 기반 아카이빙 및 장기 저장 구조 고도화
- Kubernetes + CI/CD 구성으로 서비스 운영 확장

---

## 🛠 기술 스택

| 범주 | 기술 |
|------|------|
| **데이터 수집** | NewsAPI, 크롤링 |
| **전처리** | Python (Pandas) |
| **저장소** | PostgreSQL (RDS), AWS S3, Redis |
| **자동화** | Apache Airflow (DAG 기반) |
| **운영환경** | Docker, Docker Compose |
| **시각화** | Metabase, Kibana |
| **알림/모니터링** | Slack Hook, Email Operator |

---

## 📘 기술 문서

이 프로젝트의 기술적 구성과 구현 현황은 Notion에 정리되어 있습니다.

👉 기술 개발 문서 보기: [Notion 기술 개발 페이지 바로가기](https://www.notion.so/236a97372b20803699aee87278b229e7?source=copy_link)

---

## 🔗 문서에 포함된 내용

- 기술별 담당자 및 개발 진행 상황
- Kafka Consumer / Spark 구성 방식
- Airflow DAG 구성도 및 샘플 코드
- Redis와 PostgreSQL 분리 기준
- API vs 크롤링 방식 비교 및 선정 이유
- 운영환경(Docker, Airflow) 설치 및 테스트 기록

