SELECT service_date, departure_hour
FROM {{ ref('hourly_departures') }}
WHERE departure_hour NOT BETWEEN 0 AND 23
   OR scheduled_departures <= 0
