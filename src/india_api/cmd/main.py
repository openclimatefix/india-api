"""The main entrypoint to the application."""

import csv
from io import StringIO
import uvicorn

from india_api import internal
from india_api.internal.config import Config
from india_api.internal.service import get_db_client, server


cfg = Config()

match cfg.SOURCE:
    case "indiadb":
        if cfg.DB_URL == "" or cfg.DB_URL == None:
            raise OSError(f"DB_URL env var is required using db source: {cfg.SOURCE}")

        def get_db_client_override() -> internal.DatabaseInterface:
            return internal.inputs.indiadb.Client(cfg.DB_URL)
    case "dummydb":

        def get_db_client_override() -> internal.DatabaseInterface:
            return internal.inputs.dummydb.Client()
    case _:
        raise ValueError(f"Unknown SOURCE: {cfg.SOURCE}. Expected 'dummydb'.")

# Dependency inject the desired database client
server.dependency_overrides[get_db_client] = get_db_client_override

# Function to generate example CSV data
def generate_csv_data():
    rows = [
        {'Name': 'John', 'Age': 30, 'City': 'New York'},
        {'Name': 'Alice', 'Age': 25, 'City': 'Los Angeles'},
        {'Name': 'Bob', 'Age': 35, 'City': 'Chicago'}
    ]

    csv_data = StringIO()
    csv_writer = csv.DictWriter(csv_data, fieldnames=rows[0].keys())
    csv_writer.writeheader()
    csv_writer.writerows(rows)

    return csv_data.getvalue()


def run() -> None:
    """Run the API using a uvicorn server."""
    uvicorn.run(
        server,
        host="0.0.0.0",
        port=cfg.PORT,
        reload=False,
        log_level="debug",
        workers=1,
    )


if __name__ == "__main__":
    run()
