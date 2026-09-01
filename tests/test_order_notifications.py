from decimal import Decimal

from order_notifications import OrderUpdateKind, OrderUpdateRequest, decide_notification


def test_shipment_becomes_customer_scoped_notification() -> None:
    update = OrderUpdateRequest(
        order_id="ord_1042",
        customer_id="cus_77",
        account_id="merchant_9",
        kind=OrderUpdateKind.FULFILLMENT_SHIPPED,
        occurred_at="2026-08-29T09:15:00Z",
        total=Decimal("84.20"),
        currency="USD",
        tracking_reference="track_314",
    )

    decision = decide_notification(update)

    assert decision.channel == "customer:cus_77:orders"
    assert decision.event == "order.fulfillment_shipped"
    assert decision.data["tracking_reference"] == "track_314"
    assert decision.data["total"] == "84.20"
    assert decision.account_id == "merchant_9"
    assert decision.idempotency_key == decide_notification(update).idempotency_key
