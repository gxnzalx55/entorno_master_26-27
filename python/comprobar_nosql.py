"""
Comprueba que MongoDB y Redis (sesión 6) responden.

Uso:  python comprobar_nosql.py
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# ---------- MongoDB ----------
try:
    from pymongo import MongoClient

    url = (f"mongodb://{os.getenv('MONGO_USER', 'root')}:{os.getenv('MONGO_PASSWORD', 'example1')}"
           f"@localhost:{os.getenv('MONGO_PORT', '27017')}/")
    MongoClient(url, serverSelectionTimeoutMS=3000).admin.command("ping")
    print("✅ MongoDB responde en localhost:" + os.getenv("MONGO_PORT", "27017"))
except Exception as error:
    print("❌ MongoDB no responde. ¿Has hecho 'docker compose --profile mongo up -d'?")
    print(f"   Detalle: {str(error).splitlines()[0]}")

# ---------- Redis ----------
try:
    import redis

    r = redis.Redis(host="localhost", port=int(os.getenv("REDIS_PORT", "6379")), socket_timeout=3)
    r.ping()
    print("✅ Redis responde en localhost:" + os.getenv("REDIS_PORT", "6379"))
except Exception as error:
    print("❌ Redis no responde. ¿Has hecho 'docker compose --profile redis up -d'?")
    print(f"   Detalle: {str(error).splitlines()[0]}")
