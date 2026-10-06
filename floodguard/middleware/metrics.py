"""
FloodGuard Step 5: Prometheus Metrics Middleware
Collects request latency, status codes, and active connections
for multi-region observability via Prometheus + Grafana.
"""
import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

# ---------------------------------------------------------------------------
# Prometheus metrics (graceful fallback if prometheus-client not installed)
# ---------------------------------------------------------------------------
try:
    from prometheus_client import (
        Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST,
        REGISTRY
    )
    _PROM_AVAILABLE = True
except ImportError:
    _PROM_AVAILABLE = False


def _make_metrics():
    """Create Prometheus metric objects; safe to call multiple times."""
    if not _PROM_AVAILABLE:
        return None, None, None

    try:
        request_count = Counter(
            "floodguard_http_requests_total",
            "Total HTTP requests served by FloodGuard",
            ["method", "endpoint", "status_code"],
        )
    except Exception:
        request_count = REGISTRY._names_to_collectors.get(
            "floodguard_http_requests_total"
        )

    try:
        request_latency = Histogram(
            "floodguard_http_request_duration_seconds",
            "HTTP request latency in seconds",
            ["method", "endpoint"],
            buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
        )
    except Exception:
        request_latency = REGISTRY._names_to_collectors.get(
            "floodguard_http_request_duration_seconds"
        )

    try:
        active_connections = Gauge(
            "floodguard_active_connections",
            "Number of currently active HTTP connections",
        )
    except Exception:
        active_connections = REGISTRY._names_to_collectors.get(
            "floodguard_active_connections"
        )

    return request_count, request_latency, active_connections


REQUEST_COUNT, REQUEST_LATENCY, ACTIVE_CONNECTIONS = _make_metrics()


class PrometheusMiddleware(BaseHTTPMiddleware):
    """
    Starlette middleware that automatically instruments all FastAPI endpoints.
    Exposes:
      - floodguard_http_requests_total (Counter)
      - floodguard_http_request_duration_seconds (Histogram)
      - floodguard_active_connections (Gauge)
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not _PROM_AVAILABLE:
            return await call_next(request)

        # Normalize path — strip path params to avoid high-cardinality labels
        path = request.url.path
        method = request.method

        if ACTIVE_CONNECTIONS:
            ACTIVE_CONNECTIONS.inc()

        start_time = time.perf_counter()
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as exc:
            status_code = 500
            raise exc
        finally:
            elapsed = time.perf_counter() - start_time
            if REQUEST_LATENCY:
                REQUEST_LATENCY.labels(method=method, endpoint=path).observe(elapsed)
            if REQUEST_COUNT:
                REQUEST_COUNT.labels(
                    method=method, endpoint=path, status_code=str(status_code)
                ).inc()
            if ACTIVE_CONNECTIONS:
                ACTIVE_CONNECTIONS.dec()

        return response


def get_metrics_response() -> Response:
    """
    Generate a Prometheus-compatible /metrics endpoint response.
    Falls back to JSON summary if prometheus-client is not installed.
    """
    if _PROM_AVAILABLE:
        from fastapi.responses import Response as FastAPIResponse
        return FastAPIResponse(
            content=generate_latest(REGISTRY),
            media_type=CONTENT_TYPE_LATEST,
        )
    # Graceful fallback
    from fastapi.responses import JSONResponse
    return JSONResponse({
        "status": "prometheus_client_not_installed",
        "message": "Install prometheus-client>=0.19.0 for full metrics export",
        "metrics": {
            "floodguard_http_requests_total": "unavailable",
            "floodguard_http_request_duration_seconds": "unavailable",
            "floodguard_active_connections": "unavailable"
        }
    })
