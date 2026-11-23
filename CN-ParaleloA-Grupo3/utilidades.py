"""Utilidades sin Qt: formato de números y exportación a CSV."""
from __future__ import annotations

import csv
import math
from typing import Iterable, Sequence


def formato_valor(v: float, decimales: int = 9) -> str:
    """Número con ``decimales`` cifras decimales; «—» si no está definido."""
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "—"
    return f"{v:.{decimales}f}"


def formato_error_pct(v: float) -> str:
    """Error en %: decimal fijo si es «normal», científico si es muy pequeño."""
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "—"
    if v == 0:
        return "0"
    if abs(v) >= 1e-3:
        return f"{v:.6f}"
    return f"{v:.4e}"


def formato_adaptativo(v: float, decimales: int = 6) -> str:
    """Decimal fijo para valores «normales»; científico si |v| es muy pequeño o enorme.

    Útil para f(x), que puede valer 1e-9 cerca de la raíz y se vería como 0.000000.
    """
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "—"
    if v == 0:
        return "0"
    if 1e-3 <= abs(v) < 1e7:
        return f"{v:.{decimales}f}"
    return f"{v:.4e}"


def formato_cientifico(v: float, cifras: int = 4) -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "—"
    return f"{v:.{cifras}e}"


def exportar_csv(ruta: str, encabezados: Sequence[str], filas: Iterable[Sequence]) -> None:
    """Guarda una tabla en CSV (UTF-8 con BOM para que Excel respete los acentos).

    Los ``nan`` se escriben como celdas vacías. Se escriben los números sin
    redondear, no el texto formateado de la tabla.
    """
    with open(ruta, "w", newline="", encoding="utf-8-sig") as fh:
        escritor = csv.writer(fh)
        escritor.writerow(encabezados)
        for fila in filas:
            escritor.writerow(
                ["" if (isinstance(v, float) and math.isnan(v)) else v for v in fila]
            )
