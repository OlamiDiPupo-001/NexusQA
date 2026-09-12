# Architecture decision records

## Python as the primary language

The project needed one language across the backend, the test framework,
and the chaos/security tooling, and Python covers all three without
forcing a context switch. FastAPI and Pydantic give typed, validated
models on the backend side; Playwright, HTTPX, and Pytest cover UI, API,
and test orchestration in the same language. The one deliberate exception
is k6, which uses JavaScript for load test scripts, documented separately
below.

## Playwright over Selenium

Selenium is the older, more widely known tool, but Playwright has native
async support, built-in auto-waiting for elements (removing a large
source of Selenium's flakiness), and first-class support for Chromium,
Firefox, and WebKit from one API. Given the project already leans on
Python's async patterns for the chaos layer, keeping the UI layer on a
tool with the same async model rather than mixing paradigms was the
simpler choice.

## FastAPI for the mock backend

Flask and Django were both considered. FastAPI was chosen because it
uses Pydantic natively for request and response validation, which
matches the project's broader decision to use Pydantic models as the
single source of truth for data shape (see Layer 1). It also has
built-in async support, which the webhook and load-testing routes rely
on directly, and a test client that integrates cleanly with Pytest
without extra tooling.

## A custom mock backend instead of an existing fake API

An off-the-shelf mock e-commerce API would have been faster to stand up,
but it wouldn't have had the specific failure modes this project needed
to prove resilience against. Building a small, four-endpoint backend
made it possible to control exactly which bugs exist and when they get
fixed, which is what makes the catch-then-fix pattern used across the
chaos and security layers possible in the first place.

## Docker Compose over a single container

Running the backend, database, and webhook simulator in one container
would have been simpler to set up, but it wouldn't represent how these
systems actually run in production, and it would mean networking, health
checks, and cross-service failure modes never get exercised at all.
Docker Compose keeps each service isolated and independently restartable,
matching the eventual multi-container reality the tests are meant to
validate.

## HMAC-SHA256 for webhook signature verification

The webhook signature scheme mirrors how Stripe signs real webhooks:
a shared secret, a hash computed over the exact payload, sent alongside
the request and recomputed on the receiving end. Modeling it this way,
rather than inventing a simpler custom scheme, means the signature
verification tests reflect a pattern that maps directly onto a real
payment provider's behavior instead of a toy version of the problem.

## Layer-based folder structure over feature-based

Grouping tests by feature, so all checkout-related tests sit together
regardless of type, was considered and rejected. Chaos and security
tests carry a different pass/fail philosophy than functional tests even
when they exercise the same endpoint, and mixing them by feature would
blur that distinction. Tests are grouped by layer instead — functional,
chaos, security — each with its own fixtures, so a change to one layer
can't silently affect another.

## SQLite for early development, Postgres in Docker Compose

The backend started on SQLite so development could begin without Docker
running. Postgres was introduced once Docker Compose was built, since
SQLite doesn't represent real concurrent-connection behavior accurately,
which matters for validating the atomic database update used to fix the
Layer 3 concurrency race condition. The swap needed no code changes
outside the connection string, since the database URL was centralized in
the config module from the start.

## Tenacity over hand-rolled retry logic

A manual retry loop with a sleep-based backoff would work, but Tenacity
is closer to what production Python code actually uses for this, it
avoids the subtle timing bugs hand-rolled backoff logic tends to
introduce, and it's a specific, checkable library skill rather than a
generic loop.

## A global lockout counter instead of per-sender tracking

The webhook signature lockout tracks failed attempts globally rather
than per IP address or API key. Per-sender tracking would be the more
correct approach in a system with real distinct clients, since it
isolates the impact to whoever is actually misbehaving. This project has
no concept of distinct senders by design, so a global counter is the
simplest implementation that still demonstrates the underlying pattern
honestly.

## The webhook load test runs without HMAC verification

k6's crypto tooling doesn't cleanly reproduce Python's HMAC computation
without a substantial manual reimplementation. Rather than risk a
signature that might not match byte-for-byte and produce misleading
results, the webhook load test disables signature checking through an
explicit, clearly named environment flag, never set in the correctness
or security test paths. The resulting numbers measure raw endpoint
throughput, not the additional cost of signature verification per
request.

## pytest-html over Allure for reporting

Allure produces a more polished report with history across runs, but it
needs a separate Java-based report generator and more CI setup to
publish correctly. pytest-html produces a single, self-contained HTML
file with a fraction of the setup cost, which was judged the better
trade-off given the project's time budget.