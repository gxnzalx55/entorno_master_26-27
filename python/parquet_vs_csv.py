"""
Ejercicio 2 · CSV frente a Parquet
Almacenamiento, visualización y procesamiento de datos · Sesión 4

Mide con tus propios datos lo que vimos en la presentación: tamaño, lectura de
columnas, estadísticas por grupo de filas y DuckDB.

Antes de empezar:
  - La tabla ventas_grandes tiene que existir (Ejercicio 1, crear_ventas_grandes.sql).
  - Entorno virtual activado y DuckDB instalado:  pip install duckdb

Uso, desde la carpeta python del entorno (una parte cada vez):
  python parquet_vs_csv.py a     # exportar y comparar tamaños
  python parquet_vs_csv.py b     # medir lecturas
  python parquet_vs_csv.py c     # mirar dentro del Parquet
  python parquet_vs_csv.py d     # DuckDB

Las líneas marcadas con COMPLETA son las que tienes que escribir tú.
Los ficheros se guardan en la carpeta datos/s4 del entorno.
"""
import sys
import time
from pathlib import Path

import duckdb
import pandas as pd
import pyarrow.parquet as pq

from utilidades import CARPETA_PROYECTO, consultar

DATOS = CARPETA_PROYECTO / "datos" / "s4"
CSV = DATOS / "ventas.csv"
PARQUET = DATOS / "ventas.parquet"
PARQUET_ORDENADO = DATOS / "ventas_ordenado.parquet"
PARTICIONADO = DATOS / "ventas_por_anio"
FILAS_POR_GRUPO = 200_000


# ---------------------------------------------------------------------------
#  Utilidades (no hace falta tocarlas)
# ---------------------------------------------------------------------------
def cronometrar(funcion, repeticiones=3):
    """Ejecuta la función varias veces y devuelve (resultado, mejor tiempo en segundos)."""
    mejor, resultado = float("inf"), None
    for _ in range(repeticiones):
        inicio = time.perf_counter()
        resultado = funcion()
        mejor = min(mejor, time.perf_counter() - inicio)
    return resultado, mejor


def mb(ruta: Path) -> float:
    if ruta.is_dir():
        return sum(f.stat().st_size for f in ruta.rglob("*.parquet")) / 1e6
    return ruta.stat().st_size / 1e6


def pendiente(valor, que):
    if valor is None:
        print(f"\n  >> Falta completar: {que}\n")
        sys.exit(1)
    return valor


def comprobar_ficheros():
    if not (CSV.exists() and PARQUET.exists() and PARQUET_ORDENADO.exists()):
        print("Primero ejecuta la parte A:  python parquet_vs_csv.py a")
        sys.exit(1)


# ---------------------------------------------------------------------------
#  Parte A · Exportar y comparar tamaños
# ---------------------------------------------------------------------------
def parte_a():
    DATOS.mkdir(parents=True, exist_ok=True)
    print("Leyendo ventas_grandes de PostgreSQL (unos segundos)...")
    ventas, t = cronometrar(lambda: consultar("SELECT * FROM ventas_grandes ORDER BY venta_id"), 1)
    print(f"  {len(ventas):,} filas leídas en {t:.1f} s")
    print(ventas.dtypes.to_string(), "\n")

    ventas.to_csv(CSV, index=False)
    ventas.to_parquet(PARQUET, index=False, row_group_size=FILAS_POR_GRUPO)

    # A1. Guarda un segundo Parquet con las ventas ordenadas por cliente_id y fecha,
    #     con el mismo tamaño de grupo de filas (row_group_size=FILAS_POR_GRUPO).
    # COMPLETA (1 línea)
    ventas.sort_values(["cliente_id", "fecha"]).to_parquet(PARQUET_ORDENADO, index=False, row_group_size=FILAS_POR_GRUPO)
    if not PARQUET_ORDENADO.exists():
        pendiente(None, "A1, guardar el Parquet ordenado")

    print(f"{'Fichero':<28}{'MB':>8}{'Veces menor que el CSV':>26}")
    for ruta in (CSV, PARQUET, PARQUET_ORDENADO):
        print(f"{ruta.name:<28}{mb(ruta):>8.1f}{mb(CSV) / mb(ruta):>26.1f}")


