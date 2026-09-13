# Dependency hierarchy

This describes the codebase's import structure: what's allowed to depend on what. Dependencies point one direction, from test code through feature code down to foundational code.

## Tier 3 — test code

Knows about features. Imports from Tier 2 and Tier 1 freely. Nothing
outside this tier imports from here.

    tests/conftest.py
        (root-level fixtures shared by all test layers — currently just
        the api_client fixture)

    tests/functional/
        conftest.py       (fresh DB schema + TestClient per test)
        test_checkout_api.py            (cart, checkout, order lookup happy path)
        test_order_schema_contract.py   (API response shape matches the Order model)
        test_checkout_ui.py             (Playwright, real browser against a live server)

    tests/chaos/
        conftest.py       (same client fixture pattern, scoped to this folder)
        test_webhook_signature_verification.py  (valid, invalid, and tampered signatures)
        test_webhook_idempotency.py             (duplicate event_id processed once)
        test_concurrency_race_conditions.py     (concurrent checkout vs limited stock)
        test_corrupted_payloads.py              (malformed webhook rejected gracefully)
        test_rate_limit_stress.py               (Tenacity retry against a 429)
        test_latency_injection.py               (client timeout against a slow endpoint)

    tests/security/
        conftest.py       (client fixture, plus autouse reset of rate-limit state)
        test_sql_injection.py           (OR '1'='1' against the stock search endpoint)
        test_authz_bypass.py            (IDOR check on order lookup)
        test_sensitive_data_exposure.py (card number never appears in logs or error bodies)
        test_auth_rate_limit_abuse.py   (brute-force lockout on repeated bad signatures)

    performance/
        checkout_load.js  (k6 — checkout endpoint under sustained concurrent load)
        webhook_load.js   (k6 — webhook endpoint, signature checking disabled for this run)

## Tier 2 — feature code

Knows about the domain: carts, checkout, orders, webhooks. Imports
freely from Tier 1. Should not import from other Tier 2 files unless
one feature genuinely depends on another.

    backend/app/main.py
        (wires every route into the FastAPI app, owns startup/lifespan,
        also serves the minimal checkout-page HTML used by the UI test)

    backend/app/routes/cart.py
        (in-memory cart storage, add_item, get_cart_total)

    backend/app/routes/checkout.py
        (creates a pending order from a cart's total; also owns
        checkout_limited_stock, the deliberately-then-fixed endpoint
        used to prove and then close the concurrency race condition;
        imports get_cart_total from cart.py — the one legitimate
        feature-to-feature dependency in the project)

    backend/app/routes/orders.py
        (looks up an order by id, enforces session ownership via the
        X-Session-Id header, returns 403/404 as appropriate)

    backend/app/routes/stock.py
        (stock search endpoint; the parameterized-query fix for the
        SQL injection test lives here)

    backend/app/routes/webhooks.py
        (signature verification, idempotency check, brute-force
        lockout, sanitized logging, plus the rate-limited and
        slow-response test-support endpoints)

    webhook_simulator/simulator.py
        (builds and sends signed webhook events; supports normal,
        tampered, and malformed sends)

    framework/pom/cart_page.py
        (placeholder — no cart UI test currently exercises this)

    framework/pom/checkout_page.py
        (knows the checkout page's actual button and confirmation
        element IDs; used by the one Playwright test)

## Tier 1 — foundational code

No knowledge of any specific feature. Imports nothing from Tier 2 or
Tier 3. Everything above depends on some part of this tier.

    backend/app/db.py
        (SQLAlchemy engine/session setup, OrderRecord, StockRecord,
        ProcessedWebhookEvent table definitions, is_event_processed,
        mark_event_processed, seed_stock)

    backend/app/models.py
        (Order and OrderStatus Pydantic models — the contract used in
        the schema contract test)

    backend/app/logging_utils.py
        (sanitize_for_logging — masks card_number and cvv before
        anything gets logged)

    framework/config.py
        (Settings: backend_url, db_url, webhook_secret, default_timeout
        — all environment-variable driven, no hardcoded values)

    framework/api_client.py
        (ApiClient — thin httpx wrapper, plus post_with_retry using
        Tenacity for backoff against 429s)

    framework/db_helpers.py
        (count_orders_with_status — used by the idempotency test to
        verify exactly one paid order exists after a replayed event)

    framework/pom/base_page.py
        (BasePage — holds the Playwright page reference, nothing else;
        every page object inherits from this)

    webhook_simulator/signing.py
        (sign_payload, verify_signature — HMAC-SHA256 over a sorted
        JSON payload; imported by both simulator.py and webhooks.py,
        which is why it lives here instead of inside either feature)
