
CREATE TABLE IF NOT EXISTS service_dates (
    service_id TEXT NOT NULL,
    service_date DATE NOT NULL,
    PRIMARY KEY (service_id, service_date)
);

CREATE INDEX IF NOT EXISTS idx_service_dates_date
ON service_dates (service_date);
