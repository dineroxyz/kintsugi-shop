"""Managed demo service `alpha`.

A small order service, deliberately ordinary: FastAPI handlers, one outbound
dependency (the `beta` pricing service), shared in-memory state behind a
lock, and the Kintsugi capture agent as its only unusual component. This
tree is the CLEAN release; every study fault is injected into a copy of it
by the corpus injector, never committed here.
"""

from __future__ import annotations

import os
import threading

import httpx
from fastapi import FastAPI, HTTPException

from libs.kintsugi_capture import CaptureClient, CaptureMiddleware

BETA_URL = os.environ.get("BETA_URL", "http://localhost:8102")

app = FastAPI(title="alpha")
app.add_middleware(CaptureMiddleware, service="alpha")

_pricing = CaptureClient(timeout=5.0)

# naive in-memory state; realistic enough for a demo service
ORDERS: dict[int, dict] = {}
NEXT_ID = iter(range(1, 10**6))

STOCK: dict[str, list[str]] = {
    "WIDGET": [f"WIDGET-{i}" for i in range(50)],
    "GADGET": [f"GADGET-{i}" for i in range(50)],
}
_stock_lock = threading.Lock()

DISCOUNTS = {"SAVE10": 0.10, "SAVE20": 0.20}

ORDER_EVENTS: list[dict] = []


class _Notifier:
    """Order-event notifier; only present when NOTIFY_URL is configured."""

    def __init__(self, url: str):
        self.url = url
        self.sent: list[dict] = []

    def send(self, event: dict) -> None:
        self.sent.append(event)      # a real deployment would POST to url


_notifier = (_Notifier(os.environ["NOTIFY_URL"])
             if os.environ.get("NOTIFY_URL") else None)


def order_reference(order_id: int) -> str:
    return "ORD-" + format(order_id, "06d")


def discount_rate(code: str) -> float:
    """Named codes from the table; PCT<n> codes give n percent off."""
    if code.startswith("PCT") and code[3:].isdigit():
        return min(int(code[3:]), 90) / 100.0
    return DISCOUNTS.get(code, 0.0)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "alpha"}


@app.post("/orders")
def create_order(order: dict) -> dict:
    """Create an order, pricing each line through the beta service."""
    lines = order.get("lines", [])
    if not lines:
        raise HTTPException(status_code=422, detail="order has no lines")
    total = 0.0
    for line in lines:
        if "sku" not in line:
            raise HTTPException(status_code=422, detail="line missing sku")
        try:
            resp = _pricing.get(f"{BETA_URL}/price/{line['sku']}")
        except httpx.HTTPError:
            raise HTTPException(status_code=503, detail="pricing unavailable")
        if resp.status_code == 404:
            raise HTTPException(status_code=422,
                                detail=f"unknown sku {line['sku']!r}")
        resp.raise_for_status()
        price = resp.json()["price"]
        quantity = int(line.get("quantity", 1))
        total += price * quantity
    oid = next(NEXT_ID)
    ORDERS[oid] = {"id": oid, "first_sku": lines[0]["sku"],
                   "lines": lines, "total": round(total, 2)}
    ORDER_EVENTS.append({"order": oid, "total": ORDERS[oid]["total"]})
    if _notifier is not None:
        _notifier.send(ORDER_EVENTS[-1])
    return ORDERS[oid]


@app.get("/orders/{order_id}")
def get_order(order_id: int) -> dict:
    if order_id not in ORDERS:
        raise HTTPException(status_code=404, detail=f"no order {order_id}")
    return ORDERS[order_id]


@app.post("/orders/{order_id}/cancel")
def cancel_order(order_id: int) -> dict:
    order = ORDERS.pop(order_id, None)
    if order is None:
        raise HTTPException(status_code=404, detail=f"no order {order_id}")
    return {"id": order_id, "cancelled": True, "total": order["total"]}


@app.get("/quote")
def quote(sku: str, quantity: int = 1, code: str = "") -> dict:
    """Quote a price for a SKU with an optional discount code."""
    if quantity < 1:
        raise HTTPException(status_code=422, detail="quantity must be at least 1")
    try:
        resp = _pricing.get(f"{BETA_URL}/price/{sku}")
    except httpx.HTTPError:
        raise HTTPException(status_code=503, detail="pricing unavailable")
    if resp.status_code == 404:
        raise HTTPException(status_code=404, detail=f"unknown sku {sku!r}")
    resp.raise_for_status()
    unit = resp.json()["price"]
    rate = discount_rate(code)
    total = unit * quantity * (1 - rate)
    return {"sku": sku, "quantity": quantity,
            "per_unit": round(total / quantity, 2),
            "total": round(total, 2),
            "reference": "Q" + format(quantity, "03d")}


