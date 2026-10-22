
import os
import streamlit as st
import psycopg
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="German Transit Analytics",
    page_icon="🚆",
    layout="wide"
)

st.title("🚆 German Transit Analytics")
st.caption("Long-distance railway timetables · scheduled departures · GTFS data")

@st.cache_data(ttl=300)
def get_summary():
    with psycopg.connect(
        host=os.getenv("TRANSIT_DB_HOST", "postgres"),
        port=5432,
        dbname="transit_analytics",
        user="transit_user",
        password=os.environ["TRANSIT_DB_PASSWORD"]
    ) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    COUNT(*) AS records,
                    COUNT(DISTINCT station_id) AS stations,
                    COUNT(DISTINCT service_date) AS days,
                    MIN(service_date),
                    MAX(service_date)
                FROM analytics.daily_station_departures
            """)
            return cur.fetchone()

try:
    records, stations, days, first_date, last_date = get_summary()
except (psycopg.Error, KeyError):
    st.error("Unable to connect to the transit analytics database.")
    st.stop()

col1, col2, col3 = st.columns(3)

col1.metric("Station-Date Records", f"{records:,}")
col2.metric("Stations with Departures", f"{stations:,}")
col3.metric("Service Dates", days)

st.info(f"Dataset coverage: {first_date} to {last_date}")


# Database connection settings
def connect_db():
    return psycopg.connect(
        host=os.getenv("TRANSIT_DB_HOST", "postgres"),
        port=int(os.getenv("TRANSIT_DB_PORT", "5432")),
        dbname="transit_analytics",
        user="transit_user",
        password=os.environ["TRANSIT_DB_PASSWORD"]
    )


# Get dates available in the dataset
@st.cache_data(ttl=300)
def get_available_dates():
    with connect_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT service_date
                FROM analytics.daily_station_departures
                ORDER BY service_date
            """)
            return [row[0] for row in cur.fetchall()]


# Get top 10 stations for a selected date
@st.cache_data(ttl=300)
def get_top_stations(selected_date):
    with connect_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    station_name,
                    scheduled_departures
                FROM analytics.daily_station_departures
                WHERE service_date = %s
                ORDER BY scheduled_departures DESC
                LIMIT 10
            """, (selected_date,))

            return pd.DataFrame(
                cur.fetchall(),
                columns=["Station", "Scheduled Departures"]
            )


st.divider()
st.subheader("Top 10 Busiest Railway Stations")

available_dates = get_available_dates()

if not available_dates:
    st.warning("No scheduled departure data available.")
    st.stop()

st.sidebar.header("Explore railway schedules")
st.sidebar.caption("Scheduled timetable data — not realtime delay data.")

selected_date = st.sidebar.selectbox(
    "Select Service Date",
    available_dates,
    format_func=lambda d: d.strftime("%d %B %Y")
)


# Daily KPI Summary
@st.cache_data(ttl=300)
def get_daily_kpis(selected_date):
    with connect_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    COALESCE((
                        SELECT SUM(scheduled_departures)
                        FROM analytics.daily_station_departures
                        WHERE service_date = %s
                    ), 0),

                    (
                        SELECT COUNT(*)
                        FROM analytics.daily_station_departures
                        WHERE service_date = %s
                    ),

                    COALESCE((
                        SELECT SUM(scheduled_trips)
                        FROM analytics.train_service_summary
                        WHERE service_date = %s
                    ), 0)
            """, (selected_date, selected_date, selected_date))

            return cur.fetchone()


departures, stations, trips = get_daily_kpis(selected_date)

kpi1, kpi2, kpi3 = st.columns(3)

kpi1.metric("Scheduled Departures", f"{departures:,}")
kpi2.metric("Active Stations", f"{stations:,}")
kpi3.metric("Scheduled Trips", f"{trips:,}")


top_stations = get_top_stations(selected_date)

if not top_stations.empty:
    fig = px.bar(
        top_stations.sort_values("Scheduled Departures"),
        x="Scheduled Departures",
        y="Station",
        orientation="h",
        title="Top 10 Stations by Scheduled Departures"
    )

    fig.update_layout(
        height=500,
        yaxis_title="",
        xaxis_title="Scheduled Departures"
    )

    st.plotly_chart(fig, width="stretch")

    st.dataframe(top_stations, hide_index=True)
else:
    st.warning("No station departures for this date.")


# ----------------------------------------
# Peak Hour Departure Analysis
# ----------------------------------------

