
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    ForeignKey,
    Identity,
    Numeric,
    String,
    Text,
    TIMESTAMP,
    UniqueConstraint,
    func
)

from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship
)

from geoalchemy2 import Geography


# Base class for all database models
class Base(DeclarativeBase):
    pass


# ==========================================
# 1. ENVIRONMENTAL SOURCES
# ==========================================

class EnvironmentalSource(Base):

    __tablename__ = "environmental_sources"

    source_id: Mapped[int] = mapped_column(
        BigInteger, Identity(always=True), primary_key=True
    )

    source_name: Mapped[str] = mapped_column(
        String(150), nullable=False
    )

    source_type: Mapped[str | None] = mapped_column(String(50))

    source_url: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now()
    )

    stations = relationship(
        "MonitoringStation",
        back_populates="source"
    )

    measurements = relationship(
        "AirQualityMeasurement",
        back_populates="source"
    )


# ==========================================
# 2. MONITORING STATIONS
# ==========================================

class MonitoringStation(Base):

    __tablename__ = "monitoring_stations"

    station_id: Mapped[int] = mapped_column(
        BigInteger, Identity(always=True), primary_key=True
    )

    station_code: Mapped[str | None] = mapped_column(String(100))

    station_name: Mapped[str] = mapped_column(
        String(200), nullable=False
    )

    city: Mapped[str | None] = mapped_column(String(100))

    district: Mapped[str | None] = mapped_column(String(100))

    state: Mapped[str | None] = mapped_column(
        String(100), server_default="Karnataka"
    )

    location = mapped_column(
        Geography(geometry_type="POINT", srid=4326),
        nullable=False
    )

    source_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("environmental_sources.source_id")
    )

    is_active: Mapped[bool | None] = mapped_column(
        Boolean, server_default="true"
    )

    created_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now()
    )

    source = relationship(
        "EnvironmentalSource",
        back_populates="stations"
    )

    measurements = relationship(
        "AirQualityMeasurement",
        back_populates="station"
    )


# ==========================================
# 3. AIR QUALITY MEASUREMENTS
# ==========================================

class AirQualityMeasurement(Base):

    __tablename__ = "air_quality_measurements"

    measurement_id: Mapped[int] = mapped_column(
        BigInteger, Identity(always=True), primary_key=True
    )

    station_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("monitoring_stations.station_id"),
        nullable=False
    )

    source_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("environmental_sources.source_id"),
        nullable=False
    )

    observed_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False
    )

    aqi: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))

    aqi_category: Mapped[str | None] = mapped_column(String(50))

    pm2_5: Mapped[Decimal | None] = mapped_column(Numeric(10, 3))

    pm10: Mapped[Decimal | None] = mapped_column(Numeric(10, 3))

    no2: Mapped[Decimal | None] = mapped_column(Numeric(10, 3))

    so2: Mapped[Decimal | None] = mapped_column(Numeric(10, 3))

    co: Mapped[Decimal | None] = mapped_column(Numeric(10, 3))

    o3: Mapped[Decimal | None] = mapped_column(Numeric(10, 3))

    created_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now()
    )

    station = relationship(
        "MonitoringStation",
        back_populates="measurements"
    )

    source = relationship(
        "EnvironmentalSource",
        back_populates="measurements"
    )

    __table_args__ = (
        UniqueConstraint(
            "station_id",
            "source_id",
            "observed_at"
        ),
        CheckConstraint("aqi IS NULL OR aqi >= 0"),
        CheckConstraint("pm2_5 IS NULL OR pm2_5 >= 0"),
        CheckConstraint("pm10 IS NULL OR pm10 >= 0"),
        CheckConstraint("no2 IS NULL OR no2 >= 0"),
        CheckConstraint("so2 IS NULL OR so2 >= 0"),
        CheckConstraint("co IS NULL OR co >= 0"),
        CheckConstraint("o3 IS NULL OR o3 >= 0"),
    )
