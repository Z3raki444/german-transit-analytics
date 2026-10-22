
import pendulum

from airflow.sdk import DAG
from airflow.providers.standard.operators.bash import BashOperator

with DAG(
    dag_id="german_transit_etl",
    start_date=pendulum.datetime(2026, 10, 22, tz="Europe/Berlin"),
    schedule=None,
    catchup=False,
    max_active_runs=1,
    tags=["germany", "transit", "etl"],
) as dag:

    extract = BashOperator(
        task_id="extract_gtfs",
        bash_command="python src/ingestion/extract_gtfs_static.py",
        cwd="/opt/airflow/project",
    )

    transform = BashOperator(
        task_id="transform_stops",
        bash_command="python src/transform/clean_stops.py",
        cwd="/opt/airflow/project",
    )

    load = BashOperator(
        task_id="load_stops",
        bash_command="python src/load/load_stops.py",
        cwd="/opt/airflow/project",
    )

    
    transform_routes = BashOperator(
        task_id="transform_routes",
        bash_command="python src/transform/clean_routes.py",
        cwd="/opt/airflow/project",
    )

    load_routes = BashOperator(
        task_id="load_routes",
        bash_command="python src/load/load_routes.py",
        cwd="/opt/airflow/project",
    )

    
    # Transform train journeys
    transform_trips = BashOperator(
        task_id="transform_trips",
        bash_command="python src/transform/clean_trips.py",
        cwd="/opt/airflow/project",
    )

    # Load journeys into PostgreSQL
    load_trips = BashOperator(
        task_id="load_trips",
        bash_command="python src/load/load_trips.py",
        cwd="/opt/airflow/project",
    )

    # Transform arrival and departure times
    transform_stop_times = BashOperator(
        task_id="transform_stop_times",
        bash_command="python src/transform/clean_stop_times.py",
        cwd="/opt/airflow/project",
    )

    # Load arrival and departure times
    load_stop_times = BashOperator(
        task_id="load_stop_times",
        bash_command="python src/load/load_stop_times.py",
        cwd="/opt/airflow/project",
    )

    
    transform_calendar = BashOperator(
        task_id="transform_service_calendar",
        bash_command="python src/transform/clean_service_calendar.py",
        cwd="/opt/airflow/project",
    )

    load_calendar = BashOperator(
        task_id="load_service_calendar",
        bash_command="python src/load/load_service_dates.py",
        cwd="/opt/airflow/project",
    )

    
    quality_checks = BashOperator(
        task_id="validate_gtfs_data",
        bash_command="python src/quality/check_gtfs_quality.py",
        cwd="/opt/airflow/project",
    )

    
    build_analytics = BashOperator(
        task_id="build_analytics_models",
        bash_command=(
            "dbt build "
            "--project-dir /opt/airflow/project/dbt "
            "--profiles-dir /opt/airflow/project/dbt"
        ),
        cwd="/opt/airflow/project",
    )

    
    extract >> transform >> load >> transform_routes >> load_routes

    load_routes >> transform_trips >> load_trips

    load_trips >> transform_stop_times >> load_stop_times

    load_stop_times >> transform_calendar >> load_calendar

    load_calendar >> quality_checks

    