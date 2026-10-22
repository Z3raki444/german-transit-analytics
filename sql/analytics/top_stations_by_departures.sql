
SELECT
    s.stop_name AS station_name,
    COUNT(*) AS scheduled_departures,
    COUNT(DISTINCT st.trip_id) AS unique_trips

FROM stop_times st

JOIN stops s
    ON st.stop_id = s.stop_id

WHERE st.departure_time IS NOT NULL

-- Exclude the final stop of each trip
AND EXISTS (
    SELECT 1
    FROM stop_times next_stop
    WHERE next_stop.trip_id = st.trip_id
      AND next_stop.stop_sequence > st.stop_sequence
)

GROUP BY s.stop_name

ORDER BY scheduled_departures DESC

LIMIT 10;
