# Architecture Decision Records

This log captures decisions made *before* building — the why behind each major technical choice. Updated at the start of each phase that introduces a new decision.

## Decision: Webhook load test measures endpoint performance without HMAC verification

k6's crypto module doesn't cleanly replicate Python's hmac.new() without
substantial manual implementation. Rather than ship a broken/fake
signature that silently passes, the webhook load test measures raw
endpoint throughput with signature verification disabled via an
explicit, clearly-named environment flag (never set in CI or production
paths). This means the webhook load numbers reflect endpoint performance
under load, not the additional (small, constant-time) HMAC computation
cost per request — a reasonable and clearly-documented scope boundary,
not a hidden gap.