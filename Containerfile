# Build a virtualenv using venv
# * Install required compilation tools for wheels via apt
FROM python-3.12-slim AS build-venv
RUN apt -qq update && apt -qq install -y build-essential
RUN python3 -m venv /venv
RUN /venv/bin/pip install --upgrade -q pip wheel setuptools

# Install packages into the virtualenv as a separate step
# * Only re-execute this step when the requirements files change
FROM build-venv AS install-deps
WORKDIR /app
COPY pyproject.toml pyproject.toml
RUN /venv/bin/pip install -q . --no-cache-dir --no-binary=fake_api

# Build binary for the package
# * The package is versioned via setuptools_git_versioning
#   hence the .git directory is required
# * The README.md is required for the long description
FROM install-deps AS build-app
COPY src src
COPY .git .git
COPY README.md README.md
RUN /venv/bin/pip install .

# Copy the virtualenv into a distroless image
# * These are small images that only contain the runtime dependencies
FROM gcr.io/distroless/python3-debian11
WORKDIR /app
COPY --from=build-app /venv /venv
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
ENTRYPOINT ["/venv/bin/run-api"]
