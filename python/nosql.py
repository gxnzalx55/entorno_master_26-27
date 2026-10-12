"""
Ejercicio · Redis y MongoDB sobre Northwind
Almacenamiento, visualización y procesamiento de datos · Sesión 6

  a  Redis como caché: la facturación por cliente de ventas_grandes (sesión 4), de PostgreSQL o de Redis
  b  Redis para contar y ordenar: un contador y el ranking de productos con un conjunto ordenado
  c  MongoDB: los 830 pedidos como documentos con sus líneas dentro, consultas y una agregación
  d  Eventos: los pedidos de la tienda web (sesión 5) llegan a un stream y un consumidor actualiza el ranking

Antes de empezar, en la carpeta del entorno:
  docker compose --profile redis --profile mongo up -d
  python python/comprobar_nosql.py        (tiene que decir ✅ en MongoDB y en Redis)

Uso, desde la carpeta python del entorno y con el entorno virtual activado:
  python nosql.py a        (o b, c, d; las partes se pueden repetir las veces que quieras)

Las líneas marcadas con COMPLETA son las que tienes que escribir tú.
"""
import csv
import os
import sys
import time
from datetime import datetime

import redis
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from sqlalchemy.exc import OperationalError

from utilidades import CARPETA_PROYECTO, consultar  # también carga el fichero .env

PEDIDOS_WEB = CARPETA_PROYECTO / "fuentes" / "pedidos_web.csv"


# ---------------------------------------------------------------------------
#  Conexiones (no hace falta tocarlas)
# ---------------------------------------------------------------------------
def conectar_redis():
    r = redis.Redis(host="localhost", port=int(os.getenv("REDIS_PORT", "6379")), decode_responses=True)
    r.ping()
    return r


def conectar_mongo():
    url = (f"mongodb://{os.getenv('MONGO_USER', 'root')}:{os.getenv('MONGO_PASSWORD', 'example1')}"
           f"@localhost:{os.getenv('MONGO_PORT', '27017')}/")
    cliente = MongoClient(url, serverSelectionTimeoutMS=3000)
    cliente.admin.command("ping")
    return cliente["northwind"]


def ms(inicio):
    return (time.perf_counter() - inicio) * 1000


def pendiente(valor, que):
    if valor is None:
        print(f"\n  >> Falta completar: {que}\n")
        sys.exit(1)
    return valor


# ---------------------------------------------------------------------------
#  Parte A · Redis como caché
# ---------------------------------------------------------------------------
SQL_FACTURACION = "SELECT cliente_id, sum(importe) AS facturacion FROM ventas_grandes GROUP BY cliente_id"
CLAVE_CACHE = "cache:facturacion_por_cliente"
SEGUNDOS_CACHE = 300


def facturacion_cliente(r, cliente_id):
    """Patrón cache-aside: se mira primero en Redis; si no está, se calcula en PostgreSQL y se guarda."""
    if not r.exists(CLAVE_CACHE):                                   # fallo de caché
        df = consultar(SQL_FACTURACION)                             # unos 200 ms: lee 2 millones de filas
        # A1. Guarda la facturación de los 91 clientes en un hash de Redis (campo = cliente_id, valor = facturación)
        #     y ponle una caducidad de SEGUNDOS_CACHE segundos.
        #     Pista: r.hset(CLAVE_CACHE, mapping={...}) y r.expire(CLAVE_CACHE, SEGUNDOS_CACHE)
        # COMPLETA (2 líneas)
        # (escribe aquí tus 2 líneas)
    valor = r.hget(CLAVE_CACHE, str(cliente_id))                    # acierto de caché: menos de 1 ms
    return pendiente(valor and float(valor), "A1, guardar en la caché")


def parte_a():
    r = conectar_redis()
    r.delete(CLAVE_CACHE)                                           # empezamos con la caché vacía
    for intento in (1, 2, 3):
        inicio = time.perf_counter()
        valor = facturacion_cliente(r, 35)
        print(f"  Intento {intento}: cliente 35 → {valor:,.2f}  ({ms(inicio):7.2f} ms)")
    print(f"\n  La caché caduca dentro de {r.ttl(CLAVE_CACHE)} s · campos en el hash: {r.hlen(CLAVE_CACHE)}")


# ---------------------------------------------------------------------------
#  Parte B · Redis para contar y ordenar
# ---------------------------------------------------------------------------
CLAVE_RANKING = "ranking:productos_unidades"


