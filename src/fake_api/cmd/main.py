"""The main entrypoint to the application."""

import uvicorn

from fake_api.internal.service import server


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

