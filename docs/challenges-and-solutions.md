# Challenges & Solutions

## Phase 5 — repeated version mismatches traced to wrong assumed Python version

**What broke:** Three separate-looking errors (ruff target-version invalid,
StrEnum feature availability, mypy version format) across two commit
attempts, all pointing at "wrong Python version" in different files.

**Diagnosis:** Ran `python3 --version` directly instead of continuing to
guess-and-check each config file individually.

**Root cause:** Actual installed Python was 3.14.4, but every config file
had been set assuming 3.11 (the version originally instructed, without
verifying against the real local install first). Additionally, ruff's
current release doesn't yet recognize "py314" as a valid target — it
tops out at py313.

**Fix:** Verified real interpreter version first. Set pyproject.toml and
.pre-commit-config.yaml to py313/3.13 (closest valid target ruff
supports), rather than continuing to chase individual symptom errors.

**Lesson:** Always verify the actual installed tool version BEFORE setting
config files, rather than assuming a documented/instructed version is
correct — and check what your linting tools currently support, since
tooling version support can lag behind the newest language release.