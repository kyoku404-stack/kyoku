"""DevOps Integration Test Suite: Production Infrastructure, Container Orchestration & Deployment Automation.

Specification Source: devdocs/p1/p1.10.txt (Chapters 3, 4, 5, 8, 9, 10, 11, 12, 13, 14, 17, 18)
Architecture: docs/Architecture/deployment-ai-infrastructure.md & ADR-029, ADR-030, ADR-031
Role: Member 4 (DevOps & Integration Lead)
Phase: 1.10 — Deployment, Infrastructure & Production Readiness
"""

from __future__ import annotations

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class TestDockerComposeProductionTopology(unittest.TestCase):
    """Verifies production multi-container orchestration configuration and resource quotas."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.compose_path = REPO_ROOT / "docker-compose.prod.yml"
        cls.compose_content = cls.compose_path.read_text(encoding="utf-8")

    def test_docker_compose_prod_file_exists(self) -> None:
        """Ensures docker-compose.prod.yml exists in the repository root."""
        self.assertTrue(self.compose_path.is_file(), "docker-compose.prod.yml must exist")

    def test_required_production_services_defined(self) -> None:
        """Ensures all 9 core and observability services are declared in production compose."""
        expected_services = [
            "gateway:",
            "frontend:",
            "backend:",
            "postgres:",
            "redis:",
            "prometheus:",
            "grafana:",
            "loki:",
            "promtail:",
            "ai-worker:",
        ]
        for service in expected_services:
            self.assertIn(
                service,
                self.compose_content,
                f"Missing required production service: {service}",
            )

    def test_production_resource_limits_defined(self) -> None:
        """Ensures container CPU and memory resource quotas are defined for production stability."""
        self.assertIn("resources:", self.compose_content)
        self.assertIn("limits:", self.compose_content)

        # Check explicit CPU and memory bounds
        self.assertRegex(self.compose_content, r'cpus:\s*"(?:0\.50|1\.00|2\.00)"')
        self.assertRegex(self.compose_content, r"memory:\s*(?:256M|512M|1024M|2048M|4096M)")

    def test_persistent_volumes_and_networks(self) -> None:
        """Ensures persistent named volumes and keep-network bridge are declared."""
        expected_volumes = [
            "postgres_data:",
            "redis_data:",
            "storage_data:",
            "prometheus_data:",
            "grafana_data:",
            "loki_data:",
            "nginx_certs:",
            "ai_model_cache:",
        ]
        for vol in expected_volumes:
            self.assertIn(vol, self.compose_content, f"Missing persistent volume: {vol}")

        self.assertIn("keep-network:", self.compose_content)
        self.assertIn("driver: bridge", self.compose_content)

    def test_no_hardcoded_passwords_in_compose(self) -> None:
        """Verifies production secrets require runtime environment injection (:? validation)."""
        self.assertIn(
            "SECRET_KEY: ${SECRET_KEY:?",
            self.compose_content,
            "SECRET_KEY must enforce mandatory injection in production",
        )
        self.assertIn(
            "POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?",
            self.compose_content,
            "POSTGRES_PASSWORD must enforce mandatory injection in production",
        )


class TestNginxGatewayConfiguration(unittest.TestCase):
    """Verifies enterprise Nginx reverse proxy configuration, routing, and security headers."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.gateway_path = REPO_ROOT / "infrastructure" / "nginx" / "gateway.conf"
        cls.gateway_content = cls.gateway_path.read_text(encoding="utf-8")

    def test_nginx_gateway_conf_exists(self) -> None:
        """Ensures infrastructure/nginx/gateway.conf exists."""
        self.assertTrue(self.gateway_path.is_file(), "gateway.conf must exist")

    def test_nginx_tls_modern_protocols(self) -> None:
        """Ensures TLSv1.2 and TLSv1.3 are configured with session security."""
        self.assertIn("listen 443 ssl;", self.gateway_content)
        self.assertIn("ssl_protocols TLSv1.2 TLSv1.3;", self.gateway_content)
        self.assertIn("ssl_session_tickets off;", self.gateway_content)
        self.assertIn("ssl_session_cache shared:SSL:10m;", self.gateway_content)

    def test_nginx_security_headers(self) -> None:
        """Ensures enterprise defense-in-depth headers conforming to ADR-029 & API Contract Section 7.3."""
        expected_headers = [
            "Strict-Transport-Security",
            "X-Content-Type-Options \"nosniff\"",
            "X-Frame-Options \"DENY\"",
            "X-XSS-Protection \"1; mode=block\"",
            "Referrer-Policy \"strict-origin-when-cross-origin\"",
            "Permissions-Policy \"geolocation=(), camera=(), microphone=()\"",
            "Content-Security-Policy",
        ]
        for header in expected_headers:
            self.assertIn(header, self.gateway_content, f"Missing security header: {header}")

    def test_nginx_reverse_proxy_routes(self) -> None:
        """Ensures routing matrix covers /api/v1/, /health, /metrics, /assets/, and /."""
        self.assertIn("location = /health", self.gateway_content)
        self.assertIn("location /health/", self.gateway_content)
        self.assertIn("location /api/v1/", self.gateway_content)
        self.assertIn("location = /metrics", self.gateway_content)
        self.assertIn("location ~* ^/(assets|_next/static)/", self.gateway_content)
        self.assertIn("location /", self.gateway_content)

    def test_nginx_proxy_correlation_headers_injected(self) -> None:
        """Ensures proxy correlation headers (X-Real-IP, X-Forwarded-*, X-Request-ID) are forwarded."""
        self.assertIn("proxy_set_header X-Real-IP $remote_addr;", self.gateway_content)
        self.assertIn("proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;", self.gateway_content)
        self.assertIn("proxy_set_header X-Forwarded-Proto https;", self.gateway_content)
        self.assertIn("proxy_set_header X-Request-ID $request_id;", self.gateway_content)

    def test_nginx_sse_streaming_settings(self) -> None:
        """Ensures Server-Sent Events (SSE) buffering is disabled with extended timeouts."""
        self.assertIn("proxy_buffering off;", self.gateway_content)
        self.assertIn("proxy_read_timeout 300s;", self.gateway_content)
        self.assertIn("chunked_transfer_encoding off;", self.gateway_content)


