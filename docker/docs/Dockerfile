FROM python:3.14.7-alpine3.24@sha256:9e9fde4d32eedce0b661d9ab91e826b62dddf28e928c230ec55f1866cac66b01

RUN apk add --no-cache graphviz=12.2.1-r3 font-dejavu=2.37-r6

WORKDIR /opt/depencity
COPY pyproject.toml uv.lock README.md LICENSE ./
COPY src ./src
RUN python -m pip install --no-cache-dir uv==0.13.4 \
    && uv sync --locked --no-dev

ENV PATH="/opt/depencity/.venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH="/workspace/src"
WORKDIR /workspace
ENTRYPOINT ["python", "scripts/update_model_cases_and_docs.py"]
