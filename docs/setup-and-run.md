# Setup and run

Covers running NexusQA locally through Docker Compose, and how the CI
pipeline mirrors those same steps so a passing local run and a passing
CI run mean the same thing.

## Prerequisites

- Docker Desktop (or Docker Engine + Compose plugin on Linux)
- Python 3.14+
- Git

## 1. Clone and configure environment variables

    git clone https://github.com/OlamiDiPupo-001/NexusQA.git
    cd NexusQA
    cp .env.example .env

Open `.env` and set a value for `NEXUSQA_WEBHOOK_SECRET`. Any string
works locally — it only needs to match between the backend and whatever
is signing webhooks against it (your test suite, in this case). Never
commit `.env`; it's already in `.gitignore`.

## 2. Start the stack

    docker compose up --build -d

This builds and starts three containers: `db` (Postgres), `backend`
(FastAPI), and `webhook_simulator`. Compose waits for Postgres to report
healthy before starting the backend, so a normal startup takes a few
seconds longer than the containers merely appearing in `docker ps`.

Check status:

    docker compose ps

All three should show as running, `db` as healthy.

## 3. Verify it's actually working

    curl -X POST http://localhost:8000/cart/items \
      -H "Content-Type: application/json" \
      -d '{"session_id":"smoke-test","item_name":"Widget","price_cents":1999}'

    curl -X POST http://localhost:8000/checkout \
      -H "Content-Type: application/json" \
      -d '{"session_id":"smoke-test"}'

The second call should return a real order with `"status":"pending"`. If
either call hangs or refuses to connect, see Troubleshooting below before
going further.

## 4. Set up the Python side

In a separate terminal, with the stack still running:

    python -m venv .venv
    source .venv/Scripts/activate    # Git Bash on Windows
    pip install -r requirements-dev.txt
    playwright install chromium firefox webkit

## 5. Run the test suite against the running stack

    NEXUSQA_BACKEND_URL=http://localhost:8000 pytest tests/ -v

This runs functional, chaos, and security tests against the real
Dockerized backend and Postgres, not an in-process substitute. A test
report is written to `reports/report.html`, and coverage to
`reports/coverage/index.html` — both are regular files, open them
directly in a browser.

## 6. Optional: quick iteration without Docker

For fast local iteration on functional or security tests only (these
use FastAPI's TestClient, which doesn't require the stack running),
SQLite is used automatically as a fallback:

    pytest tests/functional/ tests/security/ -v

Chaos tests that require true concurrency (`test_concurrency_race_conditions.py`)
or multiple real services (`webhook_simulator`) need the Docker stack running
and won't work correctly against TestClient alone.

## 7. Load testing (optional, requires k6 installed separately)

    NEXUSQA_DISABLE_SIGNATURE_CHECK=true docker compose up --build -d
    sleep 5
    k6 run performance/checkout_load.js
    k6 run performance/webhook_load.js
    docker compose down

The disable flag is only ever meant for this measurement — never set it
when running the correctness or security suites, since it turns off
webhook signature verification entirely.

## 8. Tear down

    docker compose down

Add `-v` if you also want to remove the Postgres data volume and start
from a completely clean database next time:

    docker compose down -v

## How CI mirrors this

Every step above has a direct counterpart in `.github/workflows/ci.yml`.
The table below maps local steps to CI jobs, so a local failure and a CI
failure can be compared directly.

| Local step | CI job | Notes |
|---|---|---|
| `pip install ruff mypy pydantic` then manual `ruff check` / `mypy` | `lint-and-typecheck` | Runs first; other jobs don't start if this fails |
| `docker compose up --build -d` | `functional-and-security-tests`, `chaos-tests`, `performance-tests` | Each job starts its own copy of the stack independently |
| `pytest tests/functional/ tests/security/` across browsers | `functional-and-security-tests` (matrix: chromium, firefox, webkit) | Runs once per browser, same test files each time |
| `pytest tests/chaos/` | `chaos-tests` | Runs in its own job so a chaos flake doesn't block visibility into the browser matrix |
| `k6 run performance/*.js` | `performance-tests` | Runs with `continue-on-error: true` — reports results but never blocks a merge |
| `docker compose down` | Each job's teardown step | Runs with `if: always()`, so containers are cleaned up even when tests fail |

The one difference worth knowing: CI sets `NEXUSQA_WEBHOOK_SECRET` from a
GitHub Actions repository secret, not from a committed `.env` file. Locally
you're reading your own `.env`; in CI, the same variable name is injected
by the workflow. The application code never knows the difference.

## Troubleshooting

**`curl` refuses to connect on port 8000.**
Run `docker compose logs backend`. If Postgres wasn't marked healthy in
time, the backend may have crashed on startup trying to connect too
early. Restarting with `docker compose up --build` (no `-d`, so you see
live logs) usually shows the actual cause immediately.

**Port already in use.**
Something else on your machine is bound to 8000 or 5432. Stop it, or
change the left-hand side of the port mapping in `docker-compose.yml`
(e.g. `"8001:8000"`), and adjust `NEXUSQA_BACKEND_URL` to match.

**Playwright tests fail with a browser-not-found error.**
Re-run `playwright install chromium firefox webkit` — this step is easy
to forget after a fresh `pip install`, since it's a separate download
step outside of `pip`.

**Tests pass locally but fail only in CI.**
Check whether the failing test depends on precise timing (a race
condition test, a timeout test). CI runners are more resource-constrained
than most laptops, so timing margins that are comfortable locally can be
tight in CI. See the Phase 7 timeout entry in
[challenges-and-solutions.md](challenges-and-solutions.md) for a real
example of this exact problem being diagnosed and fixed.