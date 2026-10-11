"""
DORA Metrics Calculation Module.

Calculates the four key DevOps Research and Assessment (DORA) metrics:
1. Deployment Frequency (deploys per day)
2. Lead Time for Changes (hours between commit and successful run)
3. Change Failure Rate (percentage of failed runs)
4. Mean Time to Restore / MTTR (hours between incident failure and recovery)

All calculations handle missing fields, empty inputs, invalid types, and
incomplete timestamps safely without raising unexpected exceptions.
Unavailable metrics return None rather than misleading or fabricated values.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def _parse_timestamp(ts: Any) -> Optional[datetime]:
    """
    Safely parse an ISO-8601 timestamp string into a timezone-aware UTC datetime.
    Returns None if the timestamp is missing, invalid, or unparseable.
    """
    if not ts or not isinstance(ts, str):
        return None
    try:
        cleaned = ts.strip().replace("Z", "+00:00")
        dt = datetime.fromisoformat(cleaned)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


def deployment_frequency(runs: Optional[List[Dict[str, Any]]], days: int = 30) -> float:
    """
    Calculate Deployment Frequency as successful deployments per day.

    Assumptions & Units:
    - Unit: deployments / day (rounded to 2 decimal places).
    - Counts workflow runs where conclusion == 'success'.
    - Empty or non-list runs return 0.0.
    - `days` must be a positive number; raises ValueError if days <= 0 or invalid.
    """
    if days is None or not isinstance(days, (int, float)) or days <= 0:
        raise ValueError("days must be a positive number greater than 0")

    if not runs or not isinstance(runs, list):
        return 0.0

    ok = [
        r for r in runs
        if isinstance(r, dict) and r.get("conclusion") == "success"
    ]
    return round(len(ok) / days, 2)


def change_failure_rate(runs: Optional[List[Dict[str, Any]]]) -> float:
    """
    Calculate Change Failure Rate as the percentage of deployments that failed.

    Assumptions & Units:
    - Unit: percentage (0.0 to 100.0, rounded to 1 decimal place).
    - Counts runs with conclusion == 'failure' relative to total valid runs.
    - Empty input returns 0.0.
    """
    if not runs or not isinstance(runs, list):
        return 0.0

    valid_runs = [r for r in runs if isinstance(r, dict)]
    if not valid_runs:
        return 0.0

    failed = [r for r in valid_runs if r.get("conclusion") == "failure"]
    return round(100.0 * len(failed) / len(valid_runs), 1)


def lead_time_for_changes(runs: Optional[List[Dict[str, Any]]]) -> Optional[float]:
    """
    Calculate Lead Time for Changes as the average elapsed time between a commit
    and its successful deployment / workflow completion.

    Assumptions & Units:
    - Unit: hours (rounded to 2 decimal places).
    - Considers successful runs (conclusion == 'success').
    - Commit time is read from run['head_commit']['timestamp'] or run['head_commit_timestamp'].
    - Completion time is read from run['updated_at'] or run['created_at'].
    - If valid commit and completion timestamps are missing or chronological order is
      invalid (negative duration), that run is excluded.
    - If no runs have sufficient data, returns None (metric unavailable).
    """
    if not runs or not isinstance(runs, list):
        return None

    lead_times: List[float] = []

    for r in runs:
        if not isinstance(r, dict) or r.get("conclusion") != "success":
            continue

        commit_ts = None
        head_commit = r.get("head_commit")
        if isinstance(head_commit, dict):
            commit_ts = head_commit.get("timestamp")
        if not commit_ts:
            commit_ts = r.get("head_commit_timestamp")

        deploy_ts = r.get("updated_at") or r.get("created_at")

        commit_dt = _parse_timestamp(commit_ts)
        deploy_dt = _parse_timestamp(deploy_ts)

        if commit_dt and deploy_dt:
            duration_seconds = (deploy_dt - commit_dt).total_seconds()
            if duration_seconds >= 0:
                lead_times.append(duration_seconds / 3600.0)

    if not lead_times:
        return None

    return round(sum(lead_times) / len(lead_times), 2)


def mean_time_to_restore(runs: Optional[List[Dict[str, Any]]]) -> Optional[float]:
    """
    Calculate Mean Time to Restore (MTTR) as the average elapsed time from a
    failed deployment to the subsequent successful recovery deployment.

    Assumptions & Units:
    - Unit: hours (rounded to 2 decimal places).
    - Requires at least one failure followed chronologically by a success.
    - Runs are sorted chronologically by run start/creation timestamp.
    - Incident duration is calculated from the first failure in a streak until
      the next successful run.
    - Unresolved incidents (trailing failures without subsequent success) are not
      counted as completed recoveries.
    - If no completed recovery cycle exists or timestamps are missing, returns None.
    """
    if not runs or not isinstance(runs, list):
        return None

    # Filter dict runs with parseable timestamps and meaningful conclusions
    dated_runs = []
    for r in runs:
        if not isinstance(r, dict):
            continue
        conclusion = r.get("conclusion")
        if conclusion not in ("success", "failure"):
            continue

        ts = r.get("created_at") or r.get("run_started_at") or r.get("updated_at")
        dt = _parse_timestamp(ts)
        if dt:
            dated_runs.append((dt, conclusion, r))

    if not dated_runs:
        return None

    # Sort chronologically (oldest first)
    dated_runs.sort(key=lambda item: item[0])

    restore_durations: List[float] = []
    incident_start_dt: Optional[datetime] = None

    for dt, conclusion, _ in dated_runs:
        if conclusion == "failure":
            if incident_start_dt is None:
                # Mark the beginning of the downtime / failure incident
                incident_start_dt = dt
        elif conclusion == "success":
            if incident_start_dt is not None:
                # Recovery completed
                duration_hours = (dt - incident_start_dt).total_seconds() / 3600.0
                if duration_hours >= 0:
                    restore_durations.append(duration_hours)
                incident_start_dt = None

    if not restore_durations:
        return None

    return round(sum(restore_durations) / len(restore_durations), 2)


def calculate_dora_metrics(runs: Optional[List[Dict[str, Any]]], days: int = 30) -> Dict[str, Any]:
    """
    Aggregate all four DORA metrics into a single structured summary dictionary.
    """
    return {
        "deployment_frequency": deployment_frequency(runs, days=days),
        "lead_time_for_changes": lead_time_for_changes(runs),
        "change_failure_rate": change_failure_rate(runs),
        "mean_time_to_restore": mean_time_to_restore(runs),
        "total_runs": len(runs) if isinstance(runs, list) else 0,
        "calculation_days": days,
    }
