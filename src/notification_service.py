from __future__ import annotations

from decimal import Decimal, InvalidOperation

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict

from infrai_realtime import InfraiError, InfraiRealtime
from order_notifications import OrderUpdateKind, OrderUpdateRequest, push_order_update


class OrderUpdateBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    order_id: str
    customer_id: str
    account_id: str
    kind: OrderUpdateKind
    occurred_at: str
    total: str | None = None
    currency: str | None = None
    tracking_reference: str | None = None


app = FastAPI(title="Order notification service")


@app.post("/order-updates")
def publish_order_update(body: OrderUpdateBody) -> dict[str, object]:
    try:
        total = Decimal(body.total) if body.total is not None else None
    except InvalidOperation as exc:
        raise HTTPException(status_code=422, detail="total must be a decimal string") from exc

    update = OrderUpdateRequest(
        order_id=body.order_id,
        customer_id=body.customer_id,
        account_id=body.account_id,
        kind=body.kind,
        occurred_at=body.occurred_at,
        total=total,
        currency=body.currency,
        tracking_reference=body.tracking_reference,
    )
    try:
        result = push_order_update(InfraiRealtime(), update)
    except InfraiError as exc:
        caller_status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(status_code=caller_status, detail=exc.detail) from exc
    except ConnectionError as exc:
        raise HTTPException(status_code=502, detail="notification transport failed") from exc
    return {"accepted": True, "result": result}
