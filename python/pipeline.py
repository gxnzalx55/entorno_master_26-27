"""
Ejercicio · Pipeline bronce, plata y oro con pruebas de calidad
Almacenamiento, visualización y procesamiento de datos · Sesión 5

Un pipeline por lotes en pequeño:
  bronce   copia sin tocar de Northwind (PostgreSQL) y de los pedidos de la tienda web (CSV)
  plata    una fila por línea de pedido, limpia y unida; las filas malas van a cuarentena
  oro      ventas mensuales por país y categoría (Power BI) y características por cliente (IA)
  pruebas  ocho comprobaciones de calidad; si alguna falla, el pipeline lo dice

Uso, desde la carpeta python del entorno y con el entorno virtual activado:
  python pipeline.py            # ejecuta todo: bronce, plata, oro y pruebas
  python pipeline.py bronce     # o una sola etapa: bronce, plata, oro, pruebas
  python pipeline.py mirar oro/clientes     # ver columnas y primeras filas de un fichero

Las líneas marcadas con COMPLETA son las que tienes que escribir tú.
Los ficheros se guardan en datos/lakehouse dentro del entorno.
"""
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import duckdb

from utilidades import CARPETA_PROYECTO, consultar

LAKEHOUSE = CARPETA_PROYECTO / "datos" / "lakehouse"
BRONCE, PLATA, ORO = LAKEHOUSE / "bronce", LAKEHOUSE / "plata", LAKEHOUSE / "oro"
PEDIDOS_WEB = CARPETA_PROYECTO / "fuentes" / "pedidos_web.csv"
TABLAS_NORTHWIND = ["orders", "order_details", "customers", "products", "categories", "employees"]


# ---------------------------------------------------------------------------
#  Utilidades (no hace falta tocarlas)
# ---------------------------------------------------------------------------
def conexion():
    """DuckDB en memoria con una vista por cada fichero de bronce, plata y oro que ya exista."""
    con = duckdb.connect()
    for prefijo, carpeta in (("b", BRONCE), ("p", PLATA), ("o", ORO)):
        for fichero in sorted(carpeta.glob("*.parquet")):
            con.sql(f"CREATE VIEW {prefijo}_{fichero.stem} AS SELECT * FROM '{fichero.as_posix()}'")
    return con


def escribir(con, sql, destino: Path) -> int:
    """Escribe el resultado de una consulta en Parquet de forma atómica y devuelve el número de filas.

    Primero se escribe un fichero temporal y después se renombra: si algo falla a mitad,
    el fichero anterior sigue intacto. Y como se sobrescribe, ejecutar dos veces da lo mismo.
    """
    destino.parent.mkdir(parents=True, exist_ok=True)
    temporal = destino.with_suffix(".tmp")
    con.sql(f"COPY ({sql}) TO '{temporal.as_posix()}' (FORMAT parquet)")
    os.replace(temporal, destino)
    return con.sql(f"SELECT count(*) FROM '{destino.as_posix()}'").fetchone()[0]


def pendiente(valor, que):
    if valor is None:
        print(f"\n  >> Falta completar: {que}\n")
        sys.exit(1)
    return valor


# ---------------------------------------------------------------------------
#  Etapa 1 · Bronce: copiar sin tocar
# ---------------------------------------------------------------------------
def bronce():
    cargado_en = datetime.now().replace(microsecond=0)
    con = duckdb.connect()
    for tabla in TABLAS_NORTHWIND:
        df = consultar(f"SELECT * FROM {tabla}")
        df["_cargado_en"] = cargado_en
        df["_origen"] = f"postgres.northwind.{tabla}"
        con.register("df", df)
        n = escribir(con, "SELECT * FROM df", BRONCE / f"{tabla}.parquet")
        con.unregister("df")
        print(f"  bronce/{tabla + '.parquet':<24}{n:>6} filas")
    # El CSV se guarda tal cual, todo como texto: en bronce no se interpreta nada
    n = escribir(con, f"""
        SELECT *, TIMESTAMP '{cargado_en}' AS _cargado_en, 'fichero.pedidos_web.csv' AS _origen
        FROM read_csv('{PEDIDOS_WEB.as_posix()}', delim = ';', header = true, all_varchar = true)
    """, BRONCE / "pedidos_web.parquet")
    print(f"  bronce/{'pedidos_web.parquet':<24}{n:>6} filas")