class TestDeploymentAutomationScripts(unittest.TestCase):
    """Verifies automated deployment, backup, restore, and test orchestration bash scripts."""

    def test_prod_deploy_script_structure(self) -> None:
        """Verifies scripts/prod-deploy.sh contains health gating and automated rollback."""
        script_path = REPO_ROOT / "scripts" / "prod-deploy.sh"
        self.assertTrue(script_path.is_file(), "scripts/prod-deploy.sh must exist")
        content = script_path.read_text(encoding="utf-8")

        self.assertIn("set -euo pipefail", content)
        self.assertIn("alembic upgrade head", content)
        self.assertIn("docker compose -f", content)
        self.assertIn("MAX_HEALTH_ATTEMPTS=12", content)  # 60s SLA (12 * 5s)
        self.assertIn("status\":\"healthy\"", content)
        self.assertIn("down", content)  # Rollback trigger

    def test_prod_backup_script_structure(self) -> None:
        """Verifies scripts/prod-backup.sh handles pg_dump, storage archive, and SHA-256 manifests."""
        script_path = REPO_ROOT / "scripts" / "prod-backup.sh"
        self.assertTrue(script_path.is_file(), "scripts/prod-backup.sh must exist")
        content = script_path.read_text(encoding="utf-8")

        self.assertIn("pg_dump", content)
        self.assertIn("storage_volume.tar.gz", content)
        self.assertIn("sha256sum", content)
        self.assertIn("manifest.json", content)
        self.assertIn("mtime", content)  # Retention pruning

    def test_prod_restore_script_structure(self) -> None:
        """Verifies scripts/prod-restore.sh validates SHA-256 integrity before executing restore."""
        script_path = REPO_ROOT / "scripts" / "prod-restore.sh"
        self.assertTrue(script_path.is_file(), "scripts/prod-restore.sh must exist")
        content = script_path.read_text(encoding="utf-8")

        self.assertIn("sha256sum", content)
        self.assertIn("pg_restore", content)
        self.assertIn("manifest.json", content)
        self.assertIn("alembic check", content)

    def test_test_deployment_script_structure(self) -> None:
        """Verifies scripts/test-deployment.sh orchestrates deployment validation."""
        script_path = REPO_ROOT / "scripts" / "test-deployment.sh"
        self.assertTrue(script_path.is_file(), "scripts/test-deployment.sh must exist")
        content = script_path.read_text(encoding="utf-8")

        self.assertIn("test_production_deployment_infrastructure.py", content)
        self.assertIn("docker-compose.prod.yml", content)


class TestProductionEnvironmentVariables(unittest.TestCase):
    """Verifies production variables are declared in .env.example without hardcoded credentials."""

    def test_env_example_production_variables(self) -> None:
        """Ensures all Phase 1.10 production deployment settings exist in .env.example."""
        env_example_path = REPO_ROOT / ".env.example"
        self.assertTrue(env_example_path.is_file(), ".env.example must exist")
        content = env_example_path.read_text(encoding="utf-8")

        expected_vars = [
            "PRODUCTION_DOMAIN=",
            "NGINX_PORT_HTTP=",
            "NGINX_PORT_HTTPS=",
            "SSL_CERT_PATH=",
            "SSL_KEY_PATH=",
            "DB_POOL_SIZE=",
            "DB_MAX_OVERFLOW=",
            "ENABLE_OPENAPI_DOCS=",
        ]
        for var in expected_vars:
            self.assertIn(var, content, f"Missing production variable in .env.example: {var}")


class TestProductionDeploymentRunbook(unittest.TestCase):
    """Verifies the production deployment and operations manual documentation completeness."""

    def test_runbook_documentation_completeness(self) -> None:
        """Ensures production-deployment-runbook.md covers architecture, SSL, deployment, and DR."""
        runbook_path = REPO_ROOT / "docs" / "Deployment" / "production-deployment-runbook.md"
        self.assertTrue(runbook_path.is_file(), "production-deployment-runbook.md must exist")
        content = runbook_path.read_text(encoding="utf-8")

        self.assertIn("Production Architecture Overview", content)
        self.assertIn("Infrastructure Sizing & Container Resource Limits", content)
        self.assertIn("SSL/TLS Certificate Provisioning", content)
        self.assertIn("Automated Deployment Workflow", content)
        self.assertIn("Recovery Point Objective (RPO)", content)
        self.assertIn("< 1 hour", content)
        self.assertIn("Recovery Time Objective (RTO)", content)
        self.assertIn("< 15 minutes", content)


if __name__ == "__main__":
    unittest.main()
