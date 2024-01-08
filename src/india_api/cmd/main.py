"""The main entrypoint to the application."""

import uvicorn

from india_api import internal
from india_api.internal.config import Config
from india_api.internal.service import get_db_client, server


cfg = Config()

match cfg.SOURCE:
    case "dummydb":

        def get_db_client_override() -> internal.DatabaseInterface:
            return internal.inputs.dummydb.Client()
    case _:
        raise ValueError(f"Unknown SOURCE: {cfg.SOURCE}. Expected 'dummydb'.")

# Dependency inject the desired database client
server.dependency_overrides[get_db_client] = get_db_client_override


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
