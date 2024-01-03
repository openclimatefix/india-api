# India API

Defines an API to help with building frontends pertaining to displaying wind and solar data.

## Running the service

Clone the repository,
and create a new virtual environment with your favorite environment manager.
Install the dependencies with

```
$ pip install -e .[dev]
```

The service is then runnable via the command `india-api`.
You should see the following output:

```shell
INFO:     Started server process [87312]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

The API should then be accessible at `http://localhost:8000`,
and the docs at `http://localhost:8000/docs`.

