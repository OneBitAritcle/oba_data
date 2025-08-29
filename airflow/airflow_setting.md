# Apache Airflow 설치 가이드 (Version 2.9.3)

> ✅ 본 문서는 **MAC** 및 **Windows(WSL - Ubuntu)** 환경에서 Airflow 설치를 정리한 내용입니다.  
> 우리는 프로젝트 공통 환경을 위해 **2.9.3 버전**을 설치하였습니다.  
> 최신 버전(3.x.x 계열)은 아직 안정화되지 않은 기능과 잦은 변경 사항이 있어 피하고,  
> **안정성과 문서화가 충분히 확보된 2.9.3 버전**을 선택했습니다.


## 📌 참고 문서
- [Airflow 공식문서](https://airflow.apache.org/docs/apache-airflow/stable/release_notes.html)  
- [Airflow GitHub](https://github.com/apache/airflow)  
- [Airflow 2.9.3 PyPI](https://pypi.org/project/apache-airflow/2.9.3/)



## 1. 가상환경 생성 및 활성화

```bash
# 가상환경 생성
python3 -m venv <가상환경이름>

# 가상환경 활성화
source <가상환경이름>/bin/activate
```


## 2. Airflow 설치

```bash
pip install 'apache-airflow[postgres,google]==2.9.3' \
 --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.9.3/constraints-3.11.txt"
```


## 3. AIRFLOW_HOME 디렉토리 설정

> ⚠️ **환경에 따라 셸 설정 파일이 다릅니다.**

### ◼︎ MAC (zsh)
```bash
echo 'export AIRFLOW_HOME="/Users/<사용자명>/Desktop/side_pjt/airflow_home"' >> ~/.zshrc
source ~/.zshrc
```

### ◼︎ Linux / WSL Ubuntu (bash)
```bash
echo 'export AIRFLOW_HOME="/home/<사용자명>/airflow_home"' >> ~/.bashrc
source ~/.bashrc
```

- 적용 안 되면 수동으로 편집:
  - MAC: `open ~/.zshrc`
  - Linux: `nano ~/.bashrc` (또는 `vi ~/.bashrc`)
- 수정 후 저장 → 다시 터미널 열기 또는 `source` 실행  
- 이후 `airflow db init` 진행


## 4. DB 초기화

```bash
airflow db init
```


## 5. 관리자 계정 생성

```bash
airflow users create \
    --username <사용자명> \
    --firstname <이름> \
    --lastname <성> \
    --role Admin \
    --email <이메일>
```

예시:

```bash
airflow users create \
    --username Thedduro \
    --firstname Thedduro \
    --lastname Lim \
    --role Admin \
    --email lsw2207@gmail.com

airflow users create \
    --username hwimin \
    --firstname hwimin \
    --lastname Kim \
    --role Admin \
    --email whimin0319@gmail.com

airflow users create \
    --username sarang \
    --firstname sarang \
    --lastname Park \
    --role Admin \
    --email sarangx1227@gmail.com
```


## 6. 웹 서버 실행

```bash
airflow webserver --port 8080
```

- 이후 [http://localhost:8080](http://localhost:8080) 접속 가능


## 7. (참고) 최신 버전 설치 시도 기록 (3.0.3)

> ⚠️ 실제 프로젝트에서는 사용하지 않았으나, 참고용으로 기록.  
> 설치 과정에서 계정 인증 방식 변경 및 cfg 수정 필요했음.

```bash
pip install 'apache-airflow==3.0.3'  --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-3.0.3/constraints-3.11.txt"
```

환경변수 및 DB 초기화:

```bash
export AIRFLOW_HOME=.
export AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=sqlite:////Users/<계정>/Desktop/airflow/airflow.db

airflow db migrate
airflow api-server -p 8080
```

계정 생성 시 오류 발생 시:

- `airflow.cfg` → `[webserver]` 항목에서 `auth_manager` 수정 필요
- 이후 다시 계정 생성 및 로그인 진행


## 📂 기본 폴더 구조 (AIRFLOW_HOME)

Airflow 초기화(`airflow db init`) 후 생성되는 디렉토리 구조는 아래와 같습니다.

```plaintext
$AIRFLOW_HOME/
├── airflow.cfg         # Airflow 설정 파일 (환경 설정)
├── logs/               # 태스크 실행 로그
│   └── scheduler/
│   └── dag_processor_manager/
├── dags/               # DAG 파일 저장 위치 (직접 작성하는 곳)
├── webserver_config.py # 웹 서버 관련 설정
└── airflow.db          # SQLite DB (기본값)
```

- **dags/** 폴더에 DAG 스크립트를 작성 및 관리합니다.  
- DB는 기본 SQLite이며, 실제 운영에서는 MySQL 등 외부 DB로 교체 예정입니다.

