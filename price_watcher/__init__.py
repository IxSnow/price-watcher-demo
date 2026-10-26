"""price-watcher: monitor configurable de precio y stock para sitios públicos.

Paquete pequeño y sin dependencias exóticas que, a partir de un archivo de
configuración YAML o JSON, revisa el precio y el stock de una lista de
productos, guarda el histórico, detecta cambios y envía alertas.

Ver README.md para el uso completo.
"""

__version__ = "1.0.0"
__user_agent_default__ = (
    "price-watcher-demo/1.0 "
    "(+https://github.com/IxSnow/price-watcher-demo; monitor de portafolio)"
)
