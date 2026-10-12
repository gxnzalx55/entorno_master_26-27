"""
Ejercicio · Una capa de datos lista para un modelo
Almacenamiento, visualización y procesamiento de datos · Sesión 10

Pregunta de negocio: ¿qué clientes volverán a comprar en los próximos cuatro meses?
No se entrena ningún modelo: se prepara el conjunto de datos, se comprueba y se documenta.

  a  La foto: las características de cada cliente en una fecha de corte
  b  La etiqueta y la división temporal: entrenamiento y prueba
  c  La fuga: la misma característica calculada con el futuro, y la línea base
  d  Exportar a Parquet y escribir la ficha de datos

Uso, desde la carpeta python del entorno y con el entorno virtual activado:
  python capa_ml.py a        (o b, c, d; las veces que quieras)

Los ficheros se guardan en datos/ml. Las líneas marcadas con COMPLETA son las que tienes que escribir tú.
"""
import hashlib
import sys

import pandas as pd

from utilidades import CARPETA_PROYECTO, consultar

CARPETA = CARPETA_PROYECTO / "datos" / "ml"
FIN_DE_LOS_DATOS = pd.Timestamp("1998-05-06")        # el último pedido de Northwind
FOTOS = {                                            # fecha de corte y fin de la ventana de la etiqueta (sin incluir)
    "train": ("1997-09-01", "1998-01-01"),           # septiembre a diciembre de 1997
    "test": ("1998-01-01", "1998-05-01"),            # enero a abril de 1998: mayo está incompleto
}
DIAS_REGLA = 120                                     # la regla de la parte C

# Un pedido por fila, con el importe calculado como en la capa oro (sesión 8)
SQL_PEDIDOS = """
    SELECT o.order_id AS pedido_id, o.customer_id AS cliente_id, c.country AS pais, o.order_date AS fecha,
           SUM(od.unit_price::numeric * od.quantity * (1 - od.discount::numeric)) AS importe
    FROM orders o
    JOIN order_details od ON od.order_id = o.order_id
    JOIN customers c      ON c.customer_id = o.customer_id
    GROUP BY o.order_id, o.customer_id, c.country, o.order_date
"""


# ---------------------------------------------------------------------------
#  Utilidades (no hace falta tocarlas)
# ---------------------------------------------------------------------------
def pendiente(valor, que):
    if valor is None:
        print(f"\n  >> Falta completar: {que}\n")
        sys.exit(1)
    return valor


def pedidos():
    df = consultar(SQL_PEDIDOS)
    df["fecha"] = pd.to_datetime(df["fecha"])
    df["importe"] = df["importe"].astype(float)
    return df


def pct(x):
    return f"{100 * x:.1f} %".replace(".", ",")


def miles(x):
    return f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ---------------------------------------------------------------------------
#  Parte A · La foto en una fecha de corte
# ---------------------------------------------------------------------------
def foto(ped, corte):
    """Una fila por cliente con pedidos ANTERIORES al corte. Nada posterior al corte puede entrar."""
    corte = pd.Timestamp(corte)
    historia = ped[ped["fecha"] < corte]
    assert historia["fecha"].max() < corte, "Fuga: hay pedidos posteriores al corte en la historia"
    f = (historia.groupby(["cliente_id", "pais"], as_index=False)
                 .agg(pedidos=("pedido_id", "nunique"), facturacion=("importe", "sum"),
                      ultimo=("fecha", "max"), primero=("fecha", "min")))
    f["ticket_medio"] = f["facturacion"] / f["pedidos"]
    f["antiguedad_dias"] = (corte - f["primero"]).dt.days
    dias = None
    # A1. Días desde la última compra (columna ultimo) hasta la fecha de corte, en días enteros.
    #     Pista: (corte - f["ultimo"]).dt.days
    # COMPLETA (1 línea)
    # (escribe aquí tu código)
    f["dias_sin_comprar"] = pendiente(dias, "A1, días sin comprar desde el corte")
    f["fecha_corte"] = corte
    columnas = ["cliente_id", "pais", "fecha_corte", "pedidos", "facturacion", "ticket_medio", "dias_sin_comprar",
                "antiguedad_dias"]
    return f[columnas].sort_values("cliente_id").reset_index(drop=True)


