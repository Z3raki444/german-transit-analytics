
WITH selected_date AS (
    -- Automatically choose a date covered by the dataset
    SELECT MIN(service_date) AS travel_date
    FROM service_dates
),

daily_departures AS (
    SELECT
        sd.travel_date,
        COALESCE(
            NULLIF(s.parent_station, ''),
            s.stop_id
        ) AS station_id,
        COALESCE(p.stop_name, s.stop_name) AS station_name,
        st.trip_id

    FROM selected_date sd

    JOIN service_dates cal
        ON cal.service_date = sd.travel_date

    JOIN trips t
        ON t.service_id = cal.service_id

    JOIN stop_times st
        ON st.trip_id = t.trip_id

    JOIN stops s
        ON st.stop_id = s.stop_id

    LEFT JOIN stops p
        ON p.stop_id = NULLIF(s.parent_station, '')

    WHERE NULLIF(st.departure_time, '') IS NOT NULL

      -- Exclude the final stop of each journey
      AND EXISTS (
          SELECT 1
          FROM stop_times next_stop
          WHERE next_stop.trip_id = st.trip_id
            AND next_stop.stop_sequence > st.stop_sequence
      )
)

SELECT
    travel_date,
    station_id,
    MAX(station_name) AS station_name,
    COUNT(*) AS scheduled_departures

FROM daily_departures

GROUP BY travel_date, station_id
ORDER BY scheduled_departures DESC
LIMIT 10;
