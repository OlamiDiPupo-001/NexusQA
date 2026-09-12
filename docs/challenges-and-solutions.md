# Challenges and solutions

Problems hit while building NexusQA, in order, with how each one got diagnosed and fixed.

## Ruff and mypy disagreeing with each other (Phase 5)

Ruff flagged the OrderStatus enum for inheriting from both str and Enum, and separately, mypy was configured against a different Python version than pyproject.toml. The enum fix was easy: ruff's own message named StrEnum as the replacement. The version mismatch took more digging, since pre-commit had quietly drifted to a newer default during an autoupdate. Once both config files pointed at the same version as the real interpreter, both errors cleared. Version drift across config files causes errors that look unrelated to each other.

## FastAPI and datetime deprecation warnings (Phase 6)

Nothing failed, but pytest kept printing warnings for the old `@app.on_event("startup")` pattern and for `datetime.utcnow()`. Both warnings pointed straight at their replacements: a lifespan context manager, and `datetime.now(UTC)`. Warnings that don't break the build are still worth fixing right away, since a future library update can turn one into a hard failure with no notice.

## mypy resolving the same file two different ways (Phase 6)

mypy failed with "source file found twice under different module names." The cause was a missing `backend/__init__.py`, even though the file one level deeper already existed, so mypy could resolve the same route file under two different names depending on which folder it treated as the package root. Adding the missing file fixed it. Every directory in an import path needs one, not just the deepest folder.

## SQLAlchemy's older ORM style fighting mypy (Phase 6)

db.py used SQLAlchemy's classic `declarative_base()` and `Column()` style, which mypy can't type-check properly. Migrating to SQLAlchemy 2.0's `DeclarativeBase` and `Mapped[]` syntax cleared several unrelated-looking errors at once, including a type mismatch in the webhook route. When a library ships a typed alternative to an older API, it's worth adopting early instead of fighting the type checker indefinitely.

## Checking whether httpx2 was a real package (Phase 7)

Starlette's TestClient started warning about httpx2 as a replacement for httpx. The first instinct was to assume it wasn't real and ignore it, which turned out to be wrong — httpx2 is an actual, actively maintained continuation of httpx. The migration got deferred anyway, since swapping the HTTP client mid-build carries more risk than a cosmetic warning justifies. Two lessons here: verify a claim about a package before asserting it, and a warning being genuine doesn't mean it needs fixing immediately.

## A real concurrency race condition (Phase 7)

A deliberately naive checkout endpoint read the stock count, waited briefly, then wrote back a decrement. Firing 5 concurrent requests at a stock of 3 produced 5 successful purchases instead of 3, which proved the race was real, not theoretical. The fix replaced the two-step read-then-write with a single atomic SQL update, letting the database guarantee the check and decrement happen as one step. Races don't show up in single-request testing, only under genuine concurrent load, and the fix belongs in the database rather than in application-level locking, since a lock only protects one process.

## A timeout test that passed most of the time (Phase 7)

A test asserting that a client times out against a slow endpoint used a 1.5 second server delay against a 1.0 second client timeout. It passed locally but failed intermittently with no code changes in between — the two values were too close together, so ordinary timing jitter could push the response across the boundary either way. Widening the delay to 3 seconds against the same 1.0 second timeout removed the ambiguity. A test that only fails sometimes is worse than no test, since it wastes time chasing flakiness instead of real bugs.

## Rate-limit state leaking from one test into the next (Phase 8)

A test asserting that legitimate requests are never penalized failed on its first request with a 429, despite sending only correctly signed payloads. The cause was a plain Python list tracking failed signature attempts, left over from the previous test, which had run immediately before and well inside the lockout window. The database resets between tests through an existing fixture, but that list isn't part of the database, so nothing was clearing it. The fix added a reset for both the signature lockout and the general rate limiter, wired in as an autouse fixture so every security test starts clean automatically. Database fixtures only protect against database state — anything held in memory needs its own reset.

## Layer 7 (k6 performance/load testing)
The http_req_duration: p(95)<80 threshold failed on first run because the 80ms target was picked arbitrarily rather than measured, so I re-ran k6 against the Dockerized backend with no threshold set, read the actual p95 from that baseline run's summary output, set the threshold a bit above that real baseline, and confirmed it now passes consistently while still catching genuine regressions.

## A feature flag that was unreachable (Phase 11)

The plan for the k6 webhook load test was to disable signature checking through an environment flag, so the load test could measure raw endpoint performance. It didn't work: the signature header was declared as required, so FastAPI rejected any request missing it before the flag's logic ever ran. Making the header optional, and having the code explicitly handle a missing signature, fixed it. A flag meant to skip application logic is useless if something earlier in the request pipeline blocks the request first.

## An untested, unused helper function (Phase 11)

The coverage report showed framework/db_helpers.py at 0%, meaning count_orders_with_status had never actually been called anywhere. It was written back in Phase 6 with Phase 7's idempotency test in mind, but that test ended up querying the order table directly instead. The fix was to rewrite the idempotency test to call the helper and assert on order status specifically, which turned out to be a stronger check than the original row count. A function that exists for a stated purpose but sits at zero coverage is worth resolving one way or the other — either use it or remove it, rather than leaving it unexplained in the final code.