def parte_a():
    ped = pedidos()
    print(f"  {len(ped)} pedidos de {ped['cliente_id'].nunique()} clientes, "
          f"del {ped['fecha'].min():%d/%m/%Y} al {ped['fecha'].max():%d/%m/%Y}")
    f = foto(ped, FOTOS["test"][0])
    print(f"\n  Foto a {FOTOS['test'][0]}: {len(f)} clientes con historia\n")
    muestra = f[f["cliente_id"].isin(["ALFKI", "QUICK", "CENTC"])]
    print(muestra[["cliente_id", "pais", "pedidos", "facturacion", "dias_sin_comprar", "antiguedad_dias"]]
          .to_string(index=False, formatters={"facturacion": miles}))


# ---------------------------------------------------------------------------
#  Parte B · La etiqueta y la división temporal
# ---------------------------------------------------------------------------
def con_etiqueta(ped, corte, fin):
    """La foto en el corte y la etiqueta: 1 si el cliente compra en la ventana [corte, fin)."""
    corte, fin = pd.Timestamp(corte), pd.Timestamp(fin)
    assert fin <= FIN_DE_LOS_DATOS, "La ventana pasa del final de los datos: estaría incompleta"
    f = foto(ped, corte)
    ventana = ped[(ped["fecha"] >= corte) & (ped["fecha"] < fin)]
    compra = None
    # B1. Etiqueta: 1 si el cliente aparece en algún pedido de la ventana y 0 si no.
    #     Pista: f["cliente_id"].isin(ventana["cliente_id"]).astype(int)
    # COMPLETA (1 línea)
    # (escribe aquí tu código)
    f["compra"] = pendiente(compra, "B1, la etiqueta")
    nuevos = sorted(set(ventana["cliente_id"]) - set(f["cliente_id"]))     # compran en la ventana sin historia
    return f, nuevos


def conjuntos(ped):
    return {nombre: con_etiqueta(ped, corte, fin) for nombre, (corte, fin) in FOTOS.items()}


def parte_b():
    ped = pedidos()
    for nombre, (f, nuevos) in conjuntos(ped).items():
        corte, fin = FOTOS[nombre]
        print(f"  {nombre:<5} corte {corte} · ventana hasta {fin} (sin incluir): {len(f)} clientes · "
              f"compran {f['compra'].sum()} ({pct(f['compra'].mean())}) · sin foto: {', '.join(nuevos) or '—'}")


# ---------------------------------------------------------------------------
#  Parte C · La fuga y la línea base
# ---------------------------------------------------------------------------
def acierto_regla(dias, etiqueta):
    """Regla: si lleva DIAS_REGLA días o menos sin comprar, volverá a comprar. Devuelve el acierto (0 a 1)."""
    acierto = None
    # C1. Predicción = 1 si dias <= DIAS_REGLA, si no 0. Acierto = proporción de clientes con predicción = etiqueta.
    #     Pista: ((dias <= DIAS_REGLA).astype(int) == etiqueta).mean()
    # COMPLETA (1 línea)
    # (escribe aquí tu código)
    return pendiente(acierto, "C1, el acierto de la regla")


def parte_c():
    ped = pedidos()
    f, _ = conjuntos(ped)["test"]
    ultimo_total = ped.groupby("cliente_id")["fecha"].max()                 # con TODOS los datos: el futuro incluido
    dias_fuga = (FIN_DE_LOS_DATOS - f["cliente_id"].map(ultimo_total)).dt.days
    alfki = f["cliente_id"] == "ALFKI"
    print(f"  ALFKI: {int(f.loc[alfki, 'dias_sin_comprar'].iloc[0])} días sin comprar en la foto · "
          f"{int(dias_fuga[alfki].iloc[0])} días si se calcula al {FIN_DE_LOS_DATOS:%d/%m/%Y}\n")
    linea_base = None
    # C2. Línea base: el acierto de decir que TODOS compran, es decir, la proporción de etiquetas iguales a 1.
    # COMPLETA (1 línea)
    # (escribe aquí tu código)
    linea_base = pendiente(linea_base, "C2, la línea base")
    filas = [("Regla con fuga (días al final de los datos)", acierto_regla(dias_fuga, f["compra"]),
              dias_fuga.corr(f["compra"])),
             ("Regla sin fuga (días al corte)", acierto_regla(f["dias_sin_comprar"], f["compra"]),
              f["dias_sin_comprar"].corr(f["compra"])),
             ("Línea base: todos compran", linea_base, None)]
    print(f"  {'Foto de prueba, ' + str(len(f)) + ' clientes':<46}{'acierto':>10}{'correlación':>14}")
    for nombre, a, r in filas:
        print(f"  {nombre:<46}{pct(a):>10}{('' if r is None else f'{r:.2f}'.replace('.', ',')):>14}")