# ---------------------------------------------------------------------------
#  Parte B · Medir lecturas
# ---------------------------------------------------------------------------
def parte_b():
    comprobar_ficheros()
    # B1. Completa las cuatro lecturas con pandas. Cada una es una función sin
    #     argumentos (lambda) que devuelve un DataFrame.
    #     Pista: pd.read_csv(..., usecols=[...]) y pd.read_parquet(..., columns=[...])
    lecturas = {
        "CSV, tabla entera": lambda: pd.read_csv(CSV),
        "Parquet, tabla entera": lambda: pd.read_parquet(PARQUET),
        "CSV, solo importe": lambda: pd.read_csv(CSV, usecols=["importe"]),
        "Parquet, solo importe": lambda: pd.read_parquet(PARQUET, columns=["importe"]),
    }
    tiempos = {}
    for nombre, funcion in lecturas.items():
        df, t = cronometrar(pendiente(funcion, f"B1, lectura «{nombre}»"))
        tiempos[nombre] = t
        print(f"{nombre:<24}{t:>8.3f} s   ({len(df.columns)} columnas)")
    print(f"\nTabla entera: Parquet {tiempos['CSV, tabla entera'] / tiempos['Parquet, tabla entera']:.1f} veces "
          "más rápido")
    print(f"Una columna:  Parquet {tiempos['CSV, solo importe'] / tiempos['Parquet, solo importe']:.1f} veces "
          "más rápido")


# ---------------------------------------------------------------------------
#  Parte C · Mirar dentro del Parquet
# ---------------------------------------------------------------------------
def rangos_cliente(ruta: Path):
    """Devuelve una lista con (mínimo, máximo) de cliente_id en cada grupo de filas."""
    meta = pq.ParquetFile(ruta).metadata
    columna = meta.schema.names.index("cliente_id")
    # C1. Recorre los grupos de filas y devuelve [(mínimo, máximo), ...] de cliente_id.
    #     Pista: meta.num_row_groups, meta.row_group(i).column(columna).statistics.min / .max
    return [
        (
            meta.row_group(i).column(columna).statistics.min,
            meta.row_group(i).column(columna).statistics.max,
        )
        for i in range(meta.num_row_groups)
    ]


def parte_c():
    comprobar_ficheros()
    meta = pq.ParquetFile(PARQUET).metadata
    print(f"Filas: {meta.num_rows:,} · grupos de filas: {meta.num_row_groups} · columnas: {meta.num_columns}")
    grupo = meta.row_group(0)
    print(f"\nGrupo 1 ({grupo.num_rows:,} filas):")
    print(f"{'columna':<12}{'compresión':<12}{'KB':>8}{'mínimo':>14}{'máximo':>14}")
    for i in range(grupo.num_columns):
        c = grupo.column(i)
        print(f"{c.path_in_schema:<12}{c.compression:<12}{c.total_compressed_size / 1e3:>8.0f}"
              f"{str(c.statistics.min or 0):>14}{str(c.statistics.max):>14}")

    for ruta in (PARQUET, PARQUET_ORDENADO):
        rangos = pendiente(rangos_cliente(ruta), "C1, función rangos_cliente")
        print(f"\n{ruta.name}: cliente_id (mínimo, máximo) en cada grupo")
        print("  " + "  ".join(f"{a}-{b}" for a, b in rangos))
        # C2. ¿En cuántos grupos podría estar el cliente 42? (mínimo <= 42 <= máximo)
        posibles = sum(1 for a, b in rangos if a <= 42 <= b)        
        print(f"  El cliente 42 puede estar en {pendiente(posibles, 'C2, contar grupos')} de {len(rangos)} grupos")


