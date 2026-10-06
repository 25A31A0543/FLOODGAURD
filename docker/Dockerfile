# ============================================================
# FloodGuard AI Platform - Production Multi-Stage Dockerfile
# Step 5: Integration & Scaling
# ============================================================

# Stage 1: Builder
FROM python:3.11-slim AS builder
WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt && \
    pip install --no-cache-dir --prefix=/install "prometheus-client>=0.19.0"

# Stage 2: Runtime
FROM python:3.11-slim AS runtime
LABEL maintainer="FloodGuard AI Team"
LABEL version="1.0.0"
LABEL description="FloodGuard AI Flood Early Warning Platform"
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libpq-dev curl && rm -rf /var/lib/apt/lists/*
COPY --from=builder /install /usr/local
COPY floodguard/ ./floodguard/
RUN mkdir -p /app/data
COPY run_server.py .
RUN groupadd -r floodguard && useradd -r -g floodguard floodguard && chown -R floodguard:floodguard /app
USER floodguard
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1
CMD ["uvicorn", "floodguard.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--log-level", "info"]
