
from sqlalchemy import select, func

from app.database import SessionLocal
from app.models import (
    EnvironmentalSource,
    MonitoringStation,
    AirQualityMeasurement
)

db = SessionLocal()

try:
    source_count = db.scalar(
        select(func.count()).select_from(EnvironmentalSource)
    )

    station_count = db.scalar(
        select(func.count()).select_from(MonitoringStation)
    )

    measurement_count = db.scalar(
        select(func.count()).select_from(AirQualityMeasurement)
    )

    print("SQLAlchemy models connected successfully!")

    print("Environmental sources:", source_count)
    print("Monitoring stations:", station_count)
    print("Air quality measurements:", measurement_count)

finally:
    db.close()
