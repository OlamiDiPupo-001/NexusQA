"""
Minimal cart logic. Deliberately in-memory (not persisted to DB) — the
cart is a v1 convenience layer that feeds into checkout; the checkout and
order records are what actually need durable, testable persistence.
"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

# In-memory store, keyed by a fake "session id" for simplicity in v1.
# Not thread-safe, not production code — intentionally minimal.
_carts: dict[str, list[dict]] = {}


class CartItem(BaseModel):
    session_id: str
    item_name: str
    price_cents: int


@router.post("/cart/items")
def add_item(item: CartItem):
    _carts.setdefault(item.session_id, []).append(
        {"item_name": item.item_name, "price_cents": item.price_cents}
    )
    return {"session_id": item.session_id, "items": _carts[item.session_id]}


def get_cart_total(session_id: str) -> int:
    return sum(i["price_cents"] for i in _carts.get(session_id, []))
