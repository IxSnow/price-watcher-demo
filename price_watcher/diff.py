"""Comparación entre el estado anterior y la observación actual."""
from __future__ import annotations

from dataclasses import dataclass

from .scraper import Observation


@dataclass
class Change:
    product_id: str
    name: str
    url: str
    kind: str  # price_drop | price_rise | back_in_stock | out_of_stock | new
    detail: str


def _fmt(value: float | None, currency: str) -> str:
    if value is None:
        return "?"
    return f"{currency} {value:,.2f}"


def detect_changes(
    previous: dict[str, dict], observations: list[Observation]
) -> list[Change]:
    """Devuelve la lista de cambios relevantes respecto al estado anterior."""
    changes: list[Change] = []
    for obs in observations:
        if obs.error is not None:
            continue
        prev = previous.get(obs.product_id)
        if prev is None:
            changes.append(
                Change(
                    obs.product_id,
                    obs.name,
                    obs.url,
                    "new",
                    f"Nuevo producto monitoreado a {_fmt(obs.price, obs.currency)}.",
                )
            )
            continue

        old_price = prev.get("price")
        if old_price is not None and obs.price is not None and obs.price != old_price:
            kind = "price_drop" if obs.price < old_price else "price_rise"
            arrow = "bajó" if obs.price < old_price else "subió"
            delta = obs.price - old_price
            changes.append(
                Change(
                    obs.product_id,
                    obs.name,
                    obs.url,
                    kind,
                    f"El precio {arrow} de {_fmt(old_price, obs.currency)} a "
                    f"{_fmt(obs.price, obs.currency)} ({delta:+,.2f}).",
                )
            )

        old_stock = prev.get("in_stock")
        if old_stock is not None and obs.in_stock is not None and obs.in_stock != old_stock:
            if obs.in_stock:
                changes.append(
                    Change(
                        obs.product_id,
                        obs.name,
                        obs.url,
                        "back_in_stock",
                        "Volvió a haber stock.",
                    )
                )
            else:
                changes.append(
                    Change(
                        obs.product_id,
                        obs.name,
                        obs.url,
                        "out_of_stock",
                        "Se quedó sin stock.",
                    )
                )
    return changes
