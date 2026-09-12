## Phase 5 — ruff UP042 + mypy/ruff version mismatch

**What broke:** ruff-check failed with UP042 ("Class OrderStatus inherits
from both str and enum.Enum"). Separately, .pre-commit-config.yaml had
mypy targeting a different Python version than pyproject.toml.

**Diagnosis:** ruff's error message directly suggested the fix
(enum.StrEnum). The version mismatch was caught by inspection after
noticing the two config files disagreed.

**Root cause:** StrEnum is a 3.11+ feature; since target-version was set
to an older target, ruff correctly flagged the str+Enum pattern as
outdated. The mypy version drifted separately, likely from a pre-commit
autoupdate pulling newer default args.

**Fix:** Switched OrderStatus to inherit from enum.StrEnum directly.
Aligned mypy's --python-version arg to match pyproject.toml and the
actual installed interpreter (3.14).

**Lesson:** Python version needs to agree across every config file that
references it (pyproject.toml, pre-commit hooks, actual installed
interpreter) — drift between them causes confusing, unrelated-looking
errors.

## Phase 6 — FastAPI/datetime deprecation warnings

**What broke:** Nothing failed, but pytest surfaced deprecation warnings
for `@app.on_event("startup")` and `datetime.utcnow()`.

**Diagnosis:** Warning text pointed directly at the FastAPI lifespan-events
docs and at the timezone-aware datetime replacement.

**Root cause:** Both are older APIs being phased out in favor of explicit,
less ambiguous replacements (lifespan context managers; timezone-aware
datetimes instead of naive UTC).

**Fix:** Switched to a `lifespan` async context manager; switched to
`datetime.now(UTC)`.

**Lesson:** Warnings that "don't fail the build" still deserve fixing
promptly — left alone, they compound, and a future library major version
can turn a warning into a hard failure with no notice.

## Phase 6 — mypy "Source file found twice under different module names"

**What broke:** mypy failed with "Source file found twice under different
module names: app.routes.cart and backend.app.routes.cart".

**Diagnosis:** mypy's own error message named both resolutions directly
(add an __init__.py, or use --explicit-package-bases).

**Root cause:** backend/__init__.py was missing, even though
backend/app/__init__.py existed — meaning mypy could resolve the same
file two different ways depending on which directory it treated as the
package root.

**Fix:** Added backend/__init__.py; also added explicit_package_bases = true
to pyproject.toml's [tool.mypy] section as a safeguard.

**Lesson:** Every directory in an import path needs its own __init__.py,
not just the deepest one — a single missing file several levels up can
cause confusing, seemingly-unrelated tooling errors much deeper in the tree.

## Phase 6 — mypy errors from SQLAlchemy's legacy declarative_base() style

**What broke:** mypy failed with "Variable Base is not valid as a type"
and "Invalid base class Base", plus a str/Column[str] assignment mismatch
in webhooks.py.

**Diagnosis:** Both errors trace back to the same file (db.py) and the
same root cause — mypy couldn't infer real Python types from the older
`declarative_base()` + `Column(...)` SQLAlchemy 1.x style.

**Root cause:** SQLAlchemy 2.0 introduced typed ORM syntax
(DeclarativeBase, Mapped[], mapped_column()) specifically to fix this
class of mypy incompatibility; the code was still using the older,
untyped style.

**Fix:** Migrated db.py to SQLAlchemy 2.0's DeclarativeBase/Mapped syntax.

**Lesson:** When a library offers a newer, explicitly type-aware API,
prefer it from the start — the older style isn't wrong, but it actively
fights static type checkers like mypy, and the fix often clears multiple
seemingly-unrelated errors at once.

## Phase 7 — Two deprecation warnings, one real, one still open

**What appeared:** StarletteDeprecationWarning suggesting installation of
`httpx2`, and an anyio.BlockingPortal deprecation warning originating
from inside starlette's own testclient.py.

**Correction:** Initially assumed httpx2 was not a real package — this
was wrong. httpx2 is a real, Pydantic-stewarded continuation of httpx,
and starlette's TestClient genuinely supports it as a replacement.

**Decision:** Deferred switching to httpx2 for now. It's a very recently
established package, and both framework/api_client.py and
webhook_simulator/simulator.py depend on the HTTP client — swapping it
mid-build introduces risk for a cosmetic warning, not a build failure.
Revisiting as a deliberate task post-MVP, not during active feature work.

**Lesson:** Verify claims about a package's existence/status before
asserting them, even when they sound plausible. Also: a warning being
"real" doesn't automatically mean the fix belongs right now — timing
and blast radius matter as much as correctness.

## Phase 7B — Concurrency race condition: naive stock decrement oversold by 100%

**What broke:** A deliberately naive "read stock, sleep, write stock"
checkout endpoint, hit with 5 concurrent requests against a stock of 3,
returned 5 successful 200 OK responses instead of the correct 3 — a
complete failure to prevent overselling.

**Diagnosis:** asyncio.gather() fired 5 real concurrent requests against
a live uvicorn server. All 5 read quantity=3 before any of them wrote
back a decrement, because the read-then-write logic wasn't atomic and
an artificial 0.05s sleep widened the race window enough to make the
collision happen every time rather than intermittently.

**Root cause:** The naive implementation performed the stock check and
the stock decrement as two separate steps (a SELECT, then an UPDATE),
leaving a window where multiple requests could all pass the check before
any of them applied their write.

**Fix:** Replaced the two-step read-then-write with a single atomic SQL
statement — `UPDATE stock SET quantity = quantity - 1 WHERE quantity > 0`
— relying on the database's own locking to guarantee the check-and-
decrement happens as one indivisible operation, not two.

**Lesson:** A race condition doesn't announce itself in single-request
testing — it requires deliberately generating real concurrent load to
surface at all. The fix isn't "add a lock in application code," which
only protects a single process; it's pushing the atomicity guarantee
down into the database itself, so it holds even across multiple
backend instances sharing one DB.

## Phase 7B2 — Client Timeout on Slow Webhook Endpoint

**What broke**: Initial version of `test_client_times_out_on_slow_response` used a
server delay of 1.5s against a 1.0s client timeout. Test passed locally but flaked
intermittently — occasionally the request completed instead of timing out.

**How it was diagnosed**: Re-ran the test multiple times back-to-back; failure rate
was inconsistent and correlated with system load, not code changes — a signature
of a timing-margin problem rather than a logic bug.

**Root cause**: The delay (1.5s) and the timeout (1.0s) were too close together.
Minor jitter (CPU scheduling, network stack overhead) was enough to push actual
response timing across the boundary in either direction, making the test's outcome
non-deterministic.

**Fix**: Increased the server-side delay to 3s while keeping the client timeout at
1.0s, creating a wide safety margin. The client now reliably times out well before
the server would ever respond, regardless of system jitter.

**Why this matters**: A test that only fails sometimes is worse than no test — it
erodes trust in the suite and wastes debugging time chasing "flakiness" instead of
real bugs. Boundary-adjacent timing values should always be avoided when testing
timeouts; leave a wide margin between the timeout and the delay being tested.

## Phase 8B — Module-level rate-limit state leaking across tests

**What broke:** `test_legitimate_requests_are_never_penalized` failed with
a 429 on its very first request, despite sending only correctly-signed
payloads — a test that should never trigger lockout at all.

**Diagnosis:** Traced the 429 back to `_failed_signature_attempts` still
holding 3 timestamps left over from the previous test
(`test_repeated_invalid_signatures_trigger_lockout`), which ran
immediately before it and well within the 5-second lockout window.

**Root cause:** `_failed_signature_attempts` is module-level Python state,
created once when `webhooks.py` is first imported. The existing DB
fixture resets the database between tests, but this list isn't part of
the database — nothing was resetting it, so state silently leaked from
one test into the next.

**Fix:** Added `reset_signature_lockout_state()` to clear both
`_failed_signature_attempts` and `_request_timestamps` (the Phase 7
general rate limiter has the identical leakage risk), wired in as an
`autouse=True` fixture in `tests/security/conftest.py` so every test in
that folder starts from a guaranteed clean slate automatically.

**Lesson:** Database fixtures only protect against database-state
leakage. Any module-level Python state (lists, counters, caches) needs
its own explicit reset mechanism — and a test suite that only passes
because of run order or timing gaps has a real bug, even while it's
technically green.


## Phase 11 — Duplicate/leftover code caused TypeError instead of clean skip

**What broke:** After adding the NEXUSQA_DISABLE_SIGNATURE_CHECK escape
hatch, requests still crashed with a 500 (TypeError: unsupported operand
types 'str' and 'NoneType' in hmac.compare_digest) even with the flag set.

**Diagnosis:** docker compose logs backend revealed the actual
traceback, pointing at an unconditional verify_signature() call still
present in the file, separate from the new flag-guarded block.

**Root cause:** The fix was added alongside the original lockout-check-
and-verify code rather than replacing it — both blocks existed
simultaneously. The flag-guarded block correctly skipped verification,
but execution then fell through into the OLD unconditional block a few
lines later, which called verify_signature() with x_webhook_signature
still None (since no header was sent), causing the TypeError.

**Lesson:** When a fix is described as "update this logic," always
confirm the OLD version is actually removed, not left in place
alongside the new one — a fall-through into leftover code produces
confusing errors that look unrelated to the actual change just made.
Always check the real container logs/traceback before guessing at a
fix; the actual exception (TypeError on None) pointed directly at the
true cause, which was different from the first hypothesis.