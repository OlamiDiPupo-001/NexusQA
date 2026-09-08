"""
Layer 2 — API tests for the happy-path Order & Payment flow.
This is the baseline every later chaos/security test builds on.
"""


def test_add_item_to_cart(client):
    response = client.post(
        "/cart/items",
        json={"session_id": "s1", "item_name": "Widget", "price_cents": 1500},
    )
    assert response.status_code == 200
    assert response.json()["items"][0]["item_name"] == "Widget"


def test_checkout_creates_pending_order(client):
    client.post(
        "/cart/items",
        json={"session_id": "s2", "item_name": "Gadget", "price_cents": 2000},
    )
    response = client.post("/checkout", json={"session_id": "s2"})
    body = response.json()

    assert response.status_code == 200
    assert body["status"] == "pending"
    assert body["total_cents"] == 2000


def test_order_lookup_after_checkout(client):
    client.post(
        "/cart/items",
        json={"session_id": "s3", "item_name": "Gizmo", "price_cents": 500},
    )
    checkout_response = client.post("/checkout", json={"session_id": "s3"})
    order_id = checkout_response.json()["order_id"]

    lookup_response = client.get(f"/orders/{order_id}")
    assert lookup_response.status_code == 200
    assert lookup_response.json()["order_id"] == order_id


def test_order_not_found_returns_404(client):
    response = client.get("/orders/99999")
    assert response.status_code == 404
