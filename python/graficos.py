"""
Ejercicio 1 · Gráficos con IA y revisión crítica
Almacenamiento, visualización y procesamiento de datos · Sesión 7

Cada reto tiene un gráfico «de partida», hecho como lo haría una IA con un prompt rápido, que tiene errores.
Tu trabajo: revisarlo con la lista de 8 puntos del enunciado y escribir la versión corregida.

  a  Facturación por país (barras)
  b  Facturación por categoría (tarta)
  c  Facturación mensual (línea)
  d  Pedidos y facturación por cliente: el gráfico lo pides tú a una IA
  e  De exploratorio a explicativo: el gráfico mensual con un mensaje

Uso, desde la carpeta python del entorno y con el entorno virtual activado:
  python graficos.py a        (o b, c, d, e; las veces que quieras)

Los gráficos se guardan como PNG en datos/graficos. Ábrelos para revisarlos.
Las funciones marcadas con COMPLETA son las que tienes que escribir tú.
"""
import sys

import matplotlib

matplotlib.use("Agg")                                               # guarda PNG sin abrir ventanas
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
import seaborn as sns  # noqa: E402

from utilidades import CARPETA_PROYECTO, consultar  # noqa: E402

CARPETA = CARPETA_PROYECTO / "datos" / "graficos"
AZUL, GRIS, NARANJA = "#0070C0", "#B8C2CC", "#E07A1F"

# Una fila por línea de pedido de Northwind, con lo necesario para todos los retos
SQL_LINEAS = """
    SELECT o.order_id, o.order_date AS fecha, c.customer_id, c.company_name AS cliente, c.country AS pais,
           cat.category_name AS categoria,
           od.unit_price * od.quantity * (1 - od.discount) AS importe
    FROM orders o
    JOIN order_details od ON od.order_id = o.order_id
    JOIN customers c      ON c.customer_id = o.customer_id
    JOIN products p       ON p.product_id = od.product_id
    JOIN categories cat   ON cat.category_id = p.category_id
"""


# ---------------------------------------------------------------------------
#  Utilidades (no hace falta tocarlas)
# ---------------------------------------------------------------------------
def datos():
    df = consultar(SQL_LINEAS)
    df["fecha"] = pd.to_datetime(df["fecha"])
    df["mes"] = df["fecha"].dt.to_period("M").dt.to_timestamp()
    return df


