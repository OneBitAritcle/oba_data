# ======== base image ========
ARG AIRFLOW_VERSION=2.9.3
ARG PYTHON_VERSION=3.9
FROM apache/airflow:${AIRFLOW_VERSION}-python${PYTHON_VERSION}

# ======== system packages ========
USER root
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        tzdata ca-certificates curl unzip wget
ENV TZ=Asia/Seoul

USER airflow

# ======== AWS tools (S3 logging 위해 필요) ========
RUN pip install --no-cache-dir boto3 awscli

# ======== python deps ========
ARG AIRFLOW_CONSTRAINTS_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-3.9.txt"
COPY --chown=airflow:0 airflow/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt \
    --constraint "${AIRFLOW_CONSTRAINTS_URL}"

# ======== DAGs 복사 ========
COPY --chown=airflow:0 airflow/dags/ /opt/airflow/dags/

# ======== default env ========
ENV AIRFLOW__CORE__LOAD_EXAMPLES=False
ENV AIRFLOW__LOGGING__LOGGING_LEVEL=INFO

