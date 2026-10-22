-- A passing singular test returns zero rows.
SELECT service_date, station_id
FROM {{ ref('daily_station_departures') }}
GROUP BY service_date, station_id
HAVING COUNT(*) > 1

UNION ALL

SELECT service_date, station_id
FROM {{ ref('daily_station_departures') }}
WHERE scheduled_departures <= 0
