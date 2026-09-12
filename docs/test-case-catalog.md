# Test case catalog

21 automated tests across Layers 2 to 4, plus two k6 load scenarios in
Layer 7.

## Layer 2 — functional

| Test | File | Proves |
|---|---|---|
| test_add_item_to_cart | test_checkout_api.py | Cart accepts an item and returns it |
| test_checkout_creates_pending_order | test_checkout_api.py | Checkout creates an order with the correct total and pending status |
| test_order_lookup_after_checkout | test_checkout_api.py | An order can be retrieved by its own ID by its owning session |
| test_order_not_found_returns_404 | test_checkout_api.py | A nonexistent order ID returns 404, not a crash |
| test_checkout_response_matches_order_contract | test_order_schema_contract.py | The API's response shape matches the Order Pydantic model exactly |
| test_checkout_page_confirms_payment | test_checkout_ui.py | The checkout page renders and responds to a real browser click, across Chromium, Firefox, and WebKit |

## Layer 3 — event-driven and chaos

| Test | File | Proves |
|---|---|---|
| test_valid_signature_is_accepted | test_webhook_signature_verification.py | A correctly signed webhook is accepted |
| test_invalid_signature_is_rejected | test_webhook_signature_verification.py | An unsigned webhook is rejected with 401 |
| test_tampered_payload_is_rejected | test_webhook_signature_verification.py | A payload altered after signing is rejected, even with a signature that was valid for the original data |
| test_duplicate_webhook_event_processed_once | test_webhook_idempotency.py | Replaying the same event_id twice results in exactly one paid order, verified directly against the database |
| test_concurrent_checkout_does_not_oversell | test_concurrency_race_conditions.py | 5 concurrent checkout requests against a stock of 3 result in exactly 3 successful purchases, not more |
| test_malformed_webhook_returns_400_not_500 | test_corrupted_payloads.py | A webhook missing a required field is rejected gracefully instead of crashing the handler |
| test_client_backs_off_and_succeeds_after_rate_limit | test_rate_limit_stress.py | A client using Tenacity-based retry eventually succeeds against a server returning 429 |
| test_client_times_out_on_slow_response | test_latency_injection.py | A client with a 1-second timeout fails predictably against a 3-second-slow endpoint, rather than hanging |

## Layer 4 — security

| Test | File | Proves |
|---|---|---|
| test_sql_injection_cannot_bypass_where_clause | test_sql_injection.py | A crafted OR '1'='1' payload cannot bypass a WHERE clause once the query is parameterized |
| test_cannot_view_another_sessions_order | test_authz_bypass.py | A session cannot view another session's order by guessing its ID (IDOR) |
| test_owner_can_view_their_own_order | test_authz_bypass.py | The ownership check doesn't block legitimate access by the actual owner |
| test_card_number_never_appears_unmasked_in_logs | test_sensitive_data_exposure.py | A card number is never written to logs in plaintext |
| test_invalid_signature_error_does_not_leak_internals | test_sensitive_data_exposure.py | A rejected webhook's error response contains no payload data or secrets |
| test_repeated_invalid_signatures_trigger_lockout | test_auth_rate_limit_abuse.py | Repeated failed signature attempts trigger a 429 lockout |
| test_legitimate_requests_are_never_penalized | test_auth_rate_limit_abuse.py | Correctly signed requests are never counted against the lockout, even in volume |

## Layer 7 — performance

| Scenario | File | Proves |
|---|---|---|
| checkout_load | checkout_load.js | Checkout holds p95 latency under 150ms at 20 concurrent virtual users, against a measured baseline of 105ms |
| webhook_load | webhook_load.js | The webhook endpoint holds the same latency threshold under 15 concurrent virtual users, measured independent of HMAC computation cost |