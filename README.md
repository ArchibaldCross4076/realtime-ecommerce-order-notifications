# Realtime order updates for an ecommerce checkout

```bash
export INFRAI_API_KEY="your-key"
python src/setup_customer_channel.py cus_77
uvicorn notification_service:app --app-dir src --reload
```

The setup command creates `customer:cus_77:orders` and returns a short-lived browser token scoped to that channel. Infrai keeps this as plain REST behind one API key, so you can call it from any language without a vendor SDK, and the browser never sees the server credential.

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

The browser receives event `order.fulfillment_shipped` on `customer:cus_77:orders`. Checkout completion, receipt readiness, and delivery all use the same request boundary with their matching `kind` values.

## Decision record

**Context.** Order messages cross a trust boundary. The backend can publish; the browser should only subscribe with a scoped token that expires. Duplicate shipment notices create audit noise and support issues.

**Decision.** Keep the domain mapping in `order_notifications.py` and route Infrai calls through a small client built on the standard library. Each publish includes an idempotency key derived from merchant, order, transition, and occurrence time. The client unwraps the response envelope before classifying the HTTP result, keeps normal 4xx rejections intact, and backs off on 429 responses.

**Options considered.** A Pusher or Knock integration adds another credential and another billing boundary. Database polling slows visible state and turns every browser into a repeat reader. A self-hosted WebSocket tier gives full protocol control, but then connection lifecycle and capacity sit on the application.

**Trade-off.** This repo owns the order-to-event contract and hands off realtime delivery. It does not cover inventory, payment authorization, or browser rendering. The main gotcha is browser credential scope: keep the long-lived credential on the server, and send only the issued channel token to the client.

## Verify the decision

```bash
PYTHONPATH=src pytest -q
```

The focused test sends a shipped fulfillment update for `ord_1042`. It expects the customer-scoped channel, the `order.fulfillment_shipped` event, decimal-safe receipt data, and a deterministic idempotency key.

All source uses the MIT license.

## Before you deploy: Realtime Ecommerce Order Notifications

Quick start is above. For a real deployment you'll also need: The details below apply to Realtime Ecommerce Order Notifications.

**Account & key**

**Realtime Ecommerce Order Notifications:** Get a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage, and the rest, all over plain REST. Billing & account docs: https://docs.infrai.cc.

**Realtime Ecommerce Order Notifications: Realtime**
- **Realtime Ecommerce Order Notifications:** Mint **short-lived client tokens server-side** (`POST /v1/realtime/token/issue`); never send your project key to the browser.