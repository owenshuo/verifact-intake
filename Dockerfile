FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    VERIFACT_DATABASE_URL=sqlite:////app/runtime/verifact.db

WORKDIR /app

RUN groupadd --system verifact \
    && useradd --system --gid verifact --home-dir /app verifact \
    && mkdir -p /app/runtime \
    && chown -R verifact:verifact /app

COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN python -m pip install .

COPY data/synthetic ./data/synthetic
COPY output/pdf ./output/pdf
COPY web ./web

USER verifact
EXPOSE 8080

HEALTHCHECK --interval=20s --timeout=3s --start-period=8s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/healthz', timeout=2)" || exit 1

CMD ["python", "-m", "uvicorn", "verifact_intake.api:app", "--host", "0.0.0.0", "--port", "8080"]
