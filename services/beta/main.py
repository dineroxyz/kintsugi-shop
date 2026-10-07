"""Managed demo service `beta` — the pricing dependency of alpha.

Deliberately tiny: a static price table behind one endpoint, with the
capture agent attached like any other managed service. It exists so that
alpha's outbound calls are real HTTP in live runs, not stubs.
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException

from libs.kintsugi_capture import CaptureMiddleware

PRICES = {
    "WIDGET": 25.0,
    "GADGET": 40.0,
    "SPROCKET": 9.5,
    "DOODAD": 3.25,
}

app = FastAPI(title="beta")
app.add_middleware(CaptureMiddleware, service="beta")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "beta"}


@app.get("/price/{sku}")
def price(sku: str) -> dict:
    if sku not in PRICES:
        raise HTTPException(status_code=404, detail=f"unknown sku {sku!r}")
    return {"sku": sku, "price": PRICES[sku]}


CATALOG_TAGS = {
    "WIDGET": ["metal", "small"],
    "GADGET": ["electronic"],
    "SPROCKET": [],
}

FX_RATES = {"USD": 1.0, "EUR": 0.92}


@app.get("/catalog/{sku}")
def catalog(sku: str) -> dict:
    if sku not in PRICES:
        raise HTTPException(status_code=404, detail=f"unknown sku {sku!r}")
    tags = CATALOG_TAGS.get(sku, [])
    return {"sku": sku, "price": PRICES[sku],
            "primary_tag": tags[0] if tags else None,
            "tag_count": len(tags), "tags": tags}


@app.get("/price/{sku}/converted")
def converted_price(sku: str, currency: str = "USD") -> dict:
    if sku not in PRICES:
        raise HTTPException(status_code=404, detail=f"unknown sku {sku!r}")
    rate = FX_RATES.get(currency)
    if rate is None:
        raise HTTPException(status_code=422,
                            detail=f"unsupported currency {currency!r}")
    return {"sku": sku, "currency": currency,
            "price": round(PRICES[sku] * rate, 2)}


BUNDLES = {
    "STARTER": ["WIDGET", "SPROCKET"],
    "PRO": ["GADGET", "WIDGET", "DOODAD"],
    "EMPTY": [],
}


@app.get("/bundles/{name}")
def bundle(name: str) -> dict:
    """Price a named bundle; leader is the first, priciest member."""
    if name not in BUNDLES:
        raise HTTPException(status_code=404, detail=f"unknown bundle {name!r}")
    members = BUNDLES[name]
    if not members:
        raise HTTPException(status_code=422, detail="bundle is empty")
    prices = sorted((PRICES[s] for s in members), reverse=True)
    return {"bundle": name, "size": len(members),
            "leader_price": prices[0], "total": round(sum(prices), 2)}


@app.get("/discounts/{tier}")
def tier_discount(tier: str) -> dict:
    """Look up a loyalty tier's discount basis points."""
    table = {"bronze": 100, "silver": 250, "gold": 500}
    if tier not in table:
        raise HTTPException(status_code=404, detail=f"unknown tier {tier!r}")
    bps = table[tier]
    return {"tier": tier, "bps": bps, "fraction": round(bps / 10000, 4)}
