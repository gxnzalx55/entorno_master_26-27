"""
DEMO ACID · Transacciones desde Python (para profundizar)

Es la parte E del Ejercicio 1 de la sesión 2, pero desde un programa en lugar de pgAdmin.
Caso: movemos 10 unidades de stock de Chai (producto 1) a Chang (producto 2). Son dos UPDATE
que tienen que ir juntos: si sale stock de uno, tiene que entrar en el otro.

El script enseña cada sentencia que envía (>) y el stock después de cada paso:

  1. Me arrepiento:   BEGIN, UPDATE, ROLLBACK              -> el cambio se deshace.
  2. Todo va bien:    BEGIN, UPDATE, UPDATE, COMMIT        -> el cambio se guarda.
                      (y otra transacción con el movimiento contrario para volver al principio)
  3. Algo falla:      BEGIN, UPDATE, UPDATE con error      -> la transacción se bloquea; ROLLBACK.
  4. Sin transacción: UPDATE, UPDATE con error (autocommit) -> se pierden 10 unidades.
  5. Cómo se escribe de verdad en un programa: with engine.begin(), que hace COMMIT o ROLLBACK solo.

Al terminar, el stock queda como estaba al empezar.

Uso, desde la carpeta python del entorno y con el entorno virtual activado:
    python demo_acid.py
"""
from sqlalchemy import text

from utilidades import conectar

CONTROL = "SELECT product_id, product_name, units_in_stock FROM products WHERE product_id IN (1, 2) ORDER BY product_id"
SALE_DE_CHAI = "UPDATE products SET units_in_stock = units_in_stock - 10 WHERE product_id = 1"
ENTRA_EN_CHANG = "UPDATE products SET units_in_stock = units_in_stock + 10 WHERE product_id = 2"
ENTRA_MAL = "UPDATE products SET unidades = unidades + 10 WHERE product_id = 2"  # errata a propósito
VUELVE_A_CHAI = "UPDATE products SET units_in_stock = units_in_stock + 10 WHERE product_id = 1"
SALE_DE_CHANG = "UPDATE products SET units_in_stock = units_in_stock - 10 WHERE product_id = 2"


def titulo(texto):
    print("\n" + "=" * 78 + f"\n{texto}\n" + "=" * 78)


def ejecutar(con, sql):
    """Envía una sentencia, como si la seleccionáramos en pgAdmin y pulsáramos F5."""
    print(f"  > {sql};")
    try:
        con.execute(text(sql))
        return True
    except Exception as error:  # el mensaje de PostgreSQL es la primera línea del error
        mensaje = str(getattr(error, "orig", error)).strip().splitlines()[0]
        print(f"    ERROR: {mensaje}")
        return False


def stock(con, nota=""):
    """La consulta de control: el stock de Chai y Chang que ve esta sesión."""
    try:
        filas = {f.product_name: f.units_in_stock for f in con.execute(text(CONTROL))}
        print(f"    stock -> Chai {filas['Chai']} · Chang {filas['Chang']}   {nota}")
        return filas
    except Exception as error:
        mensaje = str(getattr(error, "orig", error)).strip().splitlines()[0]
        print(f"  > {CONTROL};\n    ERROR: {mensaje}")
        return None


engine = conectar()

# AUTOCOMMIT es el modo normal de pgAdmin: cada sentencia se confirma sola,
# salvo que abramos una transacción con BEGIN. Así podemos escribir BEGIN, COMMIT y ROLLBACK a mano.
with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as con:
    inicial = stock(con, "(stock de partida)")

    titulo("1 · Me arrepiento: ROLLBACK deshace los cambios desde el BEGIN")
    ejecutar(con, "BEGIN")
    ejecutar(con, SALE_DE_CHAI)
    stock(con, "(provisional: solo lo ve esta sesión)")
    ejecutar(con, "ROLLBACK")
    stock(con, "(el ROLLBACK lo ha deshecho)")

    titulo("2 · Todo va bien: COMMIT guarda los cambios, y ya no hay vuelta atrás")
    ejecutar(con, "BEGIN")
    ejecutar(con, SALE_DE_CHAI)
    ejecutar(con, ENTRA_EN_CHANG)
    stock(con, "(provisional)")
    ejecutar(con, "COMMIT")
    print("  > ROLLBACK;   (después del COMMIT ya no hay transacción: PostgreSQL solo avisa y no deshace nada)")
    con.execute(text("ROLLBACK"))
    stock(con, "(guardado)")
    print("  Para volver atrás hace falta otra transacción, con el movimiento contrario:")
    ejecutar(con, "BEGIN")
    ejecutar(con, VUELVE_A_CHAI)
    ejecutar(con, SALE_DE_CHANG)
    ejecutar(con, "COMMIT")
    stock(con, "(de nuevo el stock de partida)")

    titulo("3 · Algo falla dentro de la transacción: se bloquea y solo admite ROLLBACK")
    ejecutar(con, "BEGIN")
    ejecutar(con, SALE_DE_CHAI)
    ejecutar(con, ENTRA_MAL)
    stock(con)  # da 'current transaction is aborted'
    ejecutar(con, "ROLLBACK")
    stock(con, "(atomicidad: todo o nada; Chai no ha perdido nada)")

    titulo("4 · Lo mismo SIN transacción (autocommit): cada sentencia se guarda sola")
    ejecutar(con, SALE_DE_CHAI)
    ejecutar(con, ENTRA_MAL)
    stock(con, "<- han desaparecido 10 unidades")
    print("  Restauramos el stock a mano:")
    ejecutar(con, VUELVE_A_CHAI)
    stock(con)

# 5 · Así se escribe en un programa: engine.begin() abre la transacción (BEGIN) y, al salir del bloque,
#     hace COMMIT si todo ha ido bien o ROLLBACK si ha habido un error. No hay que escribirlos a mano.
titulo("5 · En un programa: with engine.begin() hace COMMIT o ROLLBACK solo")
print("  with engine.begin() as con:      # BEGIN")
print("      con.execute(SALE_DE_CHAI)")
print("      con.execute(ENTRA_MAL)       # error -> ROLLBACK automático")
try:
    with engine.begin() as con:
        con.execute(text(SALE_DE_CHAI))
        con.execute(text(ENTRA_MAL))
except Exception as error:
    print(f"    ERROR: {str(getattr(error, 'orig', error)).strip().splitlines()[0]}  -> ROLLBACK")

with engine.connect() as con:
    final = stock(con, "(intacto)")

assert final == inicial, "El stock no ha quedado como al principio: revisa la base de datos"
engine.dispose()
