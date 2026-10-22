WITH daily_departures AS (

    SELECT
        cal.service_date,

        COALESCE(
            NULLIF(s.parent_station, ''),
            s.stop_id
        ) AS station_id,

        COALESCE(
            p.stop_name,
            s.stop_name
        ) AS station_name

    FROM "transit_analytics"."public"."service_dates" cal

    JOIN "transit_analytics"."public"."trips" t
        ON cal.service_id = t.service_id

    JOIN "transit_analytics"."public"."stop_times" st
        ON t.trip_id = st.trip_id

    JOIN "transit_analytics"."public"."stops" s
        ON st.stop_id = s.stop_id

    LEFT JOIN "transit_analytics"."public"."stops" p
        ON NULLIF(s.parent_station, '') = p.stop_id

    WHERE NULLIF(st.departure_time, '') IS NOT NULL

      -- Exclude stops where boarding is not permitted
      AND COALESCE(NULLIF(st.pickup_type, ''), '0') <> '1'

      -- Exclude the last stop of each trip
      AND EXISTS (
          SELECT 1
          FROM "transit_analytics"."public"."stop_times" nxt
          WHERE nxt.trip_id = st.trip_id
            AND nxt.stop_sequence > st.stop_sequence
      )
)

SELECT
    service_date,
    station_id,
    MAX(station_name) AS station_name,
    COUNT(*) AS scheduled_departures

FROM daily_departures

GROUP BY service_date, station_id