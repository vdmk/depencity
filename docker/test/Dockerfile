FROM python:3.14.7-alpine3.24@sha256:9e9fde4d32eedce0b661d9ab91e826b62dddf28e928c230ec55f1866cac66b01

WORKDIR /opt/depencity
COPY pyproject.toml uv.lock README.md LICENSE ./
COPY src ./src

# Dependencies are installed during the build; tests run without network access.
RUN python -m pip install --no-cache-dir uv==0.13.4 \
    && uv sync --locked --group dev

COPY tests ./tests
COPY scripts ./scripts

ENV PATH="/opt/depencity/.venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1

CMD ["pytest", "-q", "tests", "-p", "no:cacheprovider", "--import-mode=importlib", "-n", "2"]
