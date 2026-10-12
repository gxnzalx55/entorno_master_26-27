"""
EL CASO DE LA CAJA PERDIDA · comprobador de la solución

Uso
  python misterio.py culpable "Nombre Apellido"
  python misterio.py cerebro  "Nombre Apellido"      (reto extra)
  python misterio.py pista 1                         (pistas de la 1 a la 4)

El enunciado completo está en misterio/ENUNCIADO.md.
Las soluciones se guardan como huella SHA-256: no se pueden leer en este archivo.
"""

import hashlib
import sys
import unicodedata

HUELLAS = {
    "culpable": "1867d421888db609e1ca991322dfcfa5d6af82b46dc726e77910b4a5f043d591",
    "cerebro": "f124638b8ae344991b0504f5ef92417e55d5077f54585a888f99d010eb86bedb",
}

PISTAS = {
    "1": "El cliente de Sevilla está en customers (columna city). Su último pedido es el de order_date más reciente en orders.",
    "2": "orders.ship_via apunta a shippers.shipper_id. La declaración que buscas es del día siguiente a shipped_date.",
    "3": "Para comparar a un empleado con sus compañeros, une employees consigo misma: misma city y mismo reports_to.",
    "4": "caso.fichajes.num_tarjeta = employees.extension. Filtra por fecha, por puerta 'Almacén' y por hora < '08:00'.",
}


def normaliza(nombre: str) -> str:
    sin_tildes = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode()
    return " ".join(sin_tildes.lower().split())


def huella(nombre: str) -> str:
    return hashlib.sha256(normaliza(nombre).encode()).hexdigest()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    orden, valor = sys.argv[1], " ".join(sys.argv[2:])

    if orden == "pista":
        print(PISTAS.get(valor, "Hay pistas de la 1 a la 4."))
    elif orden in HUELLAS:
        if huella(valor) == HUELLAS[orden]:
            if orden == "culpable":
                print(f"✅ ¡Correcto! {valor} sacó la caja del almacén.")
                print("   Pero no actuó sola. Lee su interrogatorio en caso.interrogatorios y busca al cerebro.")
            else:
                print(f"🏆 ¡Caso cerrado! {valor} dio las instrucciones. Enhorabuena, detectives.")
        else:
            print(f"❌ {valor} no es la respuesta. Revisad vuestras consultas.")
    else:
        sys.exit(__doc__)
