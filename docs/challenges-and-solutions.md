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