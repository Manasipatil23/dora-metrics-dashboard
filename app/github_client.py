"""
GitHub API Client for fetching GitHub Actions workflow runs.

Endpoint: https://api.github.com/repos/<owner>/<repo>/actions/runs
Reads repository configuration and authentication token from environment variables:
- GITHUB_REPOSITORY (formatted as 'owner/repo') or GITHUB_OWNER and GITHUB_REPO
- GITHUB_TOKEN (optional for public repositories, recommended for higher rate limits)

Safely handles network timeouts, authentication issues, rate limits, and missing configuration.
Never logs, exposes, or hardcodes credentials.
"""

import os
from typing import Any, Dict, List, Optional, Tuple
import requests


def get_repository_config(
    custom_owner: Optional[str] = None,
    custom_repo: Optional[str] = None,
) -> Tuple[Optional[str], Optional[str]]:
    """
    Resolve repository owner and name from arguments or environment variables.
    Supports GITHUB_REPOSITORY (owner/repo) or GITHUB_OWNER and GITHUB_REPO.
    """
    if custom_owner and custom_repo:
        return custom_owner.strip(), custom_repo.strip()

    repo_env = os.getenv("GITHUB_REPOSITORY", "").strip()
    if repo_env and "/" in repo_env:
        parts = repo_env.split("/", 1)
        return parts[0].strip(), parts[1].strip()

    owner = os.getenv("GITHUB_OWNER", "").strip() or None
    repo = os.getenv("GITHUB_REPO", "").strip() or None
    return owner, repo


def fetch_workflow_runs(
    owner: Optional[str] = None,
    repo: Optional[str] = None,
    token: Optional[str] = None,
    per_page: int = 30,
    timeout: int = 10,
) -> Dict[str, Any]:
    """
    Fetch workflow runs from GitHub Actions API.

    Returns a structured dictionary:
    {
        "configured": bool,
        "success": bool,
        "runs": list of dicts,
        "total_count": int,
        "status_code": int or None,
        "message": str,
        "error_type": str or None,
        "owner": str or None,
        "repo": str or None,
        "has_token": bool,
    }
    """
    resolved_owner, resolved_repo = get_repository_config(owner, repo)
    resolved_token = token if token is not None else os.getenv("GITHUB_TOKEN", "").strip()

    has_token = bool(resolved_token)

    # Validate repository configuration
    if not resolved_owner or not resolved_repo:
        return {
            "configured": False,
            "success": False,
            "runs": [],
            "total_count": 0,
            "status_code": None,
            "message": (
                "GitHub repository is not configured. Set GITHUB_REPOSITORY='owner/repo' "
                "or both GITHUB_OWNER and GITHUB_REPO in your environment."
            ),
            "error_type": "NOT_CONFIGURED",
            "owner": resolved_owner,
            "repo": resolved_repo,
            "has_token": has_token,
        }

    api_url = f"https://api.github.com/repos/{resolved_owner}/{resolved_repo}/actions/runs"

    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "dora-metrics-dashboard",
    }
    if resolved_token:
        headers["Authorization"] = f"Bearer {resolved_token}"

    params = {
        "per_page": min(max(1, per_page), 100),
    }

    try:
        response = requests.get(api_url, headers=headers, params=params, timeout=timeout)

        if response.status_code == 200:
            data = response.json()
            runs = data.get("workflow_runs", [])
            total_count = data.get("total_count", len(runs))
            return {
                "configured": True,
                "success": True,
                "runs": runs,
                "total_count": total_count,
                "status_code": 200,
                "message": f"Successfully retrieved {len(runs)} workflow run(s) from {resolved_owner}/{resolved_repo}.",
                "error_type": None,
                "owner": resolved_owner,
                "repo": resolved_repo,
                "has_token": has_token,
            }

        elif response.status_code == 401:
            return {
                "configured": True,
                "success": False,
                "runs": [],
                "total_count": 0,
                "status_code": 401,
                "message": "Authentication failed (HTTP 401). Verify that your GITHUB_TOKEN is valid.",
                "error_type": "AUTHENTICATION_FAILED",
                "owner": resolved_owner,
                "repo": resolved_repo,
                "has_token": has_token,
            }

        elif response.status_code == 403:
            # Check for API rate limiting
            rate_limit_remaining = response.headers.get("X-RateLimit-Remaining")
            if rate_limit_remaining == "0":
                msg = (
                    "GitHub API rate limit exceeded (HTTP 403). "
                    "Unauthenticated requests are limited to 60/hour. Provide a GITHUB_TOKEN to increase your limit to 5000/hour."
                )
                error_type = "RATE_LIMITED"
            else:
                msg = "Access forbidden (HTTP 403). The token may lack 'actions:read' permissions or repo access."
                error_type = "FORBIDDEN"

            return {
                "configured": True,
                "success": False,
                "runs": [],
                "total_count": 0,
                "status_code": 403,
                "message": msg,
                "error_type": error_type,
                "owner": resolved_owner,
                "repo": resolved_repo,
                "has_token": has_token,
            }

        elif response.status_code == 404:
            return {
                "configured": True,
                "success": False,
                "runs": [],
                "total_count": 0,
                "status_code": 404,
                "message": (
                    f"Repository '{resolved_owner}/{resolved_repo}' not found (HTTP 404). "
                    "Verify the repository name or ensure your token has access if it is private."
                ),
                "error_type": "NOT_FOUND",
                "owner": resolved_owner,
                "repo": resolved_repo,
                "has_token": has_token,
            }

        else:
            return {
                "configured": True,
                "success": False,
                "runs": [],
                "total_count": 0,
                "status_code": response.status_code,
                "message": f"GitHub API responded with HTTP {response.status_code}: {response.reason}",
                "error_type": "HTTP_ERROR",
                "owner": resolved_owner,
                "repo": resolved_repo,
                "has_token": has_token,
            }

    except requests.exceptions.Timeout:
        return {
            "configured": True,
            "success": False,
            "runs": [],
            "total_count": 0,
            "status_code": None,
            "message": f"Connection to GitHub API timed out after {timeout} seconds.",
            "error_type": "TIMEOUT",
            "owner": resolved_owner,
            "repo": resolved_repo,
            "has_token": has_token,
        }

    except requests.exceptions.ConnectionError:
        return {
            "configured": True,
            "success": False,
            "runs": [],
            "total_count": 0,
            "status_code": None,
            "message": "Network connection error while reaching api.github.com. Check your internet connection.",
            "error_type": "CONNECTION_ERROR",
            "owner": resolved_owner,
            "repo": resolved_repo,
            "has_token": has_token,
        }

    except requests.exceptions.RequestException as e:
        return {
            "configured": True,
            "success": False,
            "runs": [],
            "total_count": 0,
            "status_code": None,
            "message": f"Unexpected request failure: {type(e).__name__}",
            "error_type": "REQUEST_ERROR",
            "owner": resolved_owner,
            "repo": resolved_repo,
            "has_token": has_token,
        }
