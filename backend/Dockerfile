# syntax=docker/dockerfile:1

# -----------------------------------------------------------------------------
# Stage 1: install Python dependencies
# -----------------------------------------------------------------------------
FROM python:3.12-slim AS builder

WORKDIR /backend

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# -----------------------------------------------------------------------------
# Stage 2: production runtime (uses .env.production)
# -----------------------------------------------------------------------------
FROM python:3.12-slim AS production

WORKDIR /backend

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=production

COPY --from=builder /install /usr/local
COPY main.py config.py models.py .env.production ./
COPY epcis/ epcis/

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
