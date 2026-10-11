"""
Unit Tests for DORA Metrics Calculations.

Tests all four DORA metrics using controlled synthetic test data:
1. Deployment Frequency
2. Change Failure Rate
3. Lead Time for Changes
4. Mean Time to Restore (MTTR)

NOTE: All test data dictionaries in this file are synthetic test fixtures
and do not represent actual live production workflow history.
"""

import pytest
from app.metrics import (
    calculate_dora_metrics,
    change_failure_rate,
    deployment_frequency,
    lead_time_for_changes,
    mean_time_to_restore,
)


# ---------------------------------------------------------------------------
# Starter Test from Project Guide
# ---------------------------------------------------------------------------

def test_frequency():
    """Starter test from project guide verifying deployment frequency."""
    runs = [{"conclusion": "success"}] * 3
    assert deployment_frequency(runs, days=3) == 1.0


# ---------------------------------------------------------------------------
# Deployment Frequency Tests
# ---------------------------------------------------------------------------

def test_deployment_frequency_empty_and_none():
    """Empty or None runs should return 0.0 deployments per day."""
    assert deployment_frequency([]) == 0.0
    assert deployment_frequency(None) == 0.0
    assert deployment_frequency("not-a-list") == 0.0


def test_deployment_frequency_various_counts():
    """Verify rate calculations over custom day intervals."""
    synthetic_runs = [
        {"conclusion": "success"},
        {"conclusion": "failure"},
        {"conclusion": "success"},
        {"conclusion": "cancelled"},
        {"conclusion": "success"},
    ]
    # 3 successes over 10 days = 0.3 deploys/day
    assert deployment_frequency(synthetic_runs, days=10) == 0.3
    # 3 successes over 30 days = 0.1 deploys/day
    assert deployment_frequency(synthetic_runs, days=30) == 0.1


def test_deployment_frequency_invalid_days():
    """Invalid day counts should raise ValueError."""
    synthetic_runs = [{"conclusion": "success"}]
    with pytest.raises(ValueError):
        deployment_frequency(synthetic_runs, days=0)

    with pytest.raises(ValueError):
        deployment_frequency(synthetic_runs, days=-5)

    with pytest.raises(ValueError):
        deployment_frequency(synthetic_runs, days=None)

    with pytest.raises(ValueError):
        deployment_frequency(synthetic_runs, days="invalid")


def test_deployment_frequency_malformed_entries():
    """Malformed list items and missing conclusion keys should not crash."""
    malformed_runs = [
        {"wrong_key": "success"},
        {},
        None,
        "string_entry",
        123,
        {"conclusion": "success"},
    ]
    assert deployment_frequency(malformed_runs, days=1) == 1.0


# ---------------------------------------------------------------------------
# Change Failure Rate Tests
# ---------------------------------------------------------------------------

def test_change_failure_rate_mixed():
    """Verify percentage calculation with mixed outcomes."""
    synthetic_runs = [
        {"conclusion": "success"},
        {"conclusion": "failure"},
        {"conclusion": "success"},
    ]
    # 1 failure out of 3 runs = 33.3%
    assert change_failure_rate(synthetic_runs) == 33.3


def test_change_failure_rate_all_success_and_all_failure():
    """Verify 0% on all-success and 100% on all-failure."""
    all_success = [{"conclusion": "success"}] * 4
    assert change_failure_rate(all_success) == 0.0

    all_failure = [{"conclusion": "failure"}] * 4
    assert change_failure_rate(all_failure) == 100.0


def test_change_failure_rate_empty_and_malformed():
    """Empty, None, or malformed inputs should safely return 0.0."""
    assert change_failure_rate([]) == 0.0
    assert change_failure_rate(None) == 0.0
    assert change_failure_rate("invalid") == 0.0
    assert change_failure_rate([None, "bad"]) == 0.0


# ---------------------------------------------------------------------------
# Lead Time for Changes Tests
# ---------------------------------------------------------------------------

def test_lead_time_single_run():
    """Verify elapsed hours between commit and deployment."""
    synthetic_runs = [
        {
            "conclusion": "success",
            "head_commit": {"timestamp": "2026-10-10T10:00:00Z"},
            "updated_at": "2026-10-10T12:30:00Z",  # 2.5 hours later
        }
    ]
    assert lead_time_for_changes(synthetic_runs) == 2.5


def test_lead_time_average_multiple_runs():
    """Verify average lead time calculation across multiple runs."""
    synthetic_runs = [
        {
            "conclusion": "success",
            "head_commit": {"timestamp": "2026-10-10T08:00:00Z"},
            "updated_at": "2026-10-10T09:00:00Z",  # 1.0 hour
        },
        {
            "conclusion": "success",
            "head_commit_timestamp": "2026-10-10T12:00:00Z",
            "updated_at": "2026-10-10T15:00:00Z",  # 3.0 hours
        },
        {
            "conclusion": "failure",  # Should be ignored for lead time
            "head_commit": {"timestamp": "2026-10-10T10:00:00Z"},
            "updated_at": "2026-10-10T11:00:00Z",
        },
    ]
    # Average of 1.0 and 3.0 = 2.0 hours
    assert lead_time_for_changes(synthetic_runs) == 2.0