@st.cache_data(ttl=300)
def get_hourly_departures(selected_date):
    with connect_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    departure_hour,
                    scheduled_departures
                FROM analytics.hourly_departures
                WHERE service_date = %s
                ORDER BY departure_hour
            """, (selected_date,))

            rows = cur.fetchall()

    df = pd.DataFrame(
        rows,
        columns=["Hour", "Departures"]
    )

    # Include hours with zero departures
    all_hours = pd.DataFrame({"Hour": range(24)})

    df = all_hours.merge(df, on="Hour", how="left")
    df["Departures"] = df["Departures"].fillna(0).astype(int)

    return df


st.divider()
st.subheader("Peak Train Departure Hours")

hourly_data = get_hourly_departures(selected_date)

if hourly_data["Departures"].sum() > 0:

    peak = hourly_data.loc[
        hourly_data["Departures"].idxmax()
    ]

    col1, col2 = st.columns(2)

    col1.metric(
        "Peak Departure Hour",
        f"{int(peak['Hour']):02d}:00"
    )

    col2.metric(
        "Departures During Peak Hour",
        f"{int(peak['Departures']):,}"
    )

    fig = px.bar(
        hourly_data,
        x="Hour",
        y="Departures",
        title="Scheduled Departures by Hour",
        labels={
            "Hour": "Hour of Day",
            "Departures": "Scheduled Departures"
        }
    )

    fig.update_layout(
        height=450,
        xaxis=dict(
            tickmode="linear",
            tick0=0,
            dtick=2
        ),
        hovermode="x unified"
    )

    st.plotly_chart(fig, width="stretch")

else:
    st.warning("No hourly departure data for this date.")


# ----------------------------------------
# Train Category Comparison
# ----------------------------------------

@st.cache_data(ttl=300)
def get_train_categories(selected_date):
    with connect_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    train_category,
                    SUM(scheduled_trips) AS scheduled_trips,
                    SUM(scheduled_departures) AS scheduled_departures
                FROM analytics.train_service_summary
                WHERE service_date = %s
                GROUP BY train_category
                ORDER BY scheduled_departures DESC
            """, (selected_date,))

            rows = cur.fetchall()

    return pd.DataFrame(
        rows,
        columns=[
            "Train Category",
            "Scheduled Trips",
            "Scheduled Departures"
        ]
    )


st.divider()
st.subheader("Train Category Comparison")

category_data = get_train_categories(selected_date)

if not category_data.empty:

    col1, col2 = st.columns(2)

    col1.metric(
        "Total Scheduled Trips",
        f"{category_data['Scheduled Trips'].sum():,.0f}"
    )

    col2.metric(
        "Total Scheduled Departures",
        f"{category_data['Scheduled Departures'].sum():,.0f}"
    )

    metric = st.radio(
        "Compare train categories by",
        ["Scheduled Departures", "Scheduled Trips"],
        horizontal=True
    )

    chart_data = (
        category_data
        .sort_values(metric, ascending=False)
        .head(10)
        .sort_values(metric)
    )

    fig = px.bar(
        chart_data,
        x=metric,
        y="Train Category",
        orientation="h",
        color="Train Category",
        text=metric,
        title=f"Top Train Categories by {metric}"
    )

    fig.update_layout(
        height=450,
        showlegend=False,
        yaxis_title="",
        xaxis_title=metric
    )

    st.plotly_chart(fig, width="stretch")

    st.dataframe(
        category_data,
        hide_index=True,
        width="stretch"
    )

else:
    st.warning("No train category data for this date.")



# ----------------------------------------
# Interactive Railway Station Map
# ----------------------------------------

@st.cache_data(ttl=300)
def get_station_map(selected_date):
    with connect_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                WITH child_coordinates AS (
                    SELECT
                        parent_station AS station_id,
                        AVG(stop_lat) AS latitude,
                        AVG(stop_lon) AS longitude
                    FROM public.stops
                    WHERE NULLIF(parent_station, '') IS NOT NULL
                    GROUP BY parent_station
                )

                SELECT
                    d.station_name,
                    d.scheduled_departures,
                    COALESCE(s.stop_lat, c.latitude),
                    COALESCE(s.stop_lon, c.longitude)

                FROM analytics.daily_station_departures d

                LEFT JOIN public.stops s
                    ON d.station_id = s.stop_id

                LEFT JOIN child_coordinates c
                    ON d.station_id = c.station_id

                WHERE d.service_date = %s

                ORDER BY d.scheduled_departures DESC
            """, (selected_date,))

            rows = cur.fetchall()

    return pd.DataFrame(
        rows,
        columns=[
            "Station",
            "Scheduled Departures",
            "Latitude",
            "Longitude"
        ]
    )


st.divider()
st.subheader("German Railway Station Map")

map_data = get_station_map(selected_date)

map_data = map_data.dropna(
    subset=["Latitude", "Longitude"]
)

if not map_data.empty:

    fig_map = px.scatter_map(
        map_data,
        lat="Latitude",
        lon="Longitude",
        size="Scheduled Departures",
        color="Scheduled Departures",
        hover_name="Station",
        hover_data={
            "Latitude": False,
            "Longitude": False,
            "Scheduled Departures": True
        },
        size_max=25,
        zoom=5,
        center={"lat": 51.2, "lon": 10.45},
        map_style="open-street-map",
        height=600,
        title="Scheduled Railway Departures by Station"
    )

    fig_map.update_layout(
        margin=dict(l=0, r=0, t=45, b=0)
    )

    st.plotly_chart(fig_map, width="stretch")

    st.caption(
        "Marker size represents scheduled departures "
        "on the selected GTFS service date."
    )

else:
    st.warning("No station coordinates available for this date.")
