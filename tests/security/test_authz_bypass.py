"""
Proves GET /orders/{id} cannot be used to view another session's order
by simply guessing/enumerating the order ID — a classic IDOR bug. Run
this BEFORE the ownership-check fix below — it should FAIL, since the
current endpoint has no ownership check at all.
"""


def test_cannot_view_another_sessions_order(client):
    client.post(
        "/cart/items",
        json={"session_id": "victim", "item_name": "Thing", "price_cents": 500},
    )
    checkout_response = client.post("/checkout", json={"session_id": "victim"})
    order_id = checkout_response.json()["order_id"]

    # "attacker" is a different session, simply guessing/enumerating order_id
    response = client.get(f"/orders/{order_id}", headers={"X-Session-Id": "attacker"})

    assert response.status_code == 403, (
        f"Expected 403 when a different session requests someone else's "
        f"order, got {response.status_code} — this is an IDOR "
        f"vulnerability."
    )


def test_owner_can_view_their_own_order(client):
    client.post(
        "/cart/items",
        json={"session_id": "owner", "item_name": "Thing", "price_cents": 500},
    )
    checkout_response = client.post("/checkout", json={"session_id": "owner"})
    order_id = checkout_response.json()["order_id"]

    response = client.get(f"/orders/{order_id}", headers={"X-Session-Id": "owner"})
    assert response.status_code == 200
