# Guía del entorno del curso (Docker)

Todo lo que necesitáis para las clases de bases de datos está en esta carpeta: PostgreSQL con Northwind, pgAdmin, MongoDB, mongo-express y Redis. No hay que instalar ninguna base de datos en vuestro ordenador; Docker las ejecuta por vosotros.

## 1. Docker en cinco ideas

1. **Imagen:** una plantilla de solo lectura con un programa ya instalado, por ejemplo `postgres:16`. Se descarga una vez de Docker Hub.
2. **Contenedor:** una imagen en marcha. Es como un ordenador pequeño y aislado que ejecuta un solo programa.
3. **Puerto:** la puerta entre vuestro ordenador y el contenedor. `5432:5432` significa que lo que llega a `localhost:5432` entra en el PostgreSQL del contenedor.
4. **Volumen:** el disco donde el contenedor guarda los datos. Si apagáis el contenedor, los datos siguen ahí; solo se borran si lo pedís (`down -v`).
5. **docker compose:** un archivo, `docker-compose.yml`, que describe todos los contenedores del curso y los arranca con un solo comando.

## 2. Preparación (una sola vez, antes de la sesión 2)

1. Instalad **Docker Desktop** (<https://www.docker.com/products/docker-desktop/>). En Windows, aceptad cuando pida activar WSL 2 y reiniciad.
2. Abrid Docker Desktop y esperad a que diga que está en marcha. Comprobadlo en una terminal: `docker run hello-world` tiene que mostrar "Hello from Docker!".
3. Instalad **Python 3.10 o superior**.
4. Descomprimid esta carpeta y abrid una terminal dentro de ella.
5. Cread vuestro archivo de configuración copiando el ejemplo:
   - Windows (PowerShell): `copy .env.example .env`
   - macOS / Linux: `cp .env.example .env`
6. Cread el entorno de Python e instalad las librerías (sirve para todo el curso):

```bash
cd python
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cd ..
```


## 3. Qué arrancar en cada sesión

Todos los comandos se escriben en la carpeta donde está `docker-compose.yml`, con Docker Desktop abierto.

| Sesión | Comando | Qué se arranca | Dónde se abre |
|---|---|---|---|
| 2 a 5 · SQL y ETL | `docker compose up -d` | PostgreSQL con Northwind y pgAdmin | pgAdmin: <http://localhost:5050> |
| 6 · Redis y MongoDB | `docker compose --profile redis --profile mongo up -d` | Lo de SQL + Redis + MongoDB + mongo-express | Redis: `docker exec -it curso-redis redis-cli` · mongo-express: <http://localhost:8081> |
| 7 a 9 · Power BI | `docker compose up -d` | PostgreSQL con Northwind | Power BI Desktop → PostgreSQL → `localhost` |

La primera vez que arranquéis cada parte, Docker descarga las imágenes y tarda unos minutos. Hacedlo en casa con buena conexión, no en clase.

## 4. Comprobar que todo funciona

```bash
cd python
python comprobar_entorno.py     # SQL: tiene que decir ✅ y 830 pedidos
python comprobar_nosql.py       # MongoDB y Redis: ✅ en lo que hayáis arrancado
```

Para ver qué contenedores están en marcha: `docker compose ps` (tienen que aparecer como `running` o `healthy`).

## 5. Entrar en cada herramienta

- **pgAdmin** (<http://localhost:5050>): no pide usuario. En el panel izquierdo, abrid **Clase SQL → Northwind (Docker)**. La primera vez pide la contraseña de `postgres`: es `northwind2026` (la de `.env`); marcad *Save password*. Botón derecho sobre `northwind` → **Query Tool** para escribir consultas.
- **MongoDB desde Python:** los scripts de la sesión 6 usan `mongodb://root:example1@localhost:27017/`, que es justo lo que arranca este entorno. Ejecutadlos con el mismo entorno de Python (`.venv`).
- **mongo-express** (<http://localhost:8081>): para ver en el navegador las bases de datos y colecciones que crean los scripts.
- **Redis:** `docker exec -it curso-redis redis-cli` y escribid `ping`; tiene que responder `PONG`. Los scripts de la sesión 6 conectan a `localhost:6379`.

## 6. Apagar y empezar de cero

| Quiero | Comando |
|---|---|
| Apagar todo sin perder datos | `docker compose --profile mongo --profile redis down` |
| Borrar todos los datos y empezar de cero | `docker compose --profile mongo --profile redis down -v` y volver a arrancar |

## 7. Problemas habituales

| Síntoma | Solución |
|---|---|
| `Cannot connect to the Docker daemon` o `error during connect` | Docker Desktop no está abierto. Abridlo y esperad a que arranque. |
| `port is already allocated` | Ese puerto lo usa otro programa. Cambiad el puerto en `.env` (por ejemplo `POSTGRES_PORT=5433`) y repetid el comando. |
| Falta el esquema `caso` o `password authentication failed` | Habéis cambiado `.env` después del primer arranque. Haced `docker compose down -v` y volved a arrancar. |
| pgAdmin o mongo-express no abren | Esperad 30 segundos la primera vez y comprobad con `docker compose ps`. |
| En Windows, WSL 2 no está activado | Abrid PowerShell como administrador, ejecutad `wsl --install` y reiniciad. |
