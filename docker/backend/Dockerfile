FROM python:3.13-slim AS builder

# System deps needed to build wheels for psycopg / opencv / pymupdf etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir poetry==2.4.1 poetry-plugin-export==1.9.0

# Only the dependency manifests are needed to resolve/export — keeps this
# layer cached across app-code-only changes.
COPY pyproject.toml poetry.lock ./
RUN poetry export --without-hashes --without dev -o requirements.txt

RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Final stage
FROM python:3.13-slim

# libpq-dev: psycopg runtime; curl: healthcheck; tesseract-ocr: the OCR engine
# the document pipeline actually calls (app/engines/ocr/adapters/tesseract_adapter.py);
# libgl1/libglib2.0-0: runtime libs opencv-python-headless still dlopen()s on Debian.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev curl tesseract-ocr libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Add non-root user
RUN groupadd -r claimos && useradd -r -g claimos claimos

WORKDIR /app

COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .

RUN pip install --no-cache /wheels/*

COPY . .

# Change ownership
RUN chown -R claimos:claimos /app

USER claimos

ENV PYTHONPATH=/app
ENV PORT=8000

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/api/v1/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
