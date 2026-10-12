"""
Comprueba que todo está listo antes de empezar la clase.

Uso:  python comprobar_entorno.py
"""

from utilidades import cadena_de_conexion, consultar

try:
    tablas = consultar("""
        SELECT table_schema AS esquema, COUNT(*) AS tablas
        FROM information_schema.tables
        WHERE table_schema IN ('public', 'caso')
        GROUP BY table_schema ORDER BY table_schema
    """)
    pedidos = consultar("SELECT COUNT(*) AS n FROM orders")["n"].iloc[0]
except Exception as error:
    print("❌ No puedo conectar con PostgreSQL.")
    print(f"   Cadena usada: {cadena_de_conexion().split('@')[-1]}")
    print("   ¿Has hecho 'docker compose up -d' en la carpeta del proyecto y existe el archivo .env?")
    print(f"   Detalle: {str(error).splitlines()[0]}")
    raise SystemExit(1)

print("✅ Conexión correcta con Northwind")
print(tablas.to_string(index=False))
print(f"Pedidos en orders: {pedidos} (deberían ser 830)")
if "caso" not in set(tablas["esquema"]):
    print("⚠️  Falta el esquema 'caso' del misterio: ejecuta 'docker compose down -v' y 'docker compose up -d'.")