@app.get("/orders/{order_id}/discounted")
def discounted(order_id: int, code: str = "") -> dict:
    """Apply a discount code to an existing order."""
    if order_id not in ORDERS:
        raise HTTPException(status_code=404, detail=f"no order {order_id}")
    order = ORDERS[order_id]
    rate = discount_rate(code)
    discounted_total = order["total"] * (1 - rate)
    return {"id": order_id, "total": order["total"],
            "discounted": round(discounted_total, 2)}


@app.post("/restock/{sku}")
def restock(sku: str, payload: dict) -> dict:
    count = int(payload.get("count", 0))
    if count < 1:
        raise HTTPException(status_code=422, detail="count must be at least 1")
    with _stock_lock:
        STOCK[sku] = [f"{sku}-{i}" for i in range(count)]
    return {"sku": sku, "stocked": count}


@app.post("/reserve/{sku}")
def reserve(sku: str) -> dict:
    if sku not in STOCK:
        raise HTTPException(status_code=404, detail=f"unknown sku {sku!r}")
    with _stock_lock:
        if not STOCK[sku]:
            raise HTTPException(status_code=409, detail=f"{sku} out of stock")
        unit = STOCK[sku].pop()
    return {"sku": sku, "unit": unit}


@app.get("/summary")
def orders_summary(min_total: str = "0") -> dict:
    """Aggregate view; min_total arrives as text from dashboards."""
    try:
        floor = float(min_total)
    except ValueError:
        raise HTTPException(status_code=422, detail="min_total must be numeric")
    picked = [o for o in ORDERS.values() if o["total"] >= floor]
    grand = round(sum(o["total"] for o in picked), 2)
    return {"count": len(picked), "grand_total": grand}


@app.get("/orders/{order_id}/receipt")
def receipt(order_id: int) -> dict:
    if order_id not in ORDERS:
        raise HTTPException(status_code=404, detail=f"no order {order_id}")
    order = ORDERS[order_id]
    parts = [f"{line['sku']} x{int(line.get('quantity', 1))}"
             for line in order["lines"]]
    return {"id": order_id, "reference": order_reference(order_id),
            "text": "; ".join(parts)}


CARTS: dict[str, list[dict]] = {}
_cart_lock = threading.Lock()


@app.post("/carts/{cart_id}/items")
def add_to_cart(cart_id: str, item: dict) -> dict:
    """Append an item to a cart, creating the cart on first use."""
    if "sku" not in item:
        raise HTTPException(status_code=422, detail="item missing sku")
    with _cart_lock:
        cart = CARTS.setdefault(cart_id, [])
        cart.append({"sku": item["sku"],
                     "quantity": int(item.get("quantity", 1))})
        size = len(cart)
    return {"cart": cart_id, "items": size}


@app.get("/carts/{cart_id}")
def get_cart(cart_id: str) -> dict:
    if cart_id not in CARTS:
        raise HTTPException(status_code=404, detail=f"no cart {cart_id}")
    items = CARTS[cart_id]
    first = items[0]["sku"] if items else None
    return {"cart": cart_id, "size": len(items), "first_sku": first}


@app.post("/carts/{cart_id}/checkout")
def checkout(cart_id: str) -> dict:
    if cart_id not in CARTS:
        raise HTTPException(status_code=404, detail=f"no cart {cart_id}")
    items = CARTS.pop(cart_id)
    if not items:
        raise HTTPException(status_code=422, detail="cart is empty")
    total = 0.0
    for item in items:
        resp = _pricing.get(f"{BETA_URL}/price/{item['sku']}")
        if resp.status_code == 404:
            raise HTTPException(status_code=422,
                                detail=f"unknown sku {item['sku']!r}")
        total += resp.json()["price"] * item["quantity"]
    return {"cart": cart_id, "lines": len(items), "total": round(total, 2)}


@app.get("/carts/{cart_id}/tax")
def cart_tax(cart_id: str, rate_pct: int = 10) -> dict:
    if cart_id not in CARTS:
        raise HTTPException(status_code=404, detail=f"no cart {cart_id}")
    if rate_pct < 0 or rate_pct > 100:
        raise HTTPException(status_code=422, detail="rate_pct out of range")
    base = sum(item["quantity"] for item in CARTS[cart_id])
    return {"cart": cart_id, "units": base,
            "per_unit_tax": round(base and (base * rate_pct / 100) / base, 4)}
