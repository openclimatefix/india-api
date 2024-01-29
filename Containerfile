FROM python:3.11-slim

# install requirements
RUN apt-get clean

# Copy required files.
WORKDIR /app
COPY pyproject.toml pyproject.toml
COPY src src
COPY README.md README.md

# set working directory
WORKDIR /app

# Install python requirements.
RUN pip install .

# health check and entrypoint
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:${PORT}/health || exit 1
ENTRYPOINT ["india-api"]
