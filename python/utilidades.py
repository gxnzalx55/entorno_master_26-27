"""
Funciones comunes para todos los scripts de la práctica.

- conectar(): devuelve un engine de SQLAlchemy apuntando a la base de datos
  Northwind que levanta docker-compose. Lee usuario, contraseña y puerto del
  archivo .env que está en la carpeta raíz del proyecto.
- consultar(sql): ejecuta una consulta y devuelve un DataFrame de pandas.
- empaquetar / desempaquetar: guardan resultados esperados de los retos de
  forma compacta (no es cifrado: es solo para no ver la solución de un vistazo).
- mismo_resultado(): compara el resultado de un alumno con el esperado,
  tolerando pequeñas diferencias de redondeo en los números.
"""

import base64
import json
import math
import os
import zlib
from datetime import date, datetime, time
from decimal import Decimal
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

CARPETA_PROYECTO = Path(__file__).resolve().parent.parent
load_dotenv(CARPETA_PROYECTO / ".env")


def cadena_de_conexion() -> str:
    usuario = os.getenv("POSTGRES_USER", "postgres")
    clave = os.getenv("POSTGRES_PASSWORD", "postgres")
    host = os.getenv("POSTGRES_HOST", "localhost")
    puerto = os.getenv("POSTGRES_PORT", "5432")
    base = os.getenv("POSTGRES_DB", "northwind")
    # psycopg (versión 3) es el driver moderno de PostgreSQL para Python
    return f"postgresql+psycopg://{usuario}:{clave}@{host}:{puerto}/{base}"


def conectar():
    return create_engine(cadena_de_conexion())


def consultar(sql: str, engine=None) -> pd.DataFrame:
    propio = engine is None
    engine = engine or conectar()
    try:
        with engine.connect() as con:
            return pd.read_sql(text(sql), con)
    finally:
        if propio:
            engine.dispose()


# ---------------------------------------------------------------------------
#  Normalización y comparación de resultados
# ---------------------------------------------------------------------------

def _normaliza_valor(v):
    """Convierte cada celda a un tipo simple y comparable."""
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return None
    if v is pd.NaT:
        return None
    if isinstance(v, (Decimal, float, int)) and not isinstance(v, bool):
        return float(v)
    if hasattr(v, "item"):  # tipos numpy (int64, float64...)
        return _normaliza_valor(v.item())
    if isinstance(v, (datetime, date, time, pd.Timestamp)):
        return v.isoformat()[:10] if not isinstance(v, time) else v.isoformat()
    return str(v).strip()


def filas_normalizadas(df: pd.DataFrame) -> list:
    return [[_normaliza_valor(v) for v in fila] for fila in df.itertuples(index=False)]


def _clave_orden(fila):
    return [(0, "") if v is None else (1, f"{v:020.4f}") if isinstance(v, float) else (2, v) for v in fila]


def _valores_iguales(a, b) -> bool:
    if a is None or b is None:
        return a is None and b is None
    if isinstance(a, float) and isinstance(b, float):
        return math.isclose(a, b, rel_tol=1e-6, abs_tol=0.05)
    return a == b


def mismo_resultado(obtenido: list, esperado: list, importa_orden: bool) -> tuple[bool, str]:
    """Devuelve (acierto, mensaje con una pista de qué falla)."""
    if len(obtenido) != len(esperado):
        return False, f"Tu consulta devuelve {len(obtenido)} filas y se esperaban {len(esperado)}."
    if esperado and len(obtenido[0]) != len(esperado[0]):
        return False, f"Tu consulta devuelve {len(obtenido[0])} columnas y se esperaban {len(esperado[0])}."
    if not importa_orden:
        obtenido = sorted(obtenido, key=_clave_orden)
        esperado = sorted(esperado, key=_clave_orden)
    for fo, fe in zip(obtenido, esperado):
        if not all(_valores_iguales(a, b) for a, b in zip(fo, fe)):
            pista = "Mismo número de filas y columnas, pero algún valor no coincide."
            if importa_orden:
                pista += " Revisa también el ORDER BY: en este reto el orden cuenta."
            return False, pista
    return True, "¡Correcto!"


def empaquetar(obj) -> str:
    return base64.b64encode(zlib.compress(json.dumps(obj, ensure_ascii=False).encode())).decode()


def desempaquetar(texto: str):
    return json.loads(zlib.decompress(base64.b64decode(texto)).decode())
