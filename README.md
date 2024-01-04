# India API

Defines an API to help with building frontends pertaining to displaying wind and solar data.

## Running the service

### Configuration

The application is configured via the use of environment variables.
Currently there is only one source adaptor
so there is nothing to configure.

### Using docker

Download the latest image from github container regiimage from github container registry:

```sh
$ docker run ghcr.io/openclimatefix/fake-api:latest
```

### Using python

Clone the repository,
and create a new virtual environment with your favorite environment manager.
Install the dependencies with

```
$ pip install -e .
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


## Development

Clone the repository,
and create a new environment with your favorite environment manager.
Install all the dependencies with

```
pip install -e .[all]
```

You can run the service with the command `india-api`.
Changes will be hot-reloaded by the server.


