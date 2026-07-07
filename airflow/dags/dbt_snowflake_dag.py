import sys
from datetime import datetime, timedelta

from airflow import DAG
from airflow.exceptions import AirflowException
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator
import random


sys.path.append("/opt/airflow")

from extract.service import extract_all, wait_for_max_time_sync
from extract.utils.logging_config import configure_logging
from extract.insert.insert_to_postgres import generate_fake_data

configure_logging()

def extract_postgres_to_s3_task(**context):
    """Wrapper task to extract PostgreSQL tables to S3."""
    execution_date = context.get("ds")
    run_ts = context.get("ts_nodash")
    return extract_all(execution_date=execution_date, run_ts=run_ts)



DBT_PROJECT_DIR = "/opt/airflow/dags/dbt"
DBT_PROFILES_DIR = "/opt/airflow/dags/dbt"

default_args = {
    "owner": "data_engineering",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": True,
    "email": ["data-eng-alerts@company.com"],
}

with DAG(
    dag_id="datawarehousing",
    description="Extract from PostgreSQL to S3, then run dbt",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    default_args=default_args,
    tags=["postgres", "s3", "dbt", "snowflake"],
) as dag:

    generate_fake_data_task = PythonOperator(
        task_id="generate_fake_data",
        python_callable=generate_fake_data,
        op_kwargs={
            "customer_count": random.randint(5, 15),
            "product_count": random.randint(3, 7),
            "order_count": random.randint(10, 50),
        },
    )

    extract_postgres_to_s3 = PythonOperator(
        task_id="extract_postgres_to_s3",
        python_callable=extract_postgres_to_s3_task,
    )

    max_time_sync_task = PythonOperator(
        task_id="wait_for_max_time_sync",
        python_callable=wait_for_max_time_sync,
    )

    check_dbt = BashOperator(
        task_id="check_dbt",
        bash_command="""
        echo "===== DBT VERSION ====="
        which dbt || true
        dbt --version || true

        echo "===== INSTALLED DBT PACKAGES ====="
        pip list | grep dbt || true

        echo "===== PROJECT DIRECTORY ====="
        ls -la /opt/airflow/dags/dbt || true
        """,
    )

    dbt_packages = BashOperator(
        task_id="dbt_packages",
        bash_command=f"""
        set -e
        cd {DBT_PROJECT_DIR}
        dbt deps --profiles-dir {DBT_PROFILES_DIR}
        """,
    )

    run_staging = BashOperator(
        task_id="run_staging",
        bash_command=f"""
        set -e
        cd {DBT_PROJECT_DIR}
        dbt run --select stage --target snowflake --profiles-dir {DBT_PROFILES_DIR}
        """,
    )

    run_snapshot = BashOperator(
        task_id="run_snapshot",
        bash_command=f"""
        set -e
        cd {DBT_PROJECT_DIR}
        dbt snapshot --target snowflake --profiles-dir {DBT_PROFILES_DIR}
        """,
    )

    run_dimensions = BashOperator(
        task_id="run_dimensions",
        bash_command=f"""
        set -e
        cd {DBT_PROJECT_DIR}
        dbt run --select marts.dimension --target snowflake --profiles-dir {DBT_PROFILES_DIR}
        """,
    )

    run_facts = BashOperator(
        task_id="run_facts",
        bash_command=f"""
        set -e
        cd {DBT_PROJECT_DIR}
        dbt run --select marts.fact --target snowflake --profiles-dir {DBT_PROFILES_DIR}
        """,
    )

    run_marketing = BashOperator(
        task_id="run_marketing",
        bash_command=f"""
        set -e
        cd {DBT_PROJECT_DIR}
        dbt run --select marts.marketing --target snowflake --profiles-dir {DBT_PROFILES_DIR}
        """,
    )

    run_sales = BashOperator(
        task_id="run_sales",
        bash_command=f"""
        set -e
        cd {DBT_PROJECT_DIR}
        dbt run --select marts.sales --target snowflake --profiles-dir {DBT_PROFILES_DIR}
        """,
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=f"""
        set -e
        cd {DBT_PROJECT_DIR}
        dbt test --target snowflake --profiles-dir {DBT_PROFILES_DIR}
        """,
    )

    generate_fake_data_task >> extract_postgres_to_s3 >> max_time_sync_task >> check_dbt >> dbt_packages >> run_staging >> run_snapshot >> run_dimensions >> run_facts >> run_marketing >> run_sales >> dbt_test