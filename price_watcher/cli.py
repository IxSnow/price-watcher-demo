"""Interfaz de línea de comandos de price-watcher."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .config import ConfigError, load_config, resolve_relative_paths
from .diff import detect_changes
from .notify import notify
from .scraper import check_all
from .storage import append_history, load_state, save_state


def _print_report(observations, changes) -> None:
    print(f"\n=== price-watcher {__version__} — resumen de la corrida ===")
    for obs in observations:
        if obs.error:
            print(f"  [ERROR] {obs.name}: {obs.error}")
            continue
        stock = "?" if obs.in_stock is None else ("en stock" if obs.in_stock else "AGOTADO")
        qty = "" if obs.quantity is None else f" ({obs.quantity} u.)"
        price = "?" if obs.price is None else f"{obs.currency} {obs.price:,.2f}"
        print(f"  {obs.name}: {price} — {stock}{qty}")
    print("\n--- Cambios respecto a la corrida anterior ---")
    if not changes:
        print("  Sin cambios.")
    else:
        for c in changes:
            print(f"  [{c.kind}] {c.name}: {c.detail}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="price-watcher",
        description="Monitor configurable de precio y stock para sitios públicos.",
    )
    parser.add_argument(
        "-c", "--config", default="config.example.yaml", help="archivo YAML/JSON de configuración"
    )
    parser.add_argument(
        "--no-notify", action="store_true", help="no enviar alertas (solo revisar y guardar)"
    )
    parser.add_argument(
        "--version", action="version", version=f"price-watcher {__version__}"
    )
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
    except ConfigError as exc:
        print(f"Error de configuración: {exc}", file=sys.stderr)
        return 2

    resolve_relative_paths(config, Path(args.config).resolve().parent)

    previous = load_state(config.settings.state_path)
    observations = check_all(config)
    changes = detect_changes(previous, observations)

    append_history(config.settings.history_path, observations)
    save_state(config.settings.state_path, observations)

    _print_report(observations, changes)

    if not args.no_notify:
        print("\n--- Alertas ---")
        for line in notify(changes):
            print(f"  {line}")

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
