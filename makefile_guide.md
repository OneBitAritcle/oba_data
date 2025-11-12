# 해당 명령어 대로 실행
# 이미지 빌드
make build

# 컨테이너 실행
make run
# docker run을 실행할 때 컨테이너 내부에 airflow 로그가 자동으로 쌓이는 옵션 설정

# 컨테이너 상태 확인
make ps

# Airflow Admin 계정 생성
make create-user

# 컨테이너 로그 보기
make logs

----
# 컨테이너 중지/삭제
make stop
make rm
make clean   # 이미지까지 싹 삭제
