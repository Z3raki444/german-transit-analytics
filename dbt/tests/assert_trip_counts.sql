SELECT service_date, train_category
FROM {{ ref('train_service_summary') }}
WHERE scheduled_trips <= 0
   OR scheduled_departures < 0
