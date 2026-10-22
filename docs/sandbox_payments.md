# Family Subscription Sandbox Payments

## Overview
WiFi Sense provides a SANDBOX payment provider implementation for the `CARE_MONTHLY` subscription lifecycle.
No real money moves and no card or financial details are collected, stored, or processed.

## Configuration & Environment Variables

| Variable | Type | Default | Description |
|---|---|---|---|
| `PAYMENTS_MODE` | string | `sandbox` | Provider mode (only `sandbox` is currently implemented). |
| `PAYMENT_WEBHOOK_SECRET` | string | Auto-generated in dev | HMAC-SHA256 secret for signing and verifying webhooks. Required in production. |
| `PAYMENTS_SANDBOX_SIMULATOR_ENABLED` | boolean | `true` in non-prod, `false` in prod | Gates simulation endpoints. |

## Production Gating & Simulator Endpoints

The sandbox simulator endpoints allow testing the full checkout and renewal lifecycle in development:
- `POST /payments/checkout`: Generates a sandbox checkout session ID.
- `POST /payments/sandbox/checkout/{checkout_id}/complete`: Simulates user completion (success/failure) of a payment.
- `POST /payments/sandbox/simulate`: Simulates recurring renewal or provider cancellation events.

### Behavior by Environment
1. **Non-Production (`ENVIRONMENT != production`)**:
   - `PAYMENTS_SANDBOX_SIMULATOR_ENABLED` defaults to `true`.
   - Simulation endpoints are active and accessible.
2. **Production (`ENVIRONMENT = production`)**:
   - `PAYMENTS_SANDBOX_SIMULATOR_ENABLED` defaults to `false`.
   - Any attempt to invoke `POST /payments/checkout`, `POST /payments/sandbox/checkout/{id}/complete`, or `POST /payments/sandbox/simulate` returns **HTTP 404**.
   - To explicitly enable simulation in a staging-like production build, set `PAYMENTS_SANDBOX_SIMULATOR_ENABLED=1` (or `true`).

## Webhook Verification Remains Active
The webhook receiver endpoint:
- `POST /payments/webhooks/sandbox`

is **independent** of `PAYMENTS_SANDBOX_SIMULATOR_ENABLED`. It verifies signed HTTP payloads using HMAC-SHA256 signatures via the `X-Sandbox-Signature` header and enforces timestamp tolerance (default 300 seconds) and replay protection regardless of the simulation gate.
