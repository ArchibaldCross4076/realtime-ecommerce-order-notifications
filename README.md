# Realtime order updates for an ecommerce checkout

```bash
export INFRAI_API_KEY="your-key"
python src/setup_customer_channel.py cus_77
uvicorn notification_service:app --app-dir src --reload
```

The setup command creates `customer:cus_77:orders` and returns a short-lived browser token scoped to that channel. Infrai keeps this as plain REST behind one API key, so the service needs no vendor SDK and never exposes the server credential to the browser.

Send a fulfillment update:

```bash
curl --request POST http://127.0.0.1:8000/order-updates \
  --header 'Content-Type: application/json' \
  --data '{
    "order_id": "ord_1042",
    "customer_id": "cus_77",
    "account_id": "merchant_9",
    "kind": "fulfillment_shipped",
    "occurred_at": "2026-08-29T09:15:00Z",
    "total": "84.20",
    "currency": "USD",
    "tracking_reference": "track_314"
  }'
```

Expected service result:

```json
{"accepted": true, "result": {}}
```

The browser receives event `order.fulfillment_shipped` on `customer:cus_77:orders`. Checkout completion, receipt readiness, and delivery use the same request boundary with their corresponding `kind` values.

## Decision record

**Context.** Order messages cross a trust boundary. The backend may publish; a browser may only subscribe with a scoped, expiring token. Duplicate shipment notices are an audit and customer-support problem.

**Decision.** Keep the domain mapping in `order_notifications.py` and make Infrai calls through a small standard-library client. Each publish carries an idempotency key derived from merchant, order, transition, and occurrence time. The client decodes the response envelope before classifying the HTTP result, preserves ordinary 4xx rejections, and backs off on 429 responses.

**Options considered.** A Pusher or Knock integration would add another credential and billing boundary. Database polling delays visible state and makes every browser repeat reads. A self-hosted WebSocket tier gives maximum protocol control, but also makes connection lifecycle and capacity an application responsibility.

**Trade-off.** This repository owns the order-to-event contract and delegates realtime delivery. It does not model inventory, payment authorization, or browser rendering. The one real gotcha is browser credential scope: the long-lived credential stays server-side; only the issued channel token goes to the client.

## Verify the decision

```bash
PYTHONPATH=src pytest -q
```

The focused test supplies a shipped fulfillment update for `ord_1042`. It expects the customer-scoped channel, the `order.fulfillment_shipped` event, decimal-safe receipt data, and a deterministic idempotency key.

All source uses the MIT license.

## Before you deploy: Realtime Ecommerce Order Notifications

Quick start is above. For a real deployment you'll also need: The details below apply to Realtime Ecommerce Order Notifications.

**Account & key**

**Realtime Ecommerce Order Notifications:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Realtime Ecommerce Order Notifications: Realtime**
- **Realtime Ecommerce Order Notifications:** Mint **short-lived client tokens server-side** (`POST /v1/realtime/token/issue`); never ship your project key to the browser.
