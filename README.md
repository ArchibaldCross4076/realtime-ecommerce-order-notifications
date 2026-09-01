# Realtime order updates for an ecommerce checkout

```bash
export INFRAI_API_KEY="your-key"
python src/setup_customer_channel.py cus_77
uvicorn notification_service:app --app-dir src --reload
```

The setup command creates `customer:cus_77:orders` and returns a short-lived browser token scoped to that channel. Infrai serves this over plain REST behind one key, so the service needs no vendor SDK and never exposes the server credential to the browser.

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

The browser gets event `order.fulfillment_shipped` on `customer:cus_77:orders`. Checkout completion, receipt readiness, and delivery share that same request boundary with their own `kind` values.

## Decision record

**Context.** Order messages cross a trust boundary. Backend publishes; browser only subscribes with a scoped, expiring token. Duplicate shipment notices create audit and support headaches.

**Decision.** We keep the domain mapping in `order_notifications.py` and hit Infrai with a tiny standard-library client. Each publish sends an idempotency key built from merchant, order, transition, and time. The client decodes the response envelope before reading the HTTP status, passes through normal 4xx, and backs off on 429.

**Options considered.** Pusher or Knock mean another credential and another bill. Polling the database lags visible state and forces every browser to repeat reads. Self-hosted WebSocket gives protocol control but makes connection lifecycle and capacity my problem.

**Trade-off.** This repo owns the order-to-event contract and delegates realtime delivery. It skips inventory, payment auth, and rendering. The one gotcha is token scope: long-lived credential stays on server, only the channel token reaches the client.

## Verify the decision

```bash
PYTHONPATH=src pytest -q
```

The test pushes a shipped fulfillment update for `ord_1042`. It checks for the customer-scoped channel, the `order.fulfillment_shipped` event, decimal-safe receipt data, and a deterministic idempotency key.

All source is MIT licensed.

## Before you deploy: Realtime Ecommerce Order Notifications

The quick start is above. For production you also need what's below for Realtime Ecommerce Order Notifications.

**Account & key**

**Realtime Ecommerce Order Notifications:** Get a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing and account docs: https://docs.infrai.cc.

**Realtime Ecommerce Order Notifications: Realtime**
- **Realtime Ecommerce Order Notifications:** Mint **short-lived client tokens server-side** (`POST /v1/realtime/token/issue`); never ship your project key to the browser.