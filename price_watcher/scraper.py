"""Descarga y parseo de páginas de producto públicas."""
from __future__ import annotations

import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

from .config import Config, ProductConfig

_PRICE_RE = re.compile(r"(-?\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?|\d+[.,]?\d*)")


@dataclass
class Observation:
    product_id: str
    name: str
    url: str
    checked_at: str
    price: float | None
    currency: str
    price_text: str | None
    in_stock: bool | None
    quantity: int | None
    error: str | None = None

    def as_row(self) -> dict[str, object]:
        return {
            "checked_at": self.checked_at,
            "product_id": self.product_id,
            "name": self.name,
            "price": "" if self.price is None else self.price,
            "currency": self.currency,
            "in_stock": "" if self.in_stock is None else int(self.in_stock),
            "quantity": "" if self.quantity is None else self.quantity,
            "url": self.url,
            "error": self.error or "",
        }


def parse_price(text: str) -> float | None:
    """Extrae un número de un texto de precio como '£51.77' o '$1.299.990'."""
    if not text:
        return None
    match = _PRICE_RE.search(text)
    if not match:
        return None
    raw = match.group(1)
    # Normaliza separadores: si hay coma y punto, el último es el decimal.
    if "," in raw and "." in raw:
        if raw.rfind(",") > raw.rfind("."):
            raw = raw.replace(".", "").replace(",", ".")
        else:
            raw = raw.replace(",", "")
    elif raw.count(",") == 1 and len(raw.split(",")[-1]) in (1, 2):
        raw = raw.replace(",", ".")
    else:
        raw = raw.replace(",", "")
    # Miles con punto (p.ej. 1.299.990) -> quita todos menos el último si parece decimal.
    if raw.count(".") > 1:
        raw = raw.replace(".", "")
    try:
        return float(raw)
    except ValueError:
        return None


def _interpret_stock(text: str, product: ProductConfig) -> tuple[bool | None, int | None]:
    if not text:
        return None, None
    low = text.lower()
    quantity = None
    qmatch = re.search(product.quantity_regex, low)
    if qmatch:
        try:
            quantity = int(qmatch.group(1))
        except (ValueError, IndexError):
            quantity = None
    if re.search(product.out_of_stock_regex, low):
        return False, quantity or 0
    if re.search(product.in_stock_regex, low):
        return True, quantity
    if quantity is not None:
        return quantity > 0, quantity
    return None, None


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def check_product(
    product: ProductConfig, config: Config, session: requests.Session
) -> Observation:
    headers = {"User-Agent": config.settings.user_agent, "Accept-Language": "es,en;q=0.8"}
    try:
        resp = session.get(
            product.url, headers=headers, timeout=config.settings.timeout_seconds
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        return Observation(
            product_id=product.id,
            name=product.name,
            url=product.url,
            checked_at=_now_iso(),
            price=None,
            currency=config.settings.currency,
            price_text=None,
            in_stock=None,
            quantity=None,
            error=f"descarga: {exc}",
        )

    soup = BeautifulSoup(resp.text, "html.parser")

    price_el = soup.select_one(product.price_selector)
    price_text = price_el.get_text(strip=True) if price_el else None
    price = parse_price(price_text or "")

    in_stock: bool | None = None
    quantity: int | None = None
    if product.stock_selector:
        stock_el = soup.select_one(product.stock_selector)
        stock_text = stock_el.get_text(" ", strip=True) if stock_el else ""
        in_stock, quantity = _interpret_stock(stock_text, product)

    error = None
    if price is None and price_text is None:
        error = f"no se encontró el selector de precio: {product.price_selector!r}"

    return Observation(
        product_id=product.id,
        name=product.name,
        url=product.url,
        checked_at=_now_iso(),
        price=price,
        currency=config.settings.currency,
        price_text=price_text,
        in_stock=in_stock,
        quantity=quantity,
        error=error,
    )


def check_all(config: Config) -> list[Observation]:
    """Revisa todos los productos respetando el delay configurado."""
    observations: list[Observation] = []
    with requests.Session() as session:
        for i, product in enumerate(config.products):
            if i > 0 and config.settings.request_delay_seconds > 0:
                time.sleep(config.settings.request_delay_seconds)
            observations.append(check_product(product, config, session))
    return observations
