# Architecture Decision Records

## ADR-001: Custom minimal FastAPI backend instead of an existing mock API
Building a small, purpose-built backend (4-5 endpoints) rather than using
an existing fake e-commerce API gives full control over failure modes —
specifically the ability to seed deliberate bugs (naive stock decrement,
unsanitized logging, unparameterized SQL) that later phases catch and fix.
An off-the-shelf mock couldn't guarantee these specific, demonstrable gaps.

## ADR-002: Layer-based repository structure instead of feature-based
Organizing top-level folders by test layer (functional/chaos/security)
rather than by feature (checkout/cart/orders) keeps each layer's
pass/fail philosophy isolated. A chaos test and a security test hitting
the same endpoint have fundamentally different intent; mixing them by
feature would blur that distinction.

## ADR-003: Postgres via Docker Compose instead of SQLite for the running system
SQLite is a single-file database with no separate server process — it
can't accurately represent real concurrent-connection behavior. Since
Layer 3's atomic-update fix depends specifically on real database
locking guarantees, Postgres is required to make that proof meaningful,
not just convenient for local development.

## ADR-004: pytest-html instead of Allure for reporting
Allure produces a more polished report but requires a separate
Java-based generator and heavier CI setup. Given time constraints,
pytest-html delivers a real, presentable artifact at a fraction of the
setup cost — the right tool for a four-week solo build.

## ADR-005: k6 (JavaScript) for load testing despite an all-Python stack
k6 is a Go binary with an embedded JS runtime; there's no mature
Python-native load generator with equivalent performance characteristics
(a Python-based load generator risks becoming the bottleneck itself at
scale). Language consistency was traded for measurement validity.

## ADR-006: Webhook load test runs with signature verification disabled
k6's crypto primitives don't trivially replicate Python's hmac.new()
without substantial manual reimplementation. Rather than fake a
signature (producing misleading pass/fail results) or silently skip the
limitation, the load test measures raw endpoint capacity via an
explicit, environment-gated flag (NEXUSQA_DISABLE_SIGNATURE_CHECK),
documented here and never enabled in CI or production paths.

## ADR-007: Tenacity over hand-rolled retry logic
Hand-written retry/backoff loops are more error-prone than they appear,
and Tenacity is a real, current, checkable production-grade tool —
naming it specifically is a stronger signal than "I wrote a for-loop
with sleep()".