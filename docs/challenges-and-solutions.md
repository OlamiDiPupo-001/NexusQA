# Challenges & Solutions

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