# ---------------------------------------------------------------------------
#  Etapa 2 · Plata: limpiar, revisar y unir
# ---------------------------------------------------------------------------
# Los pedidos web con tipos correctos, sin duplicados y con el motivo de cuarentena (o NULL si la fila es buena)
WEB_REVISADO = """
    WITH sin_duplicados AS (
        SELECT DISTINCT pedido_web, fecha, cliente, producto, cantidad, precio_unitario, descuento
        FROM b_pedidos_web
    ),
    tipado AS (
        SELECT pedido_web                                    AS pedido,
               strptime(fecha, '%d/%m/%Y')::DATE             AS fecha,
               nullif(upper(trim(cliente)), '')              AS customer_id,
               producto::INTEGER                             AS product_id,
               cantidad::INTEGER                             AS cantidad,
               replace(precio_unitario, ',', '.')::DOUBLE    AS precio,
               replace(descuento, ',', '.')::DOUBLE          AS descuento
        FROM sin_duplicados
    )
    SELECT *,
           CASE
                WHEN customer_id IS NULL THEN 'cliente vacío'
                WHEN cantidad <= 0 THEN 'cantidad no positiva'
                WHEN product_id NOT IN (SELECT product_id FROM b_products) THEN 'producto inexistente'
            END AS motivo
    FROM tipado
"""

# B2. Las líneas web válidas (motivo IS NULL) con las mismas columnas y en el mismo orden que las de Northwind.
#     Los pedidos web no tienen empleado: employee_id va a NULL (NULL::INTEGER).
LINEAS_WEB = """
    SELECT 'web' AS origen, pedido, fecha, customer_id, product_id,
           NULL::INTEGER AS employee_id, cantidad, precio, descuento
    FROM web_revisado
    WHERE motivo IS NULL
"""

LINEAS_PEDIDO = """
    WITH web_revisado AS ({web_revisado}),
    northwind AS (
        SELECT 'northwind' AS origen, o.order_id::VARCHAR AS pedido, o.order_date AS fecha, o.customer_id,
               od.product_id, o.employee_id, od.quantity AS cantidad, od.unit_price AS precio,
               od.discount AS descuento
        FROM b_orders o
        JOIN b_order_details od ON od.order_id = o.order_id
    ),
    web AS ({lineas_web}),
    todas AS (
        SELECT * FROM northwind
        UNION ALL
        SELECT * FROM web
    )
    SELECT t.origen, t.pedido, t.fecha, t.customer_id, c.company_name, c.country,
           t.product_id, p.product_name, cat.category_name,
           coalesce(e.first_name || ' ' || e.last_name, 'Tienda web') AS empleado,
           t.cantidad, t.precio, t.descuento,
           t.precio * t.cantidad * (1 - t.descuento) AS importe
    FROM todas t
    JOIN b_customers c    ON c.customer_id = t.customer_id
    JOIN b_products p     ON p.product_id = t.product_id
    JOIN b_categories cat ON cat.category_id = p.category_id
    LEFT JOIN b_employees e ON e.employee_id = t.employee_id
"""


def plata():
    con = conexion()
    n = escribir(con, f"SELECT * FROM ({WEB_REVISADO}) WHERE motivo IS NOT NULL", PLATA / "cuarentena.parquet")
    print(f"  plata/{'cuarentena.parquet':<25}{n:>6} filas")
    sql = LINEAS_PEDIDO.format(web_revisado=WEB_REVISADO, lineas_web=pendiente(LINEAS_WEB, "B2, líneas web"))
    n = escribir(con, sql, PLATA / "lineas_pedido.parquet")
    print(f"  plata/{'lineas_pedido.parquet':<25}{n:>6} filas")


