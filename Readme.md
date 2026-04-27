# List all pumps on testbed TB-01
curl "http://localhost:8000/api/v1/pumps?testbed=TB-01"

# Latest state of a pump
curl "http://localhost:8000/api/v1/pumps/PUMP-001/summary"

# RPM over time (1-minute buckets)
curl "http://localhost:8000/api/v1/pumps/PUMP-001/timeseries?metric=rpm&bucket=1+minute&agg=avg"

# Compare discharge pressure across pumps
curl "http://localhost:8000/api/v1/compare?pump_ids=PUMP-001,PUMP-002,PUMP-003&metric=discharge_pressure&bucket=5+minutes&agg=avg"

# Vibration data for analysis
curl "http://localhost:8000/api/v1/pumps/PUMP-001/vibration?limit=1000"

# 3-phase power readings
curl "http://localhost:8000/api/v1/pumps/PUMP-001/power"

# Label distribution for ML
curl "http://localhost:8000/api/v1/pumps/PUMP-001/labels"