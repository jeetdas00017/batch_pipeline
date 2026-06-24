FROM apache/airflow:2.10.0

USER root

# Install system dependencies needed by dbt and Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-dev \
    libpq-dev \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

USER airflow

WORKDIR /opt/airflow

# Copy requirements file and install Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt

# Ensure the project modules are importable
ENV PYTHONPATH=/opt/airflow