# ---------------------------------------------------------------------------
#  Parte D · DuckDB
# ---------------------------------------------------------------------------
def parte_d():
    comprobar_ficheros()
    con = duckdb.connect()

    def medir(titulo, sql):
        filas, t = cronometrar(lambda: con.sql(sql).fetchall(), 5)
        print(f"{titulo:<44}{t * 1000:>8.1f} ms   {filas[:3]}")

    # D1. Número de ventas e importe total del cliente 42 desde el 1 de enero de 2024.
    #     Escribe la consulta con {fichero} en el FROM: se ejecutará sobre los dos Parquet.
    #     Pista: en DuckDB, FROM 'ruta/fichero.parquet' y DATE '2024-01-01'
    cliente_42 = """
        SELECT count(*) AS ventas, sum(importe) AS importe_total
        FROM '{fichero}'
        WHERE cliente_id = 42 AND fecha >= DATE '2024-01-01'
    """
    pendiente(cliente_42, "D1, consulta del cliente 42")
    medir("D1 · cliente 42, Parquet sin ordenar", cliente_42.format(fichero=PARQUET.as_posix()))
    medir("D1 · cliente 42, Parquet ordenado", cliente_42.format(fichero=PARQUET_ORDENADO.as_posix()))

    # D2. Los 3 clientes que más facturan: cliente_id, número de ventas y facturación.
    #     Se ejecutará sobre el Parquet y sobre el CSV (read_csv_auto).
    top3 = """
        SELECT cliente_id, count(*) AS ventas, sum(importe) AS facturacion
        FROM {origen}
        GROUP BY cliente_id
        ORDER BY facturacion DESC
        LIMIT 3
    """
    pendiente(top3, "D2, consulta de los 3 mejores clientes")
    medir("D2 · top 3 clientes, Parquet", top3.format(origen=f"'{PARQUET.as_posix()}'"))
    medir("D2 · top 3 clientes, CSV", top3.format(origen=f"read_csv_auto('{CSV.as_posix()}')"))

    # D3. Particionado por año: una carpeta anio=2020, anio=2021...
    con.sql(f"""
        COPY (SELECT *, year(fecha) AS anio FROM '{PARQUET.as_posix()}')
        TO '{PARTICIONADO.as_posix()}' (FORMAT parquet, PARTITION_BY (anio), OVERWRITE_OR_IGNORE)
    """)
    for carpeta in sorted(PARTICIONADO.iterdir()):
        print(f"  {carpeta.name}/  {mb(carpeta):.1f} MB")
    #     Facturación de 2024 de dos formas:
    #     - sobre la tabla particionada, filtrando por la columna anio
    #       (FROM read_parquet('.../*/*.parquet', hive_partitioning = true))
    #     - sobre el fichero único, filtrando con year(fecha) = 2024
    particionada = f"""
        SELECT sum(importe) AS facturacion
        FROM read_parquet('{PARTICIONADO.as_posix()}/*/*.parquet', hive_partitioning = true)
        WHERE anio = 2024
    """
    unico = f"""
        SELECT sum(importe) AS facturacion
        FROM '{PARQUET.as_posix()}'
        WHERE year(fecha) = 2024
    """
    medir("D3 · 2024, particionado", pendiente(particionada, "D3, consulta sobre la tabla particionada"))
    medir("D3 · 2024, fichero único", pendiente(unico, "D3, consulta sobre el fichero único"))
    plan = con.sql("EXPLAIN ANALYZE " + particionada).fetchall()[0][1]
    print("\nEn el plan de la consulta particionada:")
    for linea in plan.splitlines():
        if "Scanning Files" in linea or "Total Files Read" in linea:
            print("  " + linea.strip(" │"))


if __name__ == "__main__":
    partes = {"a": parte_a, "b": parte_b, "c": parte_c, "d": parte_d}
    if len(sys.argv) != 2 or sys.argv[1].lower() not in partes:
        print(__doc__)
        sys.exit(1)
    partes[sys.argv[1].lower()]()

# =====================================================================
#  MIS CIFRAS (mi ordenador)
# =====================================================================
#  Tamaño CSV / Parquet / Parquet ordenado ........ 63,8 / 23,4 / 21,5 MB
#  Leer la tabla entera: CSV / Parquet ............ 0,528 / 0,039 s
#  Leer solo importe: CSV / Parquet ............... 0,246 / 0,009 s
#  Grupos con el cliente 42: sin ordenar / ordenado  10 / 1
#  D1 · cliente 42: sin ordenar / ordenado ........ 4,6 / 2,0 ms
#  D2 · top 3: Parquet / CSV ...................... 4,2 / 97,6 ms
#  D3 · 2024: particionado / fichero único ........ 2,8 / 7,2 ms
# =====================================================================

# A2. El Parquet ocupa 2,7 veces menos que el CSV (3,0 el ordenado).
#     Al ordenar, valores iguales quedan juntos en cada columna y la
#     codificación y la compresión funcionan mejor.

# B2. Tabla entera: Parquet 13,5 veces más rápido. Una columna: 26,3 veces.
#     Con una columna Parquet lee solo los bytes de esa columna; el CSV
#     tiene que recorrer todo el texto de cada línea igualmente.

# C3. Grupos a leer para el cliente 42: 10 de 10 sin ordenar, 1 de 10
#     ordenado (cada grupo cubre un tramo estrecho de cliente_id).
#     cliente_id ocupa solo 177 KB porque tiene 91 valores distintos:
#     codificación por diccionario + compresión.

# D1. Coincide con PostgreSQL: 4407 ventas, 1121260,50. Sin ordenar 4,6 ms,
#     ordenado 2,0 ms: con el ordenado DuckDB descarta 9 de 10 grupos por
#     sus estadísticas mínimo/máximo.

# D2. Parquet 4,2 ms frente a CSV 97,6 ms (unas 23 veces menos): Parquet lee
#     solo dos columnas. La vista de PostgreSQL tardó 585,6 ms (unas 140
#     veces más). Los resultados coinciden (cliente 35: 22374 ventas).

# D3. El plan lee 1 de 5 ficheros (anio=2024). La particionada es más
#     rápida (2,8 frente a 7,2 ms): descarta los otros 4 sin abrirlos.