# ---------------------------------------------------------------------------
#  Etapa 3 · Oro: listo para usar
# ---------------------------------------------------------------------------
# C1. Ventas mensuales por país y categoría para Power BI: mes (primer día del mes), country,
#     category_name, pedidos (pedidos distintos), unidades (suma de cantidad) y facturacion (2 decimales).
#     Ordena por mes, país y categoría.
VENTAS_MENSUALES = """
    SELECT date_trunc('month', fecha)::DATE AS mes,
           country,
           category_name,
           count(DISTINCT pedido)   AS pedidos,
           sum(cantidad)            AS unidades,
           round(sum(importe), 2)   AS facturacion
    FROM p_lineas_pedido
    GROUP BY ALL
    ORDER BY mes, country, category_name
"""

# Características de cada cliente para un modelo (recencia, frecuencia e importe)
CLIENTES = """
    WITH referencia AS (SELECT max(fecha) + 1 AS dia FROM p_lineas_pedido),
    por_pedido AS (
        SELECT customer_id, company_name, country, pedido, min(fecha) AS fecha, sum(importe) AS importe
        FROM p_lineas_pedido
        GROUP BY ALL
    )
    SELECT customer_id, company_name, country,
           count(*)                                      AS pedidos,
           round(sum(importe), 2)                        AS facturacion,
           round(avg(importe), 2)                        AS ticket_medio,
           max(fecha)                                    AS ultima_compra,
           (SELECT dia FROM referencia) - max(fecha)     AS dias_sin_comprar
    FROM por_pedido
    GROUP BY ALL
    ORDER BY facturacion DESC
"""


def oro():
    con = conexion()
    n = escribir(con, pendiente(VENTAS_MENSUALES, "C1, ventas mensuales"), ORO / "ventas_mensuales.parquet")
    print(f"  oro/{'ventas_mensuales.parquet':<27}{n:>6} filas")
    n = escribir(con, CLIENTES, ORO / "clientes.parquet")
    print(f"  oro/{'clientes.parquet':<27}{n:>6} filas")


# ---------------------------------------------------------------------------
#  Etapa 4 · Pruebas de calidad
# ---------------------------------------------------------------------------
# Cada prueba es una consulta que cuenta las filas que están MAL. 0 = la prueba se supera.
PRUEBAS = {
    "bronce · orders llega completa (830 filas)":
        "SELECT CASE WHEN count(*) = 830 THEN 0 ELSE 1 END FROM b_orders",
    "plata · ninguna línea sin cliente":
        "SELECT count(*) FROM p_lineas_pedido WHERE customer_id IS NULL",
    "plata · cada producto aparece una vez por pedido":
        """SELECT count(*) FROM (SELECT origen, pedido, product_id FROM p_lineas_pedido
                                 GROUP BY ALL HAVING count(*) > 1)""",
    "plata · importe positivo":
        "SELECT count(*) FROM p_lineas_pedido WHERE importe <= 0",
    "plata · Northwind cuadra con bronce":
        """SELECT CASE WHEN abs((SELECT sum(importe) FROM p_lineas_pedido WHERE origen = 'northwind')
                               - (SELECT sum(unit_price * quantity * (1 - discount)) FROM b_order_details))
                            < 0.01 THEN 0 ELSE 1 END""",
    # D1. Integridad referencial: líneas de plata cuyo product_id no existe en b_products
    # D2. Conciliación: el total de oro/ventas_mensuales es igual al de plata (diferencia menor de 1 euro,
    #     porque oro redondea cada fila a 2 decimales)
    # D3. Unicidad: clientes que aparecen más de una vez en oro/clientes
    # COMPLETA las tres consultas
    # "oro · ...": """SELECT ...""",
    "plata · integridad: todo product_id existe en products":
        "SELECT count(*) FROM p_lineas_pedido WHERE product_id NOT IN (SELECT product_id FROM b_products)",
    "oro · ventas mensuales cuadran con plata":
        """SELECT CASE WHEN abs((SELECT sum(facturacion) FROM o_ventas_mensuales)
                               - (SELECT sum(importe) FROM p_lineas_pedido)) < 1 THEN 0 ELSE 1 END""",
    "oro · un solo registro por cliente":
        """SELECT count(*) FROM (SELECT customer_id FROM o_clientes
                                 GROUP BY customer_id HAVING count(*) > 1)""",
}


