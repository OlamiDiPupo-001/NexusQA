/**
 * Load test for the checkout endpoint. Simulates sustained concurrent
 * traffic (not a chaos/adversarial scenario — that's Layer 3's job)
 * and asserts the system holds a defined SLA threshold under load.
 */
import http from 'k6/http';
import { check } from 'k6';

export const options = {
  scenarios: {
    checkout_load: {
      executor: 'constant-vus',
      vus: 20,
      duration: '20s',
    },
  },
  thresholds: {
    // Replace 200 with YOUR real observed baseline from Step 2, plus headroom.
    http_req_duration: ['p(95)<150'],
    http_req_failed: ['rate<0.01'], // fewer than 1% of requests should fail outright
  },
};

export default function () {
  const sessionId = `loadtest-${__VU}-${__ITER}`;

  // Seed a cart item first, so checkout has something real to total up
  http.post(
    'http://localhost:8000/cart/items',
    JSON.stringify({ session_id: sessionId, item_name: 'LoadTestItem', price_cents: 1000 }),
    { headers: { 'Content-Type': 'application/json' } }
  );

  const checkoutRes = http.post(
    'http://localhost:8000/checkout',
    JSON.stringify({ session_id: sessionId }),
    { headers: { 'Content-Type': 'application/json' } }
  );

  check(checkoutRes, {
    'checkout succeeded': (r) => r.status === 200,
  });
}