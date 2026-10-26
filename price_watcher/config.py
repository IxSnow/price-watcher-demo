"""Carga y validación de la configuración (YAML o JSON)."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import __user_agent_default__


class ConfigError(ValueError):
    """Error de configuración legible para el usuario."""


@dataclass
class ProductConfig:
    id: str
    name: str
    url: str
    price_selector: str
    stock_selector: str | None = None
    # Regex opcionales para interpretar el texto de stock.
    in_stock_regex: str = r"in stock|en stock|disponible|available"
    out_of_stock_regex: str = r"out of stock|agotado|sin stock|unavailable"
    quantity_regex: str = r"(\d+)\s*(?:available|disponible)"


@dataclass
class Settings:
    user_agent: str = __user_agent_default__
    request_delay_seconds: float = 2.0
    timeout_seconds: float = 20.0
    currency: str = "GBP"
    history_path: str = "data/history.csv"
    state_path: str = "data/state.json"


@dataclass
class Config:
    settings: Settings
    products: list[ProductConfig] = field(default_factory=list)

    @property
    def product_ids(self) -> list[str]:
        return [p.id for p in self.products]


def _load_raw(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    if not path.exists():
        raise ConfigError(f"No existe el archivo de configuración: {path}")
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        try:
            import yaml  # type: ignore
        except ImportError as exc:  # pragma: no cover - depende del entorno
            raise ConfigError(
                "Para leer configuración YAML instala PyYAML (pip install pyyaml) "
                "o usa un archivo .json."
            ) from exc
        data = yaml.safe_load(text)
    elif path.suffix.lower() == ".json":
        data = json.loads(text)
    else:
        raise ConfigError(
            f"Extensión no soportada: {path.suffix}. Usa .yaml, .yml o .json."
        )
    if not isinstance(data, dict):
        raise ConfigError("La configuración debe ser un objeto (mapa) en la raíz.")
    return data


def load_config(path: str | Path) -> Config:
    """Lee un archivo YAML/JSON y devuelve un objeto Config validado."""
    raw = _load_raw(path)

    settings_raw = raw.get("settings", {}) or {}
    if not isinstance(settings_raw, dict):
        raise ConfigError("'settings' debe ser un objeto.")
    settings = Settings(**{k: v for k, v in settings_raw.items() if k in Settings.__annotations__})

    products_raw = raw.get("products")
    if not products_raw or not isinstance(products_raw, list):
        raise ConfigError("Debes definir una lista 'products' con al menos un producto.")

    products: list[ProductConfig] = []
    seen_ids: set[str] = set()
    for i, item in enumerate(products_raw):
        if not isinstance(item, dict):
            raise ConfigError(f"El producto #{i + 1} debe ser un objeto.")
        for required in ("id", "name", "url", "price_selector"):
            if not item.get(required):
                raise ConfigError(
                    f"El producto #{i + 1} no tiene el campo obligatorio '{required}'."
                )
        pid = str(item["id"])
        if pid in seen_ids:
            raise ConfigError(f"Hay dos productos con el mismo id: '{pid}'.")
        seen_ids.add(pid)
        known = ProductConfig.__annotations__
        products.append(ProductConfig(**{k: v for k, v in item.items() if k in known}))

    return Config(settings=settings, products=products)


def resolve_relative_paths(config: Config, base_dir: str | Path) -> None:
    """Hace que history_path y state_path sean relativos al directorio base dado."""
    base = Path(base_dir)
    if not os.path.isabs(config.settings.history_path):
        config.settings.history_path = str(base / config.settings.history_path)
    if not os.path.isabs(config.settings.state_path):
        config.settings.state_path = str(base / config.settings.state_path)
