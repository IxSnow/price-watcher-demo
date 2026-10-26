"""Tests de detección de cambios (sin red)."""
from price_watcher.diff import detect_changes
from price_watcher.scraper import Observation


def _obs(price, in_stock=True, pid="x"):
    return Observation(
        product_id=pid,
        name="X",
        url="http://e",
        checked_at="2026-01-01T00:00:00Z",
        price=price,
        currency="GBP",
        price_text=str(price),
        in_stock=in_stock,
        quantity=None,
    )


def test_nuevo_producto():
    changes = detect_changes({}, [_obs(10.0)])
    assert len(changes) == 1
    assert changes[0].kind == "new"


def test_baja_de_precio():
    prev = {"x": {"price": 10.0, "in_stock": True}}
    changes = detect_changes(prev, [_obs(8.0)])
    assert [c.kind for c in changes] == ["price_drop"]


def test_sube_de_precio():
    prev = {"x": {"price": 10.0, "in_stock": True}}
    changes = detect_changes(prev, [_obs(12.0)])
    assert [c.kind for c in changes] == ["price_rise"]


def test_cambio_de_stock():
    prev = {"x": {"price": 10.0, "in_stock": True}}
    changes = detect_changes(prev, [_obs(10.0, in_stock=False)])
    assert [c.kind for c in changes] == ["out_of_stock"]


def test_sin_cambios():
    prev = {"x": {"price": 10.0, "in_stock": True}}
    assert detect_changes(prev, [_obs(10.0)]) == []


def test_error_se_ignora():
    obs = _obs(None)
    obs.error = "descarga fallida"
    assert detect_changes({}, [obs]) == []
