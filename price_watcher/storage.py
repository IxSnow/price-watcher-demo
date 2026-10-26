"""Persistencia del histórico (CSV) y del último estado (JSON)."""
from __future__ import annotations

import csv
import json
from pathlib import Path

from .scraper import Observation

_CSV_FIELDS = [
    "checked_at",
    "product_id",
    "name",
    "price",
    "currency",
    "in_stock",
    "quantity",
    "url",
    "error",
]


def append_history(path: str, observations: list[Observation]) -> None:
    file = Path(path)
    file.parent.mkdir(parents=True, exist_ok=True)
    write_header = not file.exists()
    with file.open("a", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=_CSV_FIELDS)
        if write_header:
            writer.writeheader()
        for obs in observations:
            writer.writerow(obs.as_row())


def load_state(path: str) -> dict[str, dict]:
    file = Path(path)
    if not file.exists():
        return {}
    try:
        return json.loads(file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_state(path: str, observations: list[Observation]) -> None:
    file = Path(path)
    file.parent.mkdir(parents=True, exist_ok=True)
    state = {
        obs.product_id: {
            "name": obs.name,
            "url": obs.url,
            "price": obs.price,
            "currency": obs.currency,
            "in_stock": obs.in_stock,
            "quantity": obs.quantity,
            "checked_at": obs.checked_at,
        }
        for obs in observations
        if obs.error is None
    }
    file.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
