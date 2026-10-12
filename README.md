# Entorno del curso · PostgreSQL, MongoDB y Redis con Docker

> **Empieza por `GUIA_DOCKER.md`**: explica Docker en cinco ideas, cómo preparar el entorno y qué arrancar en cada sesión.

Este proyecto levanta, con un solo comando, las bases de datos del curso:

- **PostgreSQL 16** con la base de datos **Northwind** ya cargada.
- **pgAdmin 4** en el navegador, sin login y con el servidor ya dado de alta.
- **Redis** y **MongoDB** (con mongo-express), que solo se arrancan en la sesión 6.

## 1. Puesta en marcha (5 minutos)

Requisitos: Docker Desktop arrancado y Python 3.10 o superior.

```bash
# 1) En la carpeta del proyecto, crea tu archivo de configuración
cp .env.example .env            # en Windows (PowerShell): copy .env.example .env

# 2) Levanta PostgreSQL y pgAdmin (la primera vez descarga las imágenes)
docker compose up -d

# 3) Instala las librerías de Python
cd python
python -m venv .venv
.venv\Scripts\activate          # en macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

# 4) Comprueba que todo funciona
python comprobar_entorno.py
```

Si el paso 4 dice **✅ Conexión correcta con Northwind** y 830 pedidos, ya está.

Si creaste el entorno antes de la sesión 4, vuelve a ejecutar `pip install -r requirements.txt` con el entorno virtual activado: así se instala DuckDB. Y lo mismo antes de la sesión 7, para instalar Seaborn.

## 2. Entrar en pgAdmin

1. Abre <http://localhost:5050>. No pide usuario.
2. En el panel izquierdo despliega **Clase SQL → Northwind (Docker)**.
3. La primera vez te pide la contraseña de `postgres`: es la de `POSTGRES_PASSWORD` en `.env`. Marca *Save password*.
4. Botón derecho sobre `northwind` → **Query Tool** para escribir consultas.

## 3. Qué hay en cada carpeta

| Carpeta o archivo | Para qué sirve | Sesión |
|---|---|---|
| `docker-compose.yml` | Define los contenedores del curso | Todas |
| `.env` | Usuario, contraseña y puertos. Lo leen Docker y Python | Todas |
| `initdb/01_northwind.sql` | Carga Northwind (solo la primera vez) | Todas |
| `initdb/02_caso_northwind.sql` | Crea el esquema `caso` de *El caso de la caja perdida* | 3 |
| `pgadmin/servers.json` | Da de alta el servidor en pgAdmin | Todas |
| `python/comprobar_entorno.py` | Comprueba la conexión con Northwind | 2 |
| `python/comprobar_nosql.py` | Comprueba Redis y MongoDB | 6 |
| `python/nosql.py` | Ejercicio de la sesión 6: caché y ranking en Redis, pedidos como documentos en MongoDB y un stream de eventos | 6 |
| `python/demo_acid.py` | Demo de transacciones: todo o nada | 2 |
| `python/misterio.py` + `misterio/ENUNCIADO.md` | *El caso de la caja perdida*: comprueba culpable y cerebro, y da pistas | 3 |
| `sql/crear_ventas_grandes.sql` | Crea `ventas_grandes`, 2 millones de ventas para medir rendimiento. Se ejecuta en pgAdmin | 4 |
| `python/parquet_vs_csv.py` | Ejercicio 2 de la sesión 4: CSV frente a Parquet con pandas y DuckDB | 4 |
| `python/pipeline.py` | Pipeline bronce, plata y oro con cuarentena y pruebas de calidad. Plantilla para el trabajo final | 5 |
| `fuentes/pedidos_web.csv` | Pedidos de una tienda web, con errores a propósito: la segunda fuente del pipeline | 5 |
| `python/graficos.py` | Ejercicio 1 de la sesión 7: gráficos con IA y revisión crítica con Seaborn. Los PNG se guardan en `datos/graficos` | 7 |
| `fuentes/maven_toys/` | Datos públicos de Maven Toys (ventas, tiendas, productos, calendario e inventario) para Power BI | 7, 8 y 9 |
| `sql/oro_estrella.sql` | Capa oro de la sesión 8: Northwind como modelo en estrella (vistas `fact_ventas` y dimensiones) para Power BI. Se ejecuta en pgAdmin | 8 y 9 |
| `python/capa_ml.py` | Ejercicio de la sesión 10: una capa de datos lista para un modelo (fotos con fecha de corte, fuga, línea base y ficha). Escribe en `datos/ml` | 10 |
| `datos/` | Ficheros CSV y Parquet que generan los scripts. No se sube a git | 4, 5 (`datos/lakehouse`: bronce, plata y oro), 7 (`datos/graficos`) y 10 (`datos/ml`) |
| `python/utilidades.py` | Conexión a PostgreSQL que usan los scripts | Todas |

## 4. Problemas habituales

| Síntoma | Solución |
|---|---|
| `port is already allocated` en el 5432 | Ya tienes otro PostgreSQL. En `.env` pon `POSTGRES_PORT=5433` y repite `docker compose up -d` |
| Falta el esquema `caso` o quieres empezar de cero | `docker compose down -v` (borra el volumen) y `docker compose up -d` |
| `password authentication failed` | Cambiaste la contraseña en `.env` después del primer arranque. Haz `docker compose down -v` y vuelve a levantar |
| pgAdmin tarda en abrir | Espera 20-30 s la primera vez; `docker compose ps` debe mostrar los servicios en `running` |

Para apagar todo sin perder los datos: `docker compose down`.