def pruebas():
    if len(PRUEBAS) < 8:
        pendiente(None, "D1, D2 y D3, las tres pruebas nuevas")
    con = conexion()
    fallos = 0
    for nombre, sql in PRUEBAS.items():
        malas = con.sql(sql).fetchone()[0]
        fallos += malas > 0
        print(f"  {'OK   ' if malas == 0 else 'FALLA'}  {nombre}" + (f"  ({malas})" if malas else ""))
    total, filas = con.sql("SELECT round(sum(importe), 2), count(*) FROM p_lineas_pedido").fetchone()
    print(f"\n  Resumen: {filas} líneas en plata · facturación {total:,.2f}")
    if fallos:
        print(f"  {fallos} prueba(s) fallan: revisa antes de publicar el oro.")
        sys.exit(1)


def mirar(nombre):
    """Muestra las columnas, el número de filas y las primeras filas de un fichero del lakehouse."""
    ruta = (LAKEHOUSE / nombre).with_suffix(".parquet")
    if not ruta.exists():
        print(f"No existe {ruta}. Ejemplos: bronce/pedidos_web, plata/cuarentena, oro/clientes")
        sys.exit(1)
    fichero = f"'{ruta.as_posix()}'"
    duckdb.sql(f"DESCRIBE SELECT * FROM {fichero}").show()
    print(f"{duckdb.sql(f'SELECT count(*) FROM {fichero}').fetchone()[0]} filas")
    duckdb.sql(f"SELECT * FROM {fichero} LIMIT 10").show(max_width=200)


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "mirar":
        mirar(sys.argv[2])
        sys.exit(0)
    etapas = {"bronce": bronce, "plata": plata, "oro": oro, "pruebas": pruebas}
    pedidas = sys.argv[1:] or list(etapas)
    if any(e not in etapas for e in pedidas):
        print(__doc__)
        sys.exit(1)
    for etapa in pedidas:
        inicio = time.perf_counter()
        print(f"\n== {etapa.upper()}")
        etapas[etapa]()
        print(f"  ({time.perf_counter() - inicio:.1f} s)")

# =====================================================================

# A1. orders 830 · order_details 2155 · customers 91 · products 77
#     categories 8 · employees 9 · pedidos_web 42

# A2. fecha, cantidad y precio_unitario son VARCHAR (texto).
#     En bronce no se interpreta nada: se copia la fuente tal cual para no
#     perder datos por formatos raros (dd/mm/aaaa, coma decimal) y se
#     limpia después, en plata.

# B3. Cuarentena: 3 filas
#       W-1015 -> cliente vacío
#       W-1004 -> cantidad no positiva (-3)
#       W-1009 -> producto inexistente (999)
#     plata/lineas_pedido: 2192 líneas (2155 Northwind + 37 web).
#     Cuadra: 40 líneas web sin duplicados = 37 válidas + 3 en cuarentena.

# C2. Tres clientes que más facturan: QUICK (111.036,31),
#     ERNSH (106.237,53) y SAVEA (104.719,20).
#     Días sin comprar CENTC: (rellena con la consulta)
#     FISSA y PARIS aparecen ahora porque sus pedidos vienen de la tienda
#     web, que se une a Northwind en plata.

# D4. Sí: las 8 pruebas en OK en las dos ejecuciones, y el resumen es
#     idéntico (2192 líneas · facturación 1.276.482,44).
#     No se duplican datos por la función escribir: guarda el resultado
#     en un fichero temporal y lo renombra con os.replace, de modo que
#     sobrescribe el fichero entero en vez de añadir filas. Si falla a
#     mitad, el fichero anterior queda intacto.