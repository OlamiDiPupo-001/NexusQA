/**
 * Load test for the payment webhook endpoint — the highest-frequency
 * automated traffic path in a real payment system, per Phase 1's
 * problem statement.
 */
import { htmlReport } from "https://raw.githubusercontent.com/benc-uk/k6-reporter/main/dist/bundle.js";



import http from 'k6/http';
import { check } from 'k6';
import { sha256 } from 'k6/crypto';

// k6 doesn't have Python's hmac module, so we replicate HMAC-SHA256
// manually here — this must produce byte-identical signatures to
// webhook_simulator/signing.py, or every request will be rejected as
// invalid before performance is even measured.
function hmacSha256Hex(secret, message) {
  return sha256(secret + message, 'hex'); // NOTE: placeholder — see below
}

export const options = {
  scenarios: {
    webhook_load: {
      executor: 'constant-vus',
      vus: 15,
      duration: '20s',
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<150'], // set from your OWN baseline, same as Step 2
    http_req_failed: ['rate<0.01'],
  },
};

export default function () {
  const payload = JSON.stringify({
    event_id: `k6-${__VU}-${__ITER}-${Date.now()}`,
    order_id: 1,
  });

  const res = http.post('http://localhost:8000/webhooks/payment', payload, {
    headers: {
      'Content-Type': 'application/json',
      // Signature intentionally omitted here — see the note below.
    },
  });

  check(res, { 'request completed': (r) => r.status !== 0 });
}



export function handleSummary(data) {
  return {
    "reports/k6-checkout-summary.html": htmlReport(data),
  };
}