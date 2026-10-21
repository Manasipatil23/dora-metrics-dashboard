# Automated DevOps Delivery Intelligence and DORA Metrics Dashboard

A modular, production-ready DevOps intelligence dashboard designed to monitor and evaluate software delivery performance using the four Google Cloud DORA (DevOps Research and Assessment) metrics. The application connects directly to the GitHub Actions REST API to analyze continuous integration and delivery pipelines in real time.

---

## 🎯 Project Overview & Objectives

In modern DevOps engineering, tracking software delivery velocity and operational stability is crucial for high-performing engineering teams. The goal of this project is to build an automated delivery intelligence dashboard that:

1. Connects to the GitHub Actions API to retrieve CI/CD pipeline execution history.
2. Accurately calculates the four core DORA metrics.
3. Renders a clean, responsive, dark-themed web dashboard with Chart.js telemetry visuals.
4. Handles missing configuration, empty datasets, API rate limits, and network errors gracefully without crashing.
5. Provides a modular foundation verified by automated tests.

---

## 📊 The Four DORA Metrics Explained

| DORA Metric | Category | Definition | Measurement Unit in Dashboard |
| :--- | :--- | :--- | :--- |
| **Deployment Frequency** | Velocity / Speed | How often the organization successfully releases code to production or staging. | Successful runs per day (`deploys / day`) over an evaluation window (default: 30 days). |
| **Lead Time for Changes** | Velocity / Speed | The elapsed time from code commit creation until the change is successfully deployed. | Average elapsed time in hours (`hours`) between `head_commit.timestamp` and run completion. |
| **Change Failure Rate** | Stability / Quality | The percentage of deployments that result in a failure in the pipeline or production. | Percentage (`%`) of evaluated runs where conclusion is `failure`. |
| **Mean Time to Restore (MTTR)** | Stability / Quality | How long it takes to recover from an incident or pipeline failure to a healthy state. | Average elapsed time in hours (`hours`) from the start of a failure incident to the next successful recovery run. |

---

## 🏗️ Project Structure

```text
dora-metrics-dashboard/
├── app/
│   ├── __init__.py           # Application package initializer
│   ├── main.py               # Flask application routes, factory, and telemetry data assembly
│   ├── github_client.py      # Resilient GitHub Actions API client with error handling
│   ├── metrics.py            # DORA metric calculation algorithms and data sanitization
│   └── templates/
│       └── index.html        # Responsive dashboard UI with Chart.js visualization
├── tests/
│   ├── __init__.py           # Test package initializer
│   ├── test_metrics.py       # Comprehensive unit tests for all 4 DORA metrics
│   └── test_app.py           # Integration tests for Flask endpoints and GitHub client
├── requirements.txt          # Python dependencies
├── .gitignore                # Git ignore rules for Python, virtual environments, and secrets
└── README.md                 # Project documentation and setup guide
```

---

## 🛠️ Technologies Used

- **Python 3.13**: Modern, robust programming language used for the backend logic and data calculations.
- **Flask**: Lightweight, beginner-friendly Python web framework for rendering the dashboard and handling HTTP routes.
- **Requests**: Reliable HTTP library used for querying the GitHub Actions REST API with timeouts and error handling.
- **Pytest**: Standard testing framework used for writing unit and integration tests.
- **Chart.js (via CDN)**: Open-source JavaScript data visualization library for rendering execution distribution charts.
- **Gunicorn**: High-performance WSGI HTTP server included for production container deployment in future milestones.

---

## 💻 Installation & Local Execution

This project is configured to run locally on Windows without requiring Docker.

### 1. Prerequisites
- Windows 10/11
- Git
- Python 3.13 installed and available on your PATH

### 2. Set Up a Virtual Environment
Open **Command Prompt** (`cmd.exe`) in the project directory:

```cmd
cd dora-metrics-dashboard
python -m venv .venv
.venv\Scripts\activate
```

*(If using PowerShell, activate using `.\.venv\Scripts\Activate.ps1`)*

### 3. Install Dependencies
```cmd
python -m pip install -r requirements.txt
```

### 4. Configure GitHub Environment Variables (Optional for Public Repos)
To connect to your GitHub repository and avoid API rate limits, set your repository and personal access token in your terminal session:

