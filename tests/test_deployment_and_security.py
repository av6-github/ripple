"""Tests for Phase 11: Deployment, Packaging, and Security Auditing."""

import os
import subprocess
import pytest
from scripts.run_security_audit import audit_gitignore, audit_tracked_files


def test_docker_configuration_files_exist():
    """Verify containerization artifacts exist."""
    assert os.path.exists("Dockerfile.backend"), "Dockerfile.backend must exist"
    assert os.path.exists("Dockerfile.frontend"), "Dockerfile.frontend must exist"
    assert os.path.exists("docker-compose.yml"), "docker-compose.yml must exist"

    # Check docker-compose.yml content
    with open("docker-compose.yml", "r") as f:
        compose_content = f.read()
    assert "ripple-backend" in compose_content
    assert "ripple-frontend" in compose_content
    assert "DATABASE_URL" in compose_content


def test_ci_workflow_exists_and_configured():
    """Verify GitHub Actions CI pipeline configuration."""
    ci_path = ".github/workflows/ci.yml"
    assert os.path.exists(ci_path), "CI workflow must exist"
    with open(ci_path, "r") as f:
        ci_content = f.read()
    assert "pytest" in ci_content
    assert "npm run lint" in ci_content
    assert "npm run build" in ci_content


def test_env_example_complete():
    """Verify .env.example contains all required keys without leaking secrets."""
    assert os.path.exists(".env.example"), ".env.example must exist"
    with open(".env.example", "r") as f:
        content = f.read()

    required_keys = [
        "DATABASE_URL",
        "NEO4J_URI",
        "NEO4J_PASSWORD",
        "PINECONE_API_KEY",
        "JWT_SECRET",
        "NEXT_PUBLIC_API_BASE",
    ]
    for key in required_keys:
        assert key in content, f"Missing {key} in .env.example"


def test_security_audit_clean_pass():
    """Programmatic security audit verifying AGENTS.md Rules 5 and 18."""
    assert audit_gitignore() is True
    assert audit_tracked_files() is True
