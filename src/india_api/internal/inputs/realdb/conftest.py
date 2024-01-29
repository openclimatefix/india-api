""" Test fixtures to set up fake database for testing. """
import os
from datetime import datetime, timedelta

import pytest
from pvsite_datamodel.connection import DatabaseConnection
from pvsite_datamodel.sqlmodels import (
    Base,
    ForecastSQL,
    ForecastValueSQL,
    GenerationSQL,
    SiteAssetType,
)
from pvsite_datamodel.write.user_and_site import create_site_group, create_user, make_fake_site
from testcontainers.postgres import PostgresContainer


@pytest.fixture(scope="session")
def engine_url():
    """Database engine, this includes the table creation."""
    with PostgresContainer("postgres:14.5") as postgres:
        url = postgres.get_connection_url()
        os.environ["DB_URL"] = url

        database_connection = DatabaseConnection(url, echo=False)

        engine = database_connection.engine

        # Would like to do this here but found the data
        # was not being deleted when using 'db_connection'
        # database_connection.create_all()
        # Base_PV.metadata.create_all(engine)

        yield url

        # Base_PV.metadata.drop_all(engine)
        # Base_Forecast.metadata.drop_all(engine)

        engine.dispose()


@pytest.fixture()
def db_connection(engine_url):
    database_connection = DatabaseConnection(engine_url, echo=False)

    engine = database_connection.engine
    # connection = engine.connect()
    # transaction = connection.begin()

    # There should be a way to only make the tables once
    # but make sure we remove the data
    Base.metadata.create_all(engine)

    yield database_connection

    # transaction.rollback()
    # connection.close()

    Base.metadata.drop_all(engine)


@pytest.fixture()
def db_session(db_connection, engine_url):
    """Return a sqlalchemy session, which tears down everything properly post-test."""

    with db_connection.get_session() as s:
        s.begin()
        yield s
        s.rollback()


@pytest.fixture()
def sites(db_session):
    """Create some fake sites"""

    site_group = create_site_group(db_session=db_session)
    create_user(
        session=db_session, email="test@test.com", site_group_name=site_group.site_group_name
    )

    sites = []
    num_sites = 2
    for j in range(num_sites):
        site = make_fake_site(db_session=db_session, ml_id=j + 1)

        if j == 1:
            site.asset_type = SiteAssetType.wind.name
        else:
            site.asset_type = SiteAssetType.pv.name
        site.country = "india"

        sites.append(site)
        site_group.sites.append(site)

    db_session.add_all(sites)
    db_session.commit()

    return sites


@pytest.fixture()
def generations(db_session, sites):
    """Create some fake generations"""
    start_times = [datetime.today() - timedelta(minutes=x) for x in range(10)]

    all_generations = []
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
def forecast_values(db_session, sites):
    """Create some fake forecast values"""
    forecast_values = []
    forecast_version: str = "0.0.0"

    num_forecasts = 10
    num_values_per_forecast = 11

    timestamps = [datetime.utcnow() - timedelta(minutes=10 * i) for i in range(num_forecasts)]

    # To make things trickier we make a second forecast at the same for one of the timestamps.
    timestamps = timestamps + timestamps[-1:]

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