**In Windows Command Prompt (`cmd.exe`):**
```cmd
set GITHUB_REPOSITORY=Manasipatil23/dora-metrics-dashboard
set GITHUB_TOKEN=your_personal_access_token_here
```

**In Windows PowerShell:**
```powershell
$env:GITHUB_REPOSITORY="Manasipatil23/dora-metrics-dashboard"
$env:GITHUB_TOKEN="your_personal_access_token_here"
```

> **Security Note:** Never commit personal access tokens or `.env` files into source control. The dashboard securely passes tokens via HTTPS request headers and never prints or displays tokens in web templates or logs.

### 5. Run the Application
Start the Flask development server:

```cmd
python -m flask --app app.main run
```

Open your browser and navigate to:
```text
http://127.0.0.1:5000
```

---

## 🧪 Running Automated Tests

All DORA metric calculations and Flask routes are verified using unit tests. To run the automated test suite:

```cmd
python -m pytest -v
```

Expected output:
```text
tests/test_app.py::test_github_client_unconfigured PASSED
tests/test_app.py::test_github_client_env_config PASSED
tests/test_app.py::test_flask_index_unconfigured PASSED
tests/test_app.py::test_flask_index_with_mocked_runs PASSED
tests/test_metrics.py::test_frequency PASSED
tests/test_metrics.py::test_deployment_frequency_empty_and_none PASSED
tests/test_metrics.py::test_deployment_frequency_various_counts PASSED
tests/test_metrics.py::test_deployment_frequency_invalid_days PASSED
tests/test_metrics.py::test_deployment_frequency_malformed_entries PASSED
tests/test_metrics.py::test_change_failure_rate_mixed PASSED
tests/test_metrics.py::test_change_failure_rate_all_success_and_all_failure PASSED
tests/test_metrics.py::test_change_failure_rate_empty_and_malformed PASSED
tests/test_metrics.py::test_lead_time_single_run PASSED
tests/test_metrics.py::test_lead_time_average_multiple_runs PASSED
tests/test_metrics.py::test_lead_time_unavailable_cases PASSED
tests/test_metrics.py::test_mttr_single_recovery_cycle PASSED
tests/test_metrics.py::test_mttr_failure_streak_before_recovery PASSED
tests/test_metrics.py::test_mttr_multiple_incidents PASSED
tests/test_metrics.py::test_mttr_out_of_order_runs PASSED
tests/test_metrics.py::test_mttr_unavailable_cases PASSED
tests/test_metrics.py::test_calculate_dora_metrics_aggregation PASSED
============================= 21 passed in 0.98s ==============================
```

---

## 📐 Assumptions & Known Limitations

1. **Lead Time for Changes**:
   - Assumes that the `head_commit.timestamp` reflects the commit author time and `updated_at` reflects the deployment completion time.
   - If commit timestamps or completion timestamps are not provided by GitHub API payloads, the metric is displayed as **Unavailable** rather than presenting inaccurate data.
2. **Mean Time to Restore (MTTR)**:
   - Evaluates consecutive pipeline runs ordered chronologically. A downtime incident begins at the first failing run and is considered restored at the next successful run.
   - If no failure-to-success recovery cycles exist in the workflow history, the metric is displayed as **Unavailable**.
3. **API Rate Limiting**:
   - Unauthenticated requests to the GitHub REST API are limited to 60 requests per hour per IP. Providing a `GITHUB_TOKEN` increases the limit to 5,000 requests per hour.

---

## 📋 Current Implementation Status & Roadmap

- [x] **Step 1: Git Workflow and Version Control** (Created `dev` branch, milestone commits)
- [x] **Step 2: Project Architecture and Dependencies** (`app/`, `tests/`, `requirements.txt`, `.gitignore`)
- [x] **Step 3: Python Application & Dashboard** (DORA metric algorithms, GitHub API client, Flask web interface, Chart.js)
- [x] **Step 4: Automated Testing** (Pytest suite with 21 unit & integration tests)
- [ ] **Step 5: Docker Containerization** *(Pending later milestone)*
- [ ] **Step 6: CI/CD Pipeline Automation** *(Pending later milestone)*
- [ ] **Step 7: Production Cloud Deployment** *(Pending later milestone)*
