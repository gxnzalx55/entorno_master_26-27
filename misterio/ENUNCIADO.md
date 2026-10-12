# 🕵️ El caso de la caja perdida

**Northwind Traders, Londres, abril de 1998.**

Un cliente de **Sevilla** ha presentado una reclamación: su último pedido llegó con una caja menos. La dirección sospecha que alguien de dentro sacó la caja del almacén antes de que saliera el envío, y os ha contratado como detectives de datos.

No tenéis testigos a mano. Solo tenéis la base de datos.

## Lo que sabéis

- Toda la información está en PostgreSQL: las tablas normales de Northwind (`customers`, `orders`, `order_details`, `products`, `shippers`, `employees`...) y el esquema **`caso`**, con cinco tablas de pistas.
- Para ver qué tablas hay en `caso`:

```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'caso';
```

- **Primera pista:** empezad por los incidentes de abril de 1998 en `caso.incidentes` y buscad el que habla de Sevilla.

## Objetivo

1. **Culpable (obligatorio):** ¿quién sacó la caja del almacén? Nombre y apellido.
2. **Cerebro (reto extra):** la persona culpable no actuó sola. ¿Quién le dio las instrucciones?

## Cómo comprobar la respuesta

```bash
cd python
python misterio.py culpable "Nombre Apellido"
python misterio.py cerebro  "Nombre Apellido"
python misterio.py pista 1
```

## Cómo se trabaja

Individualmente o en grupo, cada uno en su ordenador. Apunta la cadena de consultas que te lleva a cada nombre: al final del ejercicio la corregimos en clase.

Si te atascas, `python misterio.py pista 1` (hay cuatro pistas).

Puedes usar Copilot o cualquier asistente de IA, pero ojo: la IA no ve tu base de datos. Tendrás que leer las pistas, decidir qué tablas cruzar y comprobar cada resultado.
