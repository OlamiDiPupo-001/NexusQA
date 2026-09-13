# Naming conventions

The actual patterns already in use across this codebase, written down
so a new file added later can match the existing ones instead of
guessing.

## Test functions

`test_<subject>_<condition>_<expected_outcome>`, always snake_case, always
long enough to read as a sentence describing the scenario.
    test_checkout_creates_pending_order
    test_duplicate_webhook_event_processed_once


## Test files

`test_<layer>_<feature>.py`, one file per specific thing being tested,
grouped by layer folder rather than by feature:
    tests/chaos/test_webhook_idempotency.py
    tests/security/test_sql_injection.py

## Fixtures

`<noun>` for objects, lowercase, snake_case, named after what they hand back, not what they
do internally: `client`, `api_client`, `chaos_server`, `live_server`. A
leading underscore marks a fixture that runs automatically and isn't
meant to be requested by name in a test signature, like
`_reset_webhook_rate_limit_state`.

## Routes

REST-style paths, resource nouns for lookups, verb-like segments for
actions:
    /cart/items
    /stock/search
    /webhooks/payment

## Database tables

Snake_case, plural: `orders`, `stock`, `processed_webhook_events`.

## ORM model classes

PascalCase, singular, with a `Record` suffix to keep them visually
distinct from the Pydantic models sharing similar names: `OrderRecord`,
`StockRecord`.

## Pydantic models

PascalCase, singular, no suffix: `Order`, `WebhookEvent`. `OrderStatus`
is an enum, same casing convention.

## Environment variables

`NEXUSQA_<SCREAMING_SNAKE_CASE>`, always prefixed so they're
unambiguous against any other environment variable on a shared machine
or CI runner: `NEXUSQA_BACKEND_URL`, `NEXUSQA_WEBHOOK_SECRET`.

## Config settings

Same name as the environment variable, lowercased, prefix dropped, since
the prefix's only job was avoiding collisions in the environment itself:
`backend_url`, `db_url`, `webhook_secret`.

## Helper functions

`verb_noun`, snake_case, named after the single thing they do:
`sign_payload`, `verify_signature`, `mark_event_processed`.

## Documentation files

Kebab-case, always `docs/`: `architecture.md`, `challenges-and-solutions.md`, `setup-and-run.md`.
