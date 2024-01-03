"""The main entrypoint to the application."""

import uvicorn

from india_api import internal
from india_api.internal.service import get_db_client, server

# Dependency inject the desired database client
server.dependency_overrides[get_db_client] = lambda: internal.inputs.dummydb.Client()


def run() -> None:
    """Run the API using a uvicorn server."""
    uvicorn.run(
        server,
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="debug",
        workers=1,
        limit_concurrency=2,
    )


if __name__ == "__main__":
    run()
