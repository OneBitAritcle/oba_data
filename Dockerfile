# ======== base image ========
ARG AIRFLOW_VERSION=2.9.3
ARG PYTHON_VERSION=3.9
FROM apache/airflow:${AIRFLOW_VERSION}-python${PYTHON_VERSION}

# ======== system packages (optional) ========
USER root
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      tzdata ca-certificates curl unzip wget \
      build-essential \
    && rm -rf /var/lib/apt/lists/*
ENV TZ=Asia/Seoul

USER airflow

# ======== python deps ========
ARG AIRFLOW_CONSTRAINTS_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"
# COPY --chown=airflow:0 requirements.txt /tmp/requirements.txt
RUN if [ -f /tmp/requirements.txt ]; then \
      pip install --no-cache-dir -r /tmp/requirements.txt --constraint "${AIRFLOW_CONSTRAINTS_URL}"; \
    fi

# ======== DAGs 복사 ========
COPY --chown=airflow:0 airflow/dags/ /opt/airflow/dags/

# ======== env ========
ENV AIRFLOW__CORE__LOAD_EXAMPLES=False
ENV AIRFLOW__LOGGING__LOGGING_LEVEL=INFO