# ---------------------------------------------------------------------------
#  Parte D · Exportar y documentar
# ---------------------------------------------------------------------------
def ficha(datos):
    lineas = ["# Ficha de datos · clientes que vuelven a comprar", "",
              "Origen: Northwind (PostgreSQL del entorno del curso), pedidos del 4/7/1996 al 6/5/1998.",
              "Pregunta: ¿volverá a comprar el cliente en los cuatro meses siguientes a la fecha de corte?",
              "Fila: un cliente con al menos un pedido antes del corte. Etiqueta: compra (1 o 0).",
              "Decisiones: ventanas de cuatro meses completos (mayo de 1998, con 6 días, queda fuera); "
              "importe con descuento, como la capa oro; división temporal, sin azar.", ""]
    for nombre, (f, nuevos) in datos.items():
        corte, fin = FOTOS[nombre]
        lineas += [f"## {nombre} · corte {corte} · ventana hasta {fin} (sin incluir)", "",
                   f"- Filas: {len(f)} · columnas: {', '.join(f.columns)}"]
        nulos = None
        etiqueta = None
        # D1. Completa dos datos de la ficha:
        #     nulos    = número total de valores nulos de la tabla          Pista: int(f.isna().sum().sum())
        #     etiqueta = proporción de clientes que compran (la línea base) Pista: f["compra"].mean()
        # COMPLETA (2 líneas)
        # (escribe aquí tu código)
        pendiente(nulos, "D1, los nulos de la ficha")
        pendiente(etiqueta, "D1, la etiqueta de la ficha")
        paises = f["pais"].value_counts()
        lineas += [f"- Nulos: {nulos}",
                   f"- Etiqueta: compran {f['compra'].sum()} de {len(f)} ({pct(etiqueta)}). Es la línea base.",
                   f"- Cobertura: fuera, por no tener historia, los clientes nuevos de la ventana: "
                   f"{', '.join(nuevos) or 'ninguno'}; y los clientes que nunca han comprado.",
                   f"- Sesgos: {paises.size} países; los que más clientes tienen: "
                   + ", ".join(f"{p} {n}" for p, n in paises.head(3).items())
                   + f"; {int((paises == 1).sum())} países con un solo cliente.", ""]
    return "\n".join(lineas)


def huella(ruta):
    return hashlib.sha256(ruta.read_bytes()).hexdigest()[:12]


def exportar(datos):
    CARPETA.mkdir(parents=True, exist_ok=True)
    rutas = []
    for nombre, (f, _) in datos.items():
        ruta = CARPETA / f"clientes_{nombre}.parquet"
        f.to_parquet(ruta, index=False)
        rutas.append(ruta)
    ruta_ficha = CARPETA / "ficha_datos.md"
    ruta_ficha.write_text(ficha(datos), encoding="utf-8")
    return rutas + [ruta_ficha]


def parte_d():
    ped = pedidos()
    primera = {r.name: huella(r) for r in exportar(conjuntos(ped))}
    segunda = {r.name: huella(r) for r in exportar(conjuntos(ped))}       # otra vez: tiene que salir lo mismo
    for nombre, h in primera.items():
        estado = "idéntico" if segunda[nombre] == h else "DISTINTO"
        print(f"  {CARPETA.name}/{nombre:<26} huella {h} · segunda ejecución: {estado}")
    print(f"\n  Abre {CARPETA / 'ficha_datos.md'} para leer la ficha.")


# ---------------------------------------------------------------------------
PARTES = {"a": parte_a, "b": parte_b, "c": parte_c, "d": parte_d}

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1].lower() not in PARTES:
        print(__doc__)
        sys.exit(1)
    PARTES[sys.argv[1].lower()]()