def guardar(fig, nombre):
    CARPETA.mkdir(parents=True, exist_ok=True)
    ruta = CARPETA / f"{nombre}.png"
    fig.savefig(ruta, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print(f"  Guardado: {ruta}")


def miles(x, _=None):
    return f"{x:,.0f}".replace(",", ".")


# ---------------------------------------------------------------------------
#  Reto A · Facturación por país
# ---------------------------------------------------------------------------
def partida_a(df):
    """Prompt: «haz un gráfico de barras de la facturación por país con seaborn»."""
    por_pais = df.groupby("pais", as_index=False)["importe"].sum()
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(data=por_pais, x="pais", y="importe", hue="pais", palette="rainbow", legend=False, ax=ax)
    ax.set_ylim(20000, 260000)                                      # el eje no empieza en cero
    ax.tick_params(axis="x", rotation=90)
    ax.set_title("Facturación por país")
    return fig


def corregido_a(df):
    # COMPLETA: barras horizontales, ordenadas de mayor a menor, empezando en cero, de un solo color
    # (resalta solo el primer país, si quieres), con el eje rotulado y en euros sin decimales.
    # Pista: sort_values, sns.barplot(…, y="pais", x="importe", color=…), ax.xaxis.set_major_formatter(miles)
    return None  # COMPLETA


# ---------------------------------------------------------------------------
#  Reto B · Facturación por categoría
# ---------------------------------------------------------------------------
def partida_b(df):
    """Prompt: «muestra el reparto de la facturación entre categorías»."""
    por_cat = df.groupby("categoria")["importe"].sum()
    fig, ax = plt.subplots(figsize=(7, 7))
    ax.pie(por_cat, labels=por_cat.index, autopct="%1.1f%%", colors=sns.color_palette("hls", 8), startangle=90)
    ax.set_title("Facturación por categoría")
    return fig


def corregido_b(df):
    # COMPLETA: con 8 categorías, una tarta obliga a comparar ángulos parecidos. Haz barras horizontales
    # ordenadas con el porcentaje de cada categoría escrito al final de cada barra.
    # Pista: calcula pct = importe / total * 100 y usa ax.bar_label(ax.containers[0], fmt="%.1f %%")
    return None  # COMPLETA


# ---------------------------------------------------------------------------
#  Reto C · Facturación mensual
# ---------------------------------------------------------------------------
def partida_c(df):
    """Prompt: «gráfico de la evolución de la facturación mensual»."""
    mensual = df.groupby("mes", as_index=False)["importe"].sum()
    fig, ax = plt.subplots(figsize=(10, 4.5))
    sns.lineplot(data=mensual, x="mes", y="importe", marker="o", ax=ax)
    ax.set_title("Facturación mensual")
    return fig


def corregido_c(df):
    # COMPLETA: el último mes (mayo de 1998) solo tiene datos hasta el día 6, y la caída es falsa.
    # Quítalo de la línea (o dibújalo aparte y avisa), rotula el eje en euros y pon un título informativo.
    # Pista: mensual[mensual["mes"] < "1998-05-01"]
    return None  # COMPLETA


# ---------------------------------------------------------------------------
#  Reto D · El gráfico lo pides tú
# ---------------------------------------------------------------------------
def por_cliente(df):
    return (df.groupby(["customer_id", "cliente", "pais"], as_index=False)
              .agg(pedidos=("order_id", "nunique"), facturacion=("importe", "sum")))


def reto_d(df):
    tabla = por_cliente(df)
    print(f"  Tabla por cliente: {len(tabla)} filas · columnas: {list(tabla.columns)}")
    # COMPLETA: pide a una IA un gráfico que muestre la relación entre pedidos y facturación de cada cliente
    # (la tabla tiene las columnas de arriba). Pega aquí su código, revísalo con la lista y corrígelo.
    # Cita en un comentario la herramienta, la versión y el prompt (menos de 20 palabras).
    return None  # COMPLETA


# ---------------------------------------------------------------------------
#  Reto E · De exploratorio a explicativo
# ---------------------------------------------------------------------------
def reto_e(df):
    mensual = df.groupby("mes", as_index=False)["importe"].sum()
    completos = mensual[mensual["mes"] < "1998-05-01"]
    ene_abr = completos[completos["mes"].dt.month <= 4].groupby(completos["mes"].dt.year)["importe"].sum()
    print(f"  Enero a abril: 1997 → {miles(ene_abr[1997])} € · 1998 → {miles(ene_abr[1998])} € · "
          f"× {ene_abr[1998] / ene_abr[1997]:.1f}")
    # COMPLETA: convierte el gráfico mensual en explicativo (Knaflic):
    #  - título que diga el mensaje (usa las cifras de arriba)
    #  - todo en gris salvo los meses de enero a abril de 1998, en un color que destaque
    #  - una anotación con la cifra clave, y sin rejilla ni bordes que no aporten
    return None  # COMPLETA


# ---------------------------------------------------------------------------
RETOS = {
    "a": [("A_partida", partida_a), ("A_corregido", corregido_a)],
    "b": [("B_partida", partida_b), ("B_corregido", corregido_b)],
    "c": [("C_partida", partida_c), ("C_corregido", corregido_c)],
    "d": [("D_ia", reto_d)],
    "e": [("E_explicativo", reto_e)],
}

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1].lower() not in RETOS:
        print(__doc__)
        sys.exit(1)
    sns.set_theme(style="whitegrid")
    df = datos()
    print(f"  {len(df)} líneas de pedido · facturación total {miles(df['importe'].sum())} €")
    for nombre, funcion in RETOS[sys.argv[1].lower()]:
        fig = funcion(df)
        if fig is None:
            print(f"\n  >> Falta completar: {funcion.__name__}\n")
            sys.exit(1)
        guardar(fig, nombre)
