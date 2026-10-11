"""
Flask Web Application for DORA Metrics Dashboard.

Provides the web interface for viewing DORA delivery intelligence metrics
and GitHub Actions workflow runs.
"""

import os
from flask import Flask, render_template, request
from app.github_client import fetch_workflow_runs
from app.metrics import calculate_dora_metrics


def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)

    @app.route("/")
    def index():
        # Allow querying custom days window (defaults to 30)
        days_param = request.args.get("days", "30")
        try:
            days = int(days_param)
            if days <= 0:
                days = 30
        except ValueError:
            days = 30

        # Optional repository override via query parameters (useful for testing or switching repos)
        owner_override = request.args.get("owner")
        repo_override = request.args.get("repo")

        # 1. Fetch workflow runs from GitHub API
        api_result = fetch_workflow_runs(
            owner=owner_override,
            repo=repo_override,
        )

        runs = api_result.get("runs", [])

        # 2. Compute DORA metrics safely
        if api_result["success"] and runs:
            metrics = calculate_dora_metrics(runs, days=days)
        else:
            # When API is not configured or returned no data, metrics are unavailable or default
            metrics = {
                "deployment_frequency": 0.0 if api_result["success"] else None,
                "lead_time_for_changes": None,
                "change_failure_rate": 0.0 if api_result["success"] else None,
                "mean_time_to_restore": None,
                "total_runs": 0,
                "calculation_days": days,
            }

        # 3. Chart data for Chart.js
        success_count = sum(1 for r in runs if isinstance(r, dict) and r.get("conclusion") == "success")
        failure_count = sum(1 for r in runs if isinstance(r, dict) and r.get("conclusion") == "failure")
        other_count = len(runs) - (success_count + failure_count)

        chart_data = {
            "success": success_count,
            "failure": failure_count,
            "other": max(0, other_count),
            "total": len(runs),
        }

        # 4. Render dashboard template
        return render_template(
            "index.html",
            api_result=api_result,
            metrics=metrics,
            runs=runs[:25],  # Display up to 25 latest runs in the table
            chart_data=chart_data,
            days=days,
        )

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="127.0.0.1", port=port, debug=True)
