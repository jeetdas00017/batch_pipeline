from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

DBT_PROJECT_DIR = "C:\\Users\\admin\\OneDrive\\Documents\\projects\\git_path\\projects\\dbt"
DBT_PROFILES_DIR = "C:\\Users\\admin\\OneDrive\\Documents\\projects\\git_path\\projects\\dbt"
default_args = {
    "owner": "data_engineering",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": True,
    "email": ["data-eng-alerts@company.com"],
}

with DAG(
        
    dag_id="dbt_trigger_dag",
    description="Test PostgreSQL -> S3 extraction",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["test", "postgres", "s3"],
) as dag:

    stg_run = BashOperator(
        task_id="run_staging",
        bash_command=f"""
        cd {DBT_PROJECT_DIR}
        dbt run --select staging --profiles-dir {DBT_PROFILES_DIR}
        """
    )

    int_run = BashOperator(
        task_id="run_intermediate",
        bash_command=f"""
        cd {DBT_PROJECT_DIR}
        dbt run --select int --profiles-dir {DBT_PROFILES_DIR}
        """
    )

    dim_run = BashOperator(
        task_id="run_dimensions",
        bash_command=f"""
        cd {DBT_PROJECT_DIR}
        dbt run --select marts.dimension --profiles-dir {DBT_PROFILES_DIR}
        """
    )

    fact_run = BashOperator(
        task_id="run_facts",
        bash_command=f"""
        cd {DBT_PROJECT_DIR}
        dbt run --select marts.fact --profiles-dir {DBT_PROFILES_DIR}
        """
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=f"""
        cd {DBT_PROJECT_DIR}
        dbt test --profiles-dir {DBT_PROFILES_DIR}
        """
    )

    dbt_test >> stg_run >> int_run >> dim_run >> fact_run