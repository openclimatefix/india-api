""" Test fixtures to set up fake database for testing. """
import os
from datetime import datetime, timedelta

import pytest
from pvsite_datamodel.sqlmodels import (
    Base,
    ForecastSQL,
    ForecastValueSQL,
    GenerationSQL, SiteSQL
)
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from testcontainers.postgres import PostgresContainer


@pytest.fixture(scope="session")
def engine():
    """Database engine fixture."""

    with PostgresContainer("postgres:14.5") as postgres:
        url = postgres.get_connection_url()
        os.environ["DB_URL"] = url
        engine = create_engine(url)
        Base.metadata.create_all(engine)

        yield engine


@pytest.fixture()
def db_session(engine):
    """Return a sqlalchemy session, which tears down everything properly post-test."""

    connection = engine.connect()
    # begin the nested transaction
    transaction = connection.begin()
    # use the connection with the already started transaction

    with Session(bind=connection) as session:
        yield session

        session.close()
        # roll back the broader transaction
        transaction.rollback()
        # put back the connection to the connection pool
        connection.close()
        session.flush()

    engine.dispose()


@pytest.fixture(scope="session", autouse=True)
def db_data(engine):
    """Seed some initial data into DB."""

    with engine.connect() as connection:
        with Session(bind=connection) as session:
            # PV site
            site = SiteSQL(
                client_site_id=1,
                latitude=20.59,
                longitude=78.96,
                capacity_kw=4,
                ml_id=1,
                asset_type="pv",
                country="india"
            )
            session.add(site)

            # Wind site
            site = SiteSQL(
                client_site_id=2,
                latitude=20.59,
                longitude=78.96,
                capacity_kw=4,
                ml_id=2,
                asset_type="wind",
                country="india"
            )
            session.add(site)

            session.commit()


@pytest.fixture()
def generations(db_session):
    """Create some fake generations"""
    start_times = [datetime.today() - timedelta(minutes=x) for x in range(10)]

    all_generations = []

    sites = db_session.query(SiteSQL).all()
    for site in sites:
        for i in range(0, 10):
            generation = GenerationSQL(
                site_uuid=site.site_uuid,
                generation_power_kw=i,
                start_utc=start_times[i],
                end_utc=start_times[i] + timedelta(minutes=5),
            )
            all_generations.append(generation)

    db_session.add_all(all_generations)
    db_session.commit()

    return all_generations


@pytest.fixture()
def forecast_values(db_session):
    """Create some fake forecast values"""
    forecast_values = []
    forecast_version: str = "0.0.0"

    num_forecasts = 10
    num_values_per_forecast = 11

    timestamps = [datetime.utcnow() - timedelta(minutes=10 * i) for i in range(num_forecasts)]

    # To make things trickier we make a second forecast at the same for one of the timestamps.
    timestamps = timestamps + timestamps[-1:]

    sites = db_session.query(SiteSQL).all()
    for site in sites:
        for timestamp in timestamps:
            forecast: ForecastSQL = ForecastSQL(
                site_uuid=site.site_uuid, forecast_version=forecast_version, timestamp_utc=timestamp
            )

            db_session.add(forecast)
            db_session.commit()

            for i in range(num_values_per_forecast):
                # Forecasts of 15 minutes.
                duration = 15
                horizon = duration * i
                forecast_value: ForecastValueSQL = ForecastValueSQL(
                    forecast_power_kw=i,
                    forecast_uuid=forecast.forecast_uuid,
                    start_utc=timestamp + timedelta(minutes=horizon),
                    end_utc=timestamp + timedelta(minutes=horizon + duration),
                    horizon_minutes=horizon,
                )

                forecast_values.append(forecast_value)

    db_session.add_all(forecast_values)
    db_session.commit()

    return forecast_values
