# Build a virtualenv using venv
# * Install required compilation tools for wheels via apt
FROM debian:12-slim AS build
RUN apt -qq update && apt -qq install -y python3-venv gcc libpython3-dev && \
    python3 -m venv /venv && \
    /venv/bin/pip install --upgrade -q pip setuptools wheel

# Install packages into the virtualenv as a separate step
# * Only re-execute this step when the requirements files change
FROM build AS install-deps
WORKDIR /app
COPY pyproject.toml pyproject.toml
RUN /venv/bin/pip install -q . --no-cache-dir --no-binary=india_api

# Build binary for the package
# * The package is versioned via setuptools_git_versioning
#   hence the .git directory is required
# * The README.md is required for the long description
FROM install-deps AS build-app
COPY src src
COPY .git .git
COPY README.md README.md
RUN /venv/bin/pip install .
RUN ls /venv/bin

# Copy the virtualenv into a distroless image
# * These are small images that only contain the runtime dependencies
FROM gcr.io/distroless/python3-debian12
COPY --from=build-app /venv /venv
WORKDIR /app
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
ENTRYPOINT ["/venv/bin/fake-api"]

