
WITH last_stops AS (
    SELECT
        trip_id,
        MAX(stop_sequence) AS last_sequence
    FROM {{ source('gtfs', 'stop_times') }}
    GROUP BY trip_id
),

daily_trips AS (
    SELECT
        sd.service_date,
        t.trip_id,
        COALESCE(
            NULLIF(TRIM(r.route_short_name), ''),
            'Unknown'
        ) AS train_category

    FROM {{ source('gtfs', 'service_dates') }} sd

    JOIN {{ source('gtfs', 'trips') }} t
        ON sd.service_id = t.service_id

    JOIN {{ source('gtfs', 'routes') }} r
        ON t.route_id = r.route_id
),

trip_departures AS (
    SELECT
        dt.service_date,
        dt.train_category,
        dt.trip_id,

        COUNT(st.trip_id) FILTER (
            WHERE st.stop_sequence < ls.last_sequence
              AND NULLIF(st.departure_time, '') IS NOT NULL
              AND COALESCE(
                  NULLIF(st.pickup_type, ''), '0'
              ) <> '1'
              AND s.stop_id IS NOT NULL
        ) AS scheduled_departures

    FROM daily_trips dt

    LEFT JOIN {{ source('gtfs', 'stop_times') }} st
        ON dt.trip_id = st.trip_id

    LEFT JOIN last_stops ls
        ON dt.trip_id = ls.trip_id

    LEFT JOIN {{ source('gtfs', 'stops') }} s
        ON st.stop_id = s.stop_id

    GROUP BY
        dt.service_date,
        dt.train_category,
        dt.trip_id
)

SELECT
    service_date,
    train_category,
    COUNT(*) AS scheduled_trips,
    SUM(scheduled_departures) AS scheduled_departures

FROM trip_departures

GROUP BY
    service_date,
    train_category
