"""Tests de parseo de precio y de interpretación de stock (sin red)."""
from price_watcher.config import ProductConfig
from price_watcher.scraper import _interpret_stock, parse_price


def test_parse_price_gbp():
    assert parse_price("£51.77") == 51.77


def test_parse_price_clp_miles_con_punto():
    assert parse_price("$1.299.990") == 1299990.0


def test_parse_price_coma_decimal():
    assert parse_price("1.234,56 €") == 1234.56


def test_parse_price_sin_numero():
    assert parse_price("sin precio") is None


def _product():
    return ProductConfig(
        id="x", name="X", url="http://e", price_selector="p", stock_selector="p"
    )


def test_stock_in_stock_con_cantidad():
    in_stock, qty = _interpret_stock("In stock (22 available)", _product())
    assert in_stock is True
    assert qty == 22


def test_stock_agotado():
    in_stock, qty = _interpret_stock("Out of stock", _product())
    assert in_stock is False


def test_stock_desconocido():
    in_stock, qty = _interpret_stock("algo raro", _product())
    assert in_stock is None
    assert qty is None