def test_lead_time_unavailable_cases():
    """Lead time must return None when sufficient data is not available."""
    assert lead_time_for_changes([]) is None
    assert lead_time_for_changes(None) is None

    # Missing timestamps
    missing_timestamps = [{"conclusion": "success"}]
    assert lead_time_for_changes(missing_timestamps) is None

    # Incomplete commit timestamp
    incomplete = [{"conclusion": "success", "updated_at": "2026-10-10T12:00:00Z"}]
    assert lead_time_for_changes(incomplete) is None

    # Invalid timestamp format
    invalid_format = [
        {
            "conclusion": "success",
            "head_commit": {"timestamp": "not-a-timestamp"},
            "updated_at": "invalid",
        }
    ]
    assert lead_time_for_changes(invalid_format) is None

    # Negative duration (clock mismatch or bad data)
    negative_duration = [
        {
            "conclusion": "success",
            "head_commit": {"timestamp": "2026-10-10T15:00:00Z"},
            "updated_at": "2026-10-10T10:00:00Z",
        }
    ]
    assert lead_time_for_changes(negative_duration) is None


# ---------------------------------------------------------------------------
# Mean Time to Restore (MTTR) Tests
# ---------------------------------------------------------------------------

def test_mttr_single_recovery_cycle():
    """Verify recovery duration from a failure to subsequent success."""
    synthetic_runs = [
        {"conclusion": "failure", "created_at": "2026-10-10T08:00:00Z"},
        {"conclusion": "success", "created_at": "2026-10-10T10:30:00Z"},  # 2.5 hours to restore
    ]
    assert mean_time_to_restore(synthetic_runs) == 2.5


def test_mttr_failure_streak_before_recovery():
    """Streak of failures should measure downtime from the initial failure to success."""
    synthetic_runs = [
        {"conclusion": "failure", "created_at": "2026-10-10T08:00:00Z"},
        {"conclusion": "failure", "created_at": "2026-10-10T09:00:00Z"},
        {"conclusion": "success", "created_at": "2026-10-10T11:00:00Z"},  # 3.0 hours from first failure
    ]
    assert mean_time_to_restore(synthetic_runs) == 3.0


def test_mttr_multiple_incidents():
    """Verify MTTR correctly averages across multiple recovery cycles."""
    synthetic_runs = [
        # Incident 1: 1.0 hour downtime
        {"conclusion": "failure", "created_at": "2026-10-10T08:00:00Z"},
        {"conclusion": "success", "created_at": "2026-10-10T09:00:00Z"},
        # Incident 2: 3.0 hours downtime
        {"conclusion": "failure", "created_at": "2026-10-11T12:00:00Z"},
        {"conclusion": "success", "created_at": "2026-10-11T15:00:00Z"},
    ]
    # Average of 1.0 and 3.0 = 2.0 hours
    assert mean_time_to_restore(synthetic_runs) == 2.0


def test_mttr_out_of_order_runs():
    """Ensure runs are sorted chronologically before computing MTTR."""
    # Reverse chronological (newest first, as GitHub API often returns)
    synthetic_runs = [
        {"conclusion": "success", "created_at": "2026-10-10T11:00:00Z"},
        {"conclusion": "failure", "created_at": "2026-10-10T09:00:00Z"},
    ]
    assert mean_time_to_restore(synthetic_runs) == 2.0


def test_mttr_unavailable_cases():
    """MTTR must return None when no recovery cycles exist in data."""
    assert mean_time_to_restore([]) is None
    assert mean_time_to_restore(None) is None

    # All successes (no incident to restore)
    all_successes = [
        {"conclusion": "success", "created_at": "2026-10-10T08:00:00Z"},
        {"conclusion": "success", "created_at": "2026-10-10T09:00:00Z"},
    ]
    assert mean_time_to_restore(all_successes) is None

    # Unresolved incident (failure with no following success)
    unresolved = [
        {"conclusion": "success", "created_at": "2026-10-10T08:00:00Z"},
        {"conclusion": "failure", "created_at": "2026-10-10T09:00:00Z"},
    ]
    assert mean_time_to_restore(unresolved) is None

    # Missing timestamps
    missing_timestamps = [
        {"conclusion": "failure"},
        {"conclusion": "success"},
    ]
    assert mean_time_to_restore(missing_timestamps) is None


# ---------------------------------------------------------------------------
# Aggregated DORA Metrics Function
# ---------------------------------------------------------------------------

def test_calculate_dora_metrics_aggregation():
    """Verify overall dictionary aggregation of all four metrics."""
    synthetic_runs = [
        {
            "conclusion": "failure",
            "created_at": "2026-10-10T08:00:00Z",
            "updated_at": "2026-10-10T08:15:00Z",
        },
        {
            "conclusion": "success",
            "created_at": "2026-10-10T10:00:00Z",
            "updated_at": "2026-10-10T10:30:00Z",
            "head_commit": {"timestamp": "2026-10-10T09:30:00Z"},  # 1.0 hr lead time
        },
    ]

    metrics = calculate_dora_metrics(synthetic_runs, days=2)

    assert metrics["deployment_frequency"] == 0.5  # 1 success / 2 days
    assert metrics["change_failure_rate"] == 50.0  # 1 failure / 2 total
    assert metrics["lead_time_for_changes"] == 1.0  # 1.0 hour
    assert metrics["mean_time_to_restore"] == 2.0  # 8:00 to 10:00 = 2.0 hours
    assert metrics["total_runs"] == 2
    assert metrics["calculation_days"] == 2
