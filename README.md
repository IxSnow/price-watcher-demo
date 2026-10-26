# price-watcher

Monitor **configurable** de precio y stock para páginas de producto públicas.
A partir de un archivo YAML (o JSON) revisa una lista de productos, guarda el
histórico, detecta cambios respecto a la corrida anterior y envía una alerta
(email por SMTP y/o webhook/ntfy) **solo cuando algo cambia**.

Pensado para correr una vez al día de forma programada (cron, systemd timer o
GitHub Actions) y avisarte al celular cuando baja un precio o vuelve el stock.

> Demo de portafolio. El ejemplo apunta a
> [books.toscrape.com](https://books.toscrape.com), un sitio público creado
> expresamente para practicar scraping. **No** incluye secretos ni se hace
> pasar por un navegador.

## Qué muestra esta demo

- Scraping configurable por **selectores CSS** (sirve para casi cualquier sitio
  cambiando solo el config, sin tocar el código).
- Histórico en CSV + estado en JSON para comparar entre corridas.
- Detección de cambios: baja/sube de precio, se agota, vuelve el stock.
- Alertas por **email (SMTP)** y **webhook/ntfy**, configuradas por variables
  de entorno (nunca en el repo).
- **User-Agent honesto e identificable** (no imita a Chrome), pausa entre
  peticiones y solo datos públicos.
- Tests con `pytest` y licencia MIT.

## Cómo funciona

```
config.yaml ──▶ scraper (requests + BeautifulSoup) ──▶ observaciones
                                                          │
                     ┌────────────────────────────────────┤
                     ▼                                     ▼
            histórico (data/history.csv)        estado previo (data/state.json)
                     │                                     │
                     └──────────────▶ diff ◀───────────────┘
                                       │
                           ¿hay cambios? ──sí──▶ alertas (email / webhook / ntfy)
                                       │
                                       └──no──▶ nada (solo guarda el histórico)
```

## Instalación

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env     # completa SOLO si quieres alertas
```

## Uso

```bash
# Revisa los productos del config, guarda histórico y manda alertas si hay cambios
python -m price_watcher.cli -c config.example.yaml

# Solo revisar y guardar, sin enviar alertas
python -m price_watcher.cli -c config.example.yaml --no-notify
```

### Configuración

Cada producto define su URL y los selectores CSS del precio y del stock:

```yaml
settings:
  user_agent: "price-watcher-demo/1.0 (+https://github.com/IxSnow/price-watcher-demo; monitor de portafolio)"
  request_delay_seconds: 2.0
  currency: "GBP"

products:
  - id: "light-in-the-attic"
    name: "A Light in the Attic"
    url: "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
    price_selector: "p.price_color"
    stock_selector: "p.availability"
```

Para otro sitio, basta cambiar `url`, `price_selector` y `stock_selector`
(y, si hace falta, los regex de stock). Ver `config.example.yaml`.

### Alertas (variables de entorno)

Se configuran en `.env` (ver `.env.example`). Si faltan, esa alerta se omite
y la corrida igual guarda el histórico:

- **Email:** `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`,
  `ALERT_EMAIL_FROM`, `ALERT_EMAIL_TO`.
- **Webhook genérico** (Slack/Discord/Make/n8n...): `WEBHOOK_URL`
  (recibe `POST` con `{"title", "message"}`).
- **ntfy** (push al celular): `NTFY_SERVER`, `NTFY_TOPIC`.

### Programación diaria (ejemplo con cron)

```cron
# Todos los días a las 09:00
0 9 * * * cd /ruta/a/price-watcher && .venv/bin/python -m price_watcher.cli -c config.example.yaml >> data/cron.log 2>&1
```

## Salida de ejemplo (corrida real contra books.toscrape.com)

Primera corrida (todo nuevo):

```
=== price-watcher 1.0.0 — resumen de la corrida ===
  A Light in the Attic: GBP 51.77 — en stock (22 u.)
  Tipping the Velvet: GBP 53.74 — en stock (20 u.)
  Soumission: GBP 50.10 — en stock (20 u.)
  Sharp Objects: GBP 47.82 — en stock (20 u.)

--- Cambios respecto a la corrida anterior ---
  [new] A Light in the Attic: Nuevo producto monitoreado a GBP 51.77.
  ...
```

Corrida posterior con un cambio detectado y la alerta enviada a un webhook:

```
--- Cambios respecto a la corrida anterior ---
  [price_drop] A Light in the Attic: El precio bajó de GBP 55.00 a GBP 51.77 (-3.23).
  [back_in_stock] Soumission: Volvió a haber stock.

--- Alertas ---
  email omitido (faltan SMTP_HOST o ALERT_EMAIL_TO)
  send_webhook: enviado
```

Cuerpo JSON que recibió el webhook en esa corrida:

```json
{
  "title": "price-watcher: 2 cambio(s) detectado(s)",
  "message": "Se detectaron los siguientes cambios:\n\n- [price_drop] A Light in the Attic: El precio bajó de GBP 55.00 a GBP 51.77 (-3.23).\n  https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html\n- [back_in_stock] Soumission: Volvió a haber stock."
}
```

El histórico y el estado reales de estas corridas están en
[`examples/`](examples/) (`sample_history.csv`, `sample_state.json`) junto con
los transcripts completos (`sample_run_*.txt`).

## Tests

```bash
pip install -r requirements-dev.txt
pytest -q          # 13 tests (parseo de precio, stock y detección de cambios)
```

## Uso responsable

- Solo **datos públicos**; sin logins ni captchas.
- **User-Agent honesto** que te identifica y enlaza al repositorio.
- Pausa configurable entre peticiones para no sobrecargar el sitio.
- Respeta los términos de uso y el `robots.txt` del sitio objetivo.

## Licencia

MIT — ver [LICENSE](LICENSE).
