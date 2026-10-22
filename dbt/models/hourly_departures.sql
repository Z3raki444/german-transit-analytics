
WITH trip_last_stops AS (
    SELECT
        trip_id,
        MAX(stop_sequence) AS last_sequence
    FROM {{ source('gtfs', 'stop_times') }}
    GROUP BY trip_id
),

valid_departures AS (
    SELECT
        cal.service_date,
        MOD(
            SPLIT_PART(st.departure_time, ':', 1)::INTEGER,
            24
        ) AS departure_hour,
        st.trip_id

    FROM {{ source('gtfs', 'service_dates') }} cal

    JOIN {{ source('gtfs', 'trips') }} t
        ON cal.service_id = t.service_id

    JOIN {{ source('gtfs', 'stop_times') }} st
        ON t.trip_id = st.trip_id

    JOIN trip_last_stops last_stop
        ON st.trip_id = last_stop.trip_id

    JOIN {{ source('gtfs', 'stops') }} s
        ON st.stop_id = s.stop_id

    WHERE NULLIF(st.departure_time, '') IS NOT NULL
      AND st.stop_sequence < last_stop.last_sequence
      AND COALESCE(NULLIF(st.pickup_type, ''), '0') <> '1'
)

SELECT
    service_date,
    departure_hour,
    COUNT(*) AS scheduled_departures

FROM valid_departures

GROUP BY service_date, departure_hour
