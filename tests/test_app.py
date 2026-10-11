"""
Integration and UI tests for Flask application and GitHub API client.
"""

from unittest.mock import patch
import pytest
from app.main import create_app
from app.github_client import fetch_workflow_runs, get_repository_config


@pytest.fixture
def test_client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_github_client_unconfigured(monkeypatch):
    """When environment variables are missing, fetch_workflow_runs returns NOT_CONFIGURED."""
    monkeypatch.delenv("GITHUB_REPOSITORY", raising=False)
    monkeypatch.delenv("GITHUB_OWNER", raising=False)
    monkeypatch.delenv("GITHUB_REPO", raising=False)

    result = fetch_workflow_runs()
    assert result["configured"] is False
    assert result["success"] is False
    assert result["error_type"] == "NOT_CONFIGURED"
    assert "not configured" in result["message"]


def test_github_client_env_config(monkeypatch):
    """Test resolution of repository from GITHUB_REPOSITORY."""
    monkeypatch.setenv("GITHUB_REPOSITORY", "testuser/my-repo")
    owner, repo = get_repository_config()
    assert owner == "testuser"
    assert repo == "my-repo"


def test_flask_index_unconfigured(test_client, monkeypatch):
    """Dashboard should render gracefully when credentials are not configured."""
    monkeypatch.delenv("GITHUB_REPOSITORY", raising=False)
    monkeypatch.delenv("GITHUB_OWNER", raising=False)
    monkeypatch.delenv("GITHUB_REPO", raising=False)

    response = test_client.get("/")
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "Automated DevOps Delivery Intelligence and DORA Metrics Dashboard" in html
    assert "Repository Not Configured" in html
    assert "set GITHUB_REPOSITORY=" in html


def test_flask_index_with_mocked_runs(test_client):
    """Dashboard should render metrics and table with valid workflow data."""
    mock_runs = [
        {
            "id": 1001,
            "name": "CI Build",
            "event": "push",
            "status": "completed",
            "conclusion": "success",
            "head_sha": "abc1234567",
            "head_commit": {"id": "abc1234567", "timestamp": "2026-10-10T08:00:00Z"},
            "created_at": "2026-10-10T08:30:00Z",
            "updated_at": "2026-10-10T09:00:00Z",
            "html_url": "https://github.com/test/repo/actions/runs/1001",
        }
    ]

    mock_result = {
        "configured": True,
        "success": True,
        "runs": mock_runs,
        "total_count": 1,
        "status_code": 200,
        "message": "Loaded 1 run",
        "error_type": None,
        "owner": "test",
        "repo": "repo",
        "has_token": False,
    }

    with patch("app.main.fetch_workflow_runs", return_value=mock_result):
        response = test_client.get("/?days=10")
        assert response.status_code == 200
        html = response.data.decode("utf-8")
        assert "Live GitHub Actions Connected" in html
        assert "CI Build" in html
        assert "abc1234" in html
        assert "val-deployment-frequency" in html