def parte_b():
    r = conectar_redis()
    # Un contador: INCR es atómico, aunque mil usuarios lo incrementen a la vez
    r.delete("visitas:producto:59")
    for _ in range(3):
        r.incr("visitas:producto:59")
    print(f"  Visitas a la ficha del producto 59: {r.get('visitas:producto:59')}")

    # El ranking: un conjunto ordenado (sorted set) con las unidades vendidas de cada producto en Northwind
    unidades = consultar("""
        SELECT p.product_name, sum(od.quantity) AS unidades
        FROM order_details od JOIN products p ON p.product_id = od.product_id
        GROUP BY p.product_name""")
    r.delete(CLAVE_RANKING, STREAM, PROCESADOS)                    # la parte D empieza de cero
    r.zadd(CLAVE_RANKING, dict(zip(unidades.product_name, unidades.unidades.astype(int))))
    print(f"  Productos en el ranking: {r.zcard(CLAVE_RANKING)}")

    # B1. Los 3 productos más vendidos, con sus unidades. Pista: r.zrevrange(clave, 0, 2, withscores=True)
    # B2. El puesto de 'Chai' en el ranking (el primero es el 1). Pista: r.zrevrank(clave, 'Chai') empieza en 0
    top3 = None  # COMPLETA
    puesto_chai = None  # COMPLETA
    print("\n  Top 3 por unidades:")
    for i, (producto, n) in enumerate(pendiente(top3, "B1, top 3"), 1):
        print(f"    {i}. {producto:<26}{int(n):>6}")
    print(f"\n  Chai está en el puesto {pendiente(puesto_chai, 'B2, puesto de Chai')} de {r.zcard(CLAVE_RANKING)}")


# ---------------------------------------------------------------------------
#  Parte C · MongoDB: pedidos como documentos
# ---------------------------------------------------------------------------
def documentos_pedidos():
    """Un documento por pedido, con el cliente, el empleado y las líneas dentro (embebidos)."""
    pedidos = consultar("""
        SELECT o.order_id, o.order_date, o.customer_id, c.company_name, c.country,
               e.first_name || ' ' || e.last_name AS empleado, o.ship_city, o.ship_country
        FROM orders o
        JOIN customers c ON c.customer_id = o.customer_id
        JOIN employees e ON e.employee_id = o.employee_id""")
    lineas = consultar("""
        SELECT od.order_id, p.product_id, p.product_name, cat.category_name,
               od.unit_price, od.quantity, od.discount
        FROM order_details od
        JOIN products p ON p.product_id = od.product_id
        JOIN categories cat ON cat.category_id = p.category_id""")
    por_pedido = {}
    for l in lineas.itertuples(index=False):
        por_pedido.setdefault(int(l.order_id), []).append({
            "producto_id": int(l.product_id), "producto": l.product_name, "categoria": l.category_name,
            "precio": float(l.unit_price), "cantidad": int(l.quantity), "descuento": float(l.discount)})
    return [{
        "_id": int(p.order_id),
        "fecha": datetime.combine(p.order_date, datetime.min.time()),
        "cliente": {"id": p.customer_id, "empresa": p.company_name, "pais": p.country},
        "empleado": p.empleado,
        "envio": {"ciudad": p.ship_city, "pais": p.ship_country},
        "lineas": por_pedido[int(p.order_id)],
    } for p in pedidos.itertuples(index=False)]


def parte_c():
    db = conectar_mongo()
    db.pedidos.drop()                                               # idempotente: se vuelve a cargar entero
    db.pedidos.insert_many(documentos_pedidos())
    print(f"  Documentos en la colección pedidos: {db.pedidos.count_documents({})}")
    ejemplo = db.pedidos.find_one({"_id": 10248})
    print(f"  Pedido 10248: {ejemplo['cliente']['empresa']} · {len(ejemplo['lineas'])} líneas · "
          f"primera: {ejemplo['lineas'][0]['producto']}")

    # C1. Cuántos pedidos son de clientes de España. Pista: el país está en el subdocumento cliente: "cliente.pais"
    # C2. Cuántos pedidos tienen alguna línea del producto 'Chai'. Pista: "lineas.producto" busca dentro del array
    espana = None  # COMPLETA
    con_chai = None  # COMPLETA
    print(f"\n  C1 · Pedidos de clientes de España: {pendiente(espana, 'C1')}")
    print(f"  C2 · Pedidos con alguna línea de Chai: {pendiente(con_chai, 'C2')}")

    # C3. Facturación por categoría, de mayor a menor: una agregación con $unwind (una fila por línea), $group
    #     (suma de precio × cantidad × (1 − descuento) por categoría) y $sort.
    agregacion = None  # COMPLETA: la lista de etapas
    filas = list(db.pedidos.aggregate(pendiente(agregacion, "C3, agregación")))
    print("\n  C3 · Facturación por categoría:")
    for f in filas:
        print(f"    {f['_id']:<18}{f['facturacion']:>14,.2f}")
    total_mongo = sum(f["facturacion"] for f in filas)
    total_sql = consultar("SELECT sum(unit_price * quantity * (1 - discount)) AS t FROM order_details").t[0]
    print(f"\n  Total MongoDB {total_mongo:,.2f} · total PostgreSQL {total_sql:,.2f} · "
          f"{'cuadran' if abs(total_mongo - total_sql) < 0.01 else 'NO cuadran'}")


