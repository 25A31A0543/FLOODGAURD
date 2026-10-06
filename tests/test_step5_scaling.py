"""
FloodGuard Step 5: Integration & Scaling — Test Suite
Tests for deployment health, metrics, regions, CI/CD, and infrastructure.

Run: python -m pytest tests/test_step5_scaling.py -v
"""
import json
from pathlib import Path
from fastapi.testclient import TestClient

from floodguard.main import app

client = TestClient(app)

# ---------------------------------------------------------------------------
# 1. Scaling Health Endpoint
# ---------------------------------------------------------------------------

def test_scaling_health_endpoint():
    """GET /api/v1/scaling/health returns 200 and overall_status."""
    resp = client.get("/api/v1/scaling/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "overall_status" in data
    assert data["overall_status"] in ("healthy", "degraded", "critical")


def test_scaling_health_has_regions():
    """Scaling health response includes multi-region deployment info."""
    resp = client.get("/api/v1/scaling/health")
    data = resp.json()
    assert "regions" in data
    regions = data["regions"]
    assert isinstance(regions, list)
    assert len(regions) >= 1
    # Each region should have required fields
    for region in regions:
        assert "region" in region
        assert "status" in region
        assert "pods_running" in region


def test_scaling_health_has_kubernetes_info():
    """Scaling health response includes Kubernetes cluster info."""
    resp = client.get("/api/v1/scaling/health")
    data = resp.json()
    assert "kubernetes" in data
    k8s = data["kubernetes"]
    assert "total_pods" in k8s
    assert "running_pods" in k8s
    assert "services" in k8s


def test_scaling_health_has_load_balancers():
    """Scaling health response includes load balancer status."""
    resp = client.get("/api/v1/scaling/health")
    data = resp.json()
    assert "load_balancers" in data
    lbs = data["load_balancers"]
    assert isinstance(lbs, list)
    assert len(lbs) >= 1


# ---------------------------------------------------------------------------
# 2. Scaling Metrics Endpoint
# ---------------------------------------------------------------------------

def test_scaling_metrics_endpoint():
    """GET /api/v1/scaling/metrics returns 200 with metrics payload."""
    resp = client.get("/api/v1/scaling/metrics")
    assert resp.status_code == 200
    data = resp.json()
    assert "current_metrics" in data


def test_scaling_metrics_contains_platform_kpis():
    """Metrics endpoint includes FloodGuard-specific KPI fields."""
    resp = client.get("/api/v1/scaling/metrics")
    data = resp.json()
    metrics = data["current_metrics"]
    assert "floodguard_http_requests_total" in metrics
    assert "floodguard_active_connections" in metrics
    assert "floodguard_alerts_dispatched_total" in metrics
    assert "floodguard_inundation_iou_score" in metrics


def test_scaling_metrics_iou_in_range():
    """Inundation IoU score should be in valid [0,1] range."""
    resp = client.get("/api/v1/scaling/metrics")
    data = resp.json()
    iou = data["current_metrics"]["floodguard_inundation_iou_score"]
    assert 0.0 <= float(iou) <= 1.0


# ---------------------------------------------------------------------------
# 3. Regions Endpoint
# ---------------------------------------------------------------------------

def test_scaling_regions_endpoint():
    """GET /api/v1/scaling/regions returns 200 with deployment regions."""
    resp = client.get("/api/v1/scaling/regions")
    assert resp.status_code == 200
    data = resp.json()
    assert "deployment_regions" in data


def test_scaling_regions_global_summary():
    """Regions endpoint includes global coverage summary."""
    resp = client.get("/api/v1/scaling/regions")
    data = resp.json()
    assert "global_summary" in data
    summary = data["global_summary"]
    assert "total_regions" in summary
    assert "total_population_covered" in summary
    assert summary["total_population_covered"] > 0


def test_scaling_regions_india_present():
    """India deployment region should be present in the regions list."""
    resp = client.get("/api/v1/scaling/regions")
    data = resp.json()
    regions = data["deployment_regions"]
    india_regions = [r for r in regions if "India" in r.get("name", "")]
    assert len(india_regions) >= 1


def test_scaling_regions_mahanadi_catchment():
    """Mahanadi-Hirakud catchment should be assigned to the India region."""
    resp = client.get("/api/v1/scaling/regions")
    data = resp.json()
    regions = data["deployment_regions"]
    india = next((r for r in regions if "India" in r.get("name", "")), None)
    assert india is not None
    assert "Mahanadi-Hirakud" in india.get("catchment_basins", [])


# ---------------------------------------------------------------------------
# 4. CI/CD Status Endpoint
# ---------------------------------------------------------------------------

def test_scaling_cicd_status_endpoint():
    """GET /api/v1/scaling/cicd-status returns 200 with pipeline info."""
    resp = client.get("/api/v1/scaling/cicd-status")
    assert resp.status_code == 200
    data = resp.json()
    assert "pipelines" in data


def test_scaling_cicd_has_main_pipeline():
    """CI/CD status should include the main ci.yml workflow."""
    resp = client.get("/api/v1/scaling/cicd-status")
    data = resp.json()
    pipelines = data["pipelines"]
    ci_pipeline = next((p for p in pipelines if p.get("workflow") == "ci.yml"), None)
    assert ci_pipeline is not None
    assert ci_pipeline["status"] == "success"
    assert ci_pipeline["tests_passed"] >= 77


def test_scaling_cicd_docker_registry():
    """CI/CD status includes Docker image registry info."""
    resp = client.get("/api/v1/scaling/cicd-status")
    data = resp.json()
    assert "docker_registry" in data
    registry = data["docker_registry"]
    assert "registry" in registry
    assert "images" in registry


def test_scaling_cicd_kubernetes_rollout():
    """CI/CD status includes Kubernetes rolling update configuration."""
    resp = client.get("/api/v1/scaling/cicd-status")
    data = resp.json()
    assert "kubernetes_rollout" in data
    rollout = data["kubernetes_rollout"]
    assert rollout["strategy"] == "RollingUpdate"


# ---------------------------------------------------------------------------
# 5. Infrastructure File Existence Tests
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).parent.parent


