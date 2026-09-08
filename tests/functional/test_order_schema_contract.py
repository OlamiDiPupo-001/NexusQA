"""
Contract test: proves the API's actual JSON response can be parsed into
our Order Pydantic model without validation errors. This is different
from test_checkout_api.py's tests, which check specific field VALUES —
this test checks the overall SHAPE matches what the model promises.
"""

from datetime import datetime

from backend.app.models import Order, OrderStatus


def test_checkout_response_matches_order_contract(client):
    client.post(
        "/cart/items",
        json={"session_id": "contract1", "item_name": "Thing", "price_cents": 800},
    )
    checkout_response = client.post("/checkout", json={"session_id": "contract1"})
    order_id = checkout_response.json()["order_id"]

    lookup_response = client.get(f"/orders/{order_id}")
    data = lookup_response.json()

    # This is the actual contract check: if the backend's response shape
    # ever drifts from what Order expects, this raises a ValidationError
    # right here, with a precise message about which field broke.
    order = Order(
        id=data["order_id"],
        total_cents=data["total_cents"],
        status=OrderStatus(data["status"]),
        created_at=datetime.fromisoformat(data["created_at"]),
    )
    assert order.status == OrderStatus.PENDING
