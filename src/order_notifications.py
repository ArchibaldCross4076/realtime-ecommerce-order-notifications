from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal
from enum import StrEnum
from hashlib import sha256
from typing import Any

from infrai_realtime import InfraiRealtime


class OrderUpdateKind(StrEnum):
    CHECKOUT_COMPLETED = "checkout_completed"
    FULFILLMENT_SHIPPED = "fulfillment_shipped"
    RECEIPT_READY = "receipt_ready"
    ORDER_DELIVERED = "order_delivered"


@dataclass(frozen=True)
class OrderUpdateRequest:
    order_id: str
    customer_id: str
    account_id: str
    kind: OrderUpdateKind
    occurred_at: str
    total: Decimal | None = None
    currency: str | None = None
    tracking_reference: str | None = None


@dataclass(frozen=True)
class NotificationDecision:
    channel: str
    event: str
    data: dict[str, Any]
    account_id: str
    idempotency_key: str


def decide_notification(update: OrderUpdateRequest) -> NotificationDecision:
    channel = f"customer:{update.customer_id}:orders"
    event_by_kind = {
        OrderUpdateKind.CHECKOUT_COMPLETED: "order.checkout_completed",
        OrderUpdateKind.FULFILLMENT_SHIPPED: "order.fulfillment_shipped",
        OrderUpdateKind.RECEIPT_READY: "order.receipt_ready",
        OrderUpdateKind.ORDER_DELIVERED: "order.delivered",
    }
    data = {
        key: str(value) if isinstance(value, Decimal) else value
        for key, value in asdict(update).items()
        if value is not None and key not in {"customer_id", "account_id", "kind"}
    }
    raw_key = f"{update.account_id}:{update.order_id}:{update.kind}:{update.occurred_at}"
    return NotificationDecision(
        channel=channel,
        event=event_by_kind[update.kind],
        data=data,
        account_id=update.account_id,
        idempotency_key="order-update:" + sha256(raw_key.encode()).hexdigest(),
    )


def push_order_update(client: InfraiRealtime, update: OrderUpdateRequest) -> dict[str, Any]:
    decision = decide_notification(update)
    return client.publish(
        channel=decision.channel,
        event=decision.event,
        data=decision.data,
        account_id=decision.account_id,
        idempotency_key=decision.idempotency_key,
    )