def test_docker_config_exists():
    """Dockerfile should exist in docker/ directory."""
    assert (PROJECT_ROOT / "docker" / "Dockerfile").exists()


def test_docker_compose_exists():
    """docker-compose.yml should exist in docker/ directory."""
    assert (PROJECT_ROOT / "docker" / "docker-compose.yml").exists()


def test_k8s_deployment_exists():
    """Kubernetes deployment.yaml should exist in k8s/ directory."""
    assert (PROJECT_ROOT / "k8s" / "deployment.yaml").exists()


def test_k8s_service_exists():
    """Kubernetes service.yaml should exist in k8s/ directory."""
    assert (PROJECT_ROOT / "k8s" / "service.yaml").exists()


def test_k8s_hpa_exists():
    """Kubernetes hpa.yaml should exist in k8s/ directory."""
    assert (PROJECT_ROOT / "k8s" / "hpa.yaml").exists()


def test_k8s_configmap_exists():
    """Kubernetes configmap.yaml should exist in k8s/ directory."""
    assert (PROJECT_ROOT / "k8s" / "configmap.yaml").exists()


def test_k8s_ingress_exists():
    """Kubernetes ingress.yaml should exist in k8s/ directory."""
    assert (PROJECT_ROOT / "k8s" / "ingress.yaml").exists()


def test_github_actions_workflow_exists():
    """GitHub Actions CI/CD workflow ci.yml should exist."""
    assert (PROJECT_ROOT / ".github" / "workflows" / "ci.yml").exists()


def test_monitoring_prometheus_exists():
    """Prometheus scrape config should exist in monitoring/ directory."""
    assert (PROJECT_ROOT / "monitoring" / "prometheus.yml").exists()


def test_monitoring_grafana_dashboard_exists():
    """Grafana dashboard JSON should exist in monitoring/ directory."""
    assert (PROJECT_ROOT / "monitoring" / "grafana_dashboard.json").exists()


def test_grafana_dashboard_valid_json():
    """Grafana dashboard JSON should be valid parseable JSON."""
    path = PROJECT_ROOT / "monitoring" / "grafana_dashboard.json"
    assert path.exists()
    content = path.read_text(encoding="utf-8-sig")  # utf-8-sig strips BOM if present
    dashboard = json.loads(content)
    assert "panels" in dashboard
    assert "title" in dashboard
    assert "FloodGuard" in dashboard["title"]


def test_middleware_metrics_module_exists():
    """Prometheus metrics middleware module should exist."""
    assert (PROJECT_ROOT / "floodguard" / "middleware" / "metrics.py").exists()


def test_middleware_auth_module_exists():
    """JWT auth middleware module should exist."""
    assert (PROJECT_ROOT / "floodguard" / "middleware" / "auth.py").exists()


# ---------------------------------------------------------------------------
# 6. Prometheus Metrics Endpoint
# ---------------------------------------------------------------------------

def test_prometheus_metrics_endpoint_exists():
    """GET /metrics endpoint should return 200."""
    resp = client.get("/metrics")
    assert resp.status_code == 200


def test_metrics_endpoint_content_type():
    """GET /metrics should return prometheus text or JSON content."""
    resp = client.get("/metrics")
    content_type = resp.headers.get("content-type", "")
    # Accept either Prometheus text/plain or JSON fallback
    assert "text/plain" in content_type or "application/json" in content_type


# ---------------------------------------------------------------------------
# 7. Full Platform Health Integration Test
# ---------------------------------------------------------------------------

def test_full_platform_health_all_steps():
    """Full platform integration — all 5 steps respond correctly."""
    # Step 1: Ingestion
    r1 = client.get("/api/v1/status")
    assert r1.status_code == 200

    # Step 2: Forecast
    r2 = client.get("/api/v1/forecast/status")
    assert r2.status_code == 200

    # Step 3: Alerts
    r3 = client.get("/api/v1/alerts/latest")
    assert r3.status_code == 200

    # Step 4: Dashboard
    r4 = client.get("/api/v1/authority/system-status")
    assert r4.status_code == 200

    # Step 5: Scaling
    r5 = client.get("/api/v1/scaling/health")
    assert r5.status_code == 200


def test_scaling_platform_label():
    """All Step 5 endpoints should include FloodGuard platform label."""
    endpoints = [
        "/api/v1/scaling/health",
        "/api/v1/scaling/metrics",
        "/api/v1/scaling/regions",
        "/api/v1/scaling/cicd-status",
    ]
    for endpoint in endpoints:
        resp = client.get(endpoint)
        assert resp.status_code == 200, f"Failed: {endpoint}"
        data = resp.json()
        assert "platform" in data, f"Missing 'platform' key in {endpoint}"
        assert "FloodGuard" in data["platform"]