# ---------------------------------------------------------------------------
#  Parte D · Eventos: un stream de pedidos web
# ---------------------------------------------------------------------------
STREAM = "eventos:pedidos_web"
GRUPO = "actualizar_ranking"
PROCESADOS = "eventos:procesados"


def productor(r):
    """Envía cada línea del CSV de la tienda web como un evento al stream (como si llegaran en tiempo real)."""
    with open(PEDIDOS_WEB, encoding="utf-8") as fichero:
        lineas = list(csv.DictReader(fichero, delimiter=";"))
    for linea in lineas:
        r.xadd(STREAM, {"pedido": linea["pedido_web"], "cliente": linea["cliente"].strip().upper(),
                        "producto": linea["producto"], "cantidad": linea["cantidad"]})
    return len(lineas)


def consumidor(r, nombres):
    """Lee los eventos nuevos del grupo, actualiza el ranking y confirma cada evento con XACK."""
    try:
        r.xgroup_create(STREAM, GRUPO, id="0", mkstream=True)
    except redis.ResponseError:                                     # el grupo ya existe
        pass
    contadores = {"sumados": 0, "duplicados": 0, "descartados": 0}
    while True:
        respuesta = r.xreadgroup(GRUPO, "consumidor-1", {STREAM: ">"}, count=100)
        if not respuesta:
            break
        for id_evento, evento in respuesta[0][1]:
            producto = nombres.get(int(evento["producto"]))
            cantidad = int(evento["cantidad"])
            # D1. Decide qué hacer con cada evento:
            #     - si no hay cliente, el producto no existe (producto es None) o la cantidad no es positiva → descartado
            #     - si el par pedido:producto ya se procesó → duplicado.
            #       Pista: r.sadd(PROCESADOS, clave) devuelve 1 si la clave es nueva y 0 si ya estaba
            #     - si no → sumar la cantidad al ranking con r.zincrby(CLAVE_RANKING, cantidad, producto)
            #     Suma 1 al contador que corresponda.
            pass  # COMPLETA
            r.xack(STREAM, GRUPO, id_evento)
    return contadores


def parte_d():
    r = conectar_redis()
    if not r.exists(CLAVE_RANKING):
        print("Primero ejecuta la parte B, que crea el ranking:  python nosql.py b")
        sys.exit(1)
    nombres = {int(i): n for i, n in consultar("SELECT product_id, product_name FROM products").itertuples(index=False)}
    antes = dict(r.zrevrange(CLAVE_RANKING, 0, -1, withscores=True))
    enviados = productor(r)
    contadores = consumidor(r, nombres)
    print(f"  Eventos enviados: {enviados} · en el stream: {r.xlen(STREAM)}")
    print(f"  Sumados al ranking: {contadores['sumados']} · duplicados: {contadores['duplicados']} · "
          f"descartados: {contadores['descartados']}")
    if sum(contadores.values()) == 0:
        print("\n  >> Falta completar: D1, decidir qué hacer con cada evento\n")
        sys.exit(1)
    print("\n  Top 5 después de los pedidos web:")
    for i, (producto, n) in enumerate(r.zrevrange(CLAVE_RANKING, 0, 4, withscores=True), 1):
        print(f"    {i}. {producto:<26}{int(n):>6}   (+{int(n - antes.get(producto, 0))})")


if __name__ == "__main__":
    partes = {"a": parte_a, "b": parte_b, "c": parte_c, "d": parte_d}
    if len(sys.argv) != 2 or sys.argv[1].lower() not in partes:
        print(__doc__)
        sys.exit(1)
    try:
        partes[sys.argv[1].lower()]()
    except (redis.ConnectionError, ConnectionRefusedError):
        print("Redis no responde. En la carpeta del entorno: docker compose --profile redis --profile mongo up -d")
        sys.exit(1)
    except ServerSelectionTimeoutError:
        print("MongoDB no responde. En la carpeta del entorno: docker compose --profile redis --profile mongo up -d")
        sys.exit(1)
    except OperationalError:
        print("PostgreSQL no responde. En la carpeta del entorno: docker compose up -d")
        sys.exit(1)
