-- =====================================================================
--  EJERCICIO 1 · Laboratorio de planes de ejecución
--  Almacenamiento, visualización y procesamiento de datos · Sesión 4
--  Plantilla de trabajo: no se entrega; se corrige en clase.
-- =====================================================================
--  Sin IA, salvo en los retos marcados «Con IA». En esos retos, anota:
--    Herramienta y versión:
--    Prompt principal (menos de 20 palabras):
-- =====================================================================
--  Antes de empezar: ejecuta crear_ventas_grandes.sql (F5).  
--  Para medir: EXPLAIN ANALYZE delante de la consulta.
--  Ejecuta cada consulta 2 o 3 veces y anota la última.
-- =====================================================================

-- ---------------------------------------------------------------------
-- PARTE A · Leer planes en Northwind
-- ---------------------------------------------------------------------

-- Pregunta 1
EXPLAIN ANALYZE
SELECT c.category_name,
       round(sum(od.unit_price * od.quantity * (1 - od.discount))::numeric, 2)
         AS facturacion
FROM categories c
JOIN products p       ON p.category_id = c.category_id
JOIN order_details od ON od.product_id = p.product_id
GROUP BY c.category_name
ORDER BY facturacion DESC;

-- Nodo: Seq Scan en order_details, products y categories; dos Hash Join,
--       un HashAggregate y un Sort final.
-- Tiempo: 2,379 ms
-- Por qué: Las tres tablas son pequeñas (2155, 77 y 8 filas) y la consulta
--          necesita leerlas enteras, sin filtro que un índice pueda aprovechar.
--          Los dos Hash Join sacan 2155 filas cada uno (cada línea de pedido
--          encuentra su producto y su categoría) y el HashAggregate las
--   

-- Pregunta 2
EXPLAIN ANALYZE
SELECT * FROM orders WHERE order_id = 10248;

EXPLAIN ANALYZE
SELECT * FROM orders WHERE customer_id = 'ALFKI';

-- Nodo: order_id = 10248  -> PENDIENTE (pega tu plan; lo esperado es Index Scan
--                            using orders_pkey)
--       customer_id = 'ALFKI' -> Seq Scan on orders
-- Tiempo: order_id -> PENDIENTE · customer_id -> 0,165 ms
-- Por qué: order_id es la clave primaria y tiene índice, así que PostgreSQL
--          salta directamente a la fila. customer_id no tiene índice en orders,
--          así que lee las 830 filas, devuelve 6 y descarta 824 (Rows Removed
--          by Filter).

-- Pregunta 3
-- Versión LEFT JOIN
EXPLAIN ANALYZE
SELECT c.customer_id, c.company_name
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.customer_id
WHERE o.order_id IS NULL;

-- Versión NOT EXISTS
EXPLAIN ANALYZE
SELECT c.customer_id, c.company_name
FROM customers c
WHERE NOT EXISTS (
    SELECT 1 FROM orders o WHERE o.customer_id = c.customer_id
);

-- Nodo: Hash Anti Join (con Seq Scan en customers y en orders)
-- Tiempo: 0,219 ms
-- Por qué: Las dos formulaciones devuelven los mismos 2 clientes. PostgreSQL
--          reconoce el LEFT JOIN ... IS NULL como un anti-join, así que ambas
--          dan el mismo plan: construye una tabla hash con los 830 pedidos y
--          se queda con los clientes que no encuentran pareja.

-- ---------------------------------------------------------------------
-- PARTE B · Crear un índice
-- ---------------------------------------------------------------------

-- Pregunta 4
EXPLAIN ANALYZE
SELECT count(*), sum(importe)
FROM ventas_grandes
WHERE cliente_id = 42 AND fecha >= '2024-01-01';

-- Y sin EXPLAIN, para ver el resultado:
SELECT count(*), sum(importe)
FROM ventas_grandes
WHERE cliente_id = 42 AND fecha >= '2024-01-01';

-- Nodo: Parallel Seq Scan (bajo Gather, Partial Aggregate y Finalize Aggregate)
-- Procesos: Workers Launched 2 + 1 = 3
-- Rows Removed by Filter: 665.198 (por proceso; unos 2 millones en total)
-- Tiempo: 99,888 ms
-- Resultado sin EXPLAIN: 4407 ventas, 1121260.50
-- Por qué: Todavía no hay índice por cliente_id (solo el de la clave primaria),
--          así que PostgreSQL lee las 2 millones de filas con 3 procesos en
--          paralelo y descarta casi todas.

-- Pregunta 5
CREATE INDEX idx_ventas_cliente_fecha ON ventas_grandes (cliente_id, fecha);

EXPLAIN ANALYZE
SELECT count(*), sum(importe)
FROM ventas_grandes
WHERE cliente_id = 42 AND fecha >= '2024-01-01';

SELECT count(*), sum(importe)
FROM ventas_grandes
WHERE cliente_id = 42 AND fecha >= '2024-01-01';

-- Nodo: PENDIENTE (pega tu plan; lo esperado es Bitmap Heap Scan + Bitmap Index
--       Scan, como en la P11)
-- Heap Blocks: PENDIENTE
-- Tiempo: PENDIENTE (veces más rápido que 99,888 ms: PENDIENTE)
-- Resultado: 4407 ventas, 1121260.50. No ha cambiado.
-- Por qué: El índice (cliente_id, fecha) resuelve las dos condiciones a la vez,
--          así que solo se leen las páginas de la tabla que contienen filas del
--          cliente 42 desde 2024. El índice acelera la consulta, pero no altera
--          el resultado.

-- Pregunta 6
EXPLAIN ANALYZE
SELECT pg_size_pretty(pg_relation_size('ventas_grandes'))          AS tabla,
       pg_size_pretty(pg_relation_size('ventas_grandes_pkey'))     AS indice_pk,
       pg_size_pretty(pg_relation_size('idx_ventas_cliente_fecha')) AS indice_cliente_fecha;

-- Nodo: PENDIENTE (ejecuta la consulta SIN EXPLAIN ANALYZE; con él solo salía
--       el nodo Result, sin los tamaños)
-- Tiempo: no aplica
-- Por qué: Los índices ocupan espacio en disco y hay que mantenerlos en cada
--          INSERT, UPDATE y DELETE. Es el precio de las lecturas rápidas.


-- Pregunta 7
EXPLAIN ANALYZE
SELECT count(*), sum(importe)
FROM ventas_grandes
WHERE fecha >= '2024-01-01';

-- Nodo: Parallel Seq Scan (no usa el índice)
-- Tiempo: 400,950 ms
-- Por qué: El índice está ordenado primero por cliente_id y después por fecha,
--          como una guía telefónica ordenada por apellido y luego por nombre.
--          Buscar solo por nombre (fecha) obligaría a revisar la sección de cada
--          apellido (cada cliente). Además, esta consulta devuelve cerca del 20 %
--          de la tabla (unas 400.000 filas), y con tantas filas leer la tabla
--          entera sale más barato.

-- ---------------------------------------------------------------------
-- PARTE C · Romper el índice
-- ---------------------------------------------------------------------

-- Pregunta 8
EXPLAIN ANALYZE
SELECT count(*), sum(importe)
FROM ventas_grandes
WHERE cliente_id + 0 = 42 AND fecha >= '2024-01-01';

-- Nodo: Parallel Seq Scan
-- Tiempo: 93,361 ms
-- Por qué: Al aplicar una operación a la columna (cliente_id + 0), PostgreSQL ya
--          no puede buscar 42 en el índice, que está ordenado por cliente_id y
--          no por cliente_id + 0. Tiene que calcular la expresión fila a fila.


-- Pregunta 9
EXPLAIN ANALYZE
SELECT count(*), sum(importe)
FROM ventas_grandes
WHERE cliente_id = 42 AND EXTRACT(YEAR FROM fecha) = 2024;

-- Nodo: Bitmap Heap Scan sobre un Bitmap Index Scan (idx_ventas_cliente_fecha)
-- Tiempo: 106,637 ms
-- Index Cond: cliente_id = 42 (22.054 filas)
-- Filter (después): EXTRACT(year FROM fecha) = 2024
-- Filas descartadas: 17.647 (se quedan 4407)
-- Heap Blocks: exact=12237
-- Por qué: El índice solo resuelve cliente_id = 42, porque EXTRACT sobre fecha
--          impide usarlo para la fecha. Hay que leer todas las filas del
--          cliente (12.237 páginas) y filtrar el año después.

-- Pregunta 10
EXPLAIN ANALYZE
SELECT count(*), sum(importe)
FROM ventas_grandes
WHERE cliente_id > 5;

-- Para el porcentaje de la tabla que devuelve:
SELECT round(100.0 * count(*) FILTER (WHERE cliente_id > 5) / count(*), 1) AS pct
FROM ventas_grandes;

-- Nodo: Parallel Seq Scan
-- Tiempo: 213,166 ms
-- Porcentaje de la tabla: 94,5 %
-- Por qué: La consulta devuelve casi toda la tabla. Pasar por el índice y luego
--          saltar a la tabla fila a fila costaría más que leerla entera de
--          principio a fin. No usar el índice es la decisión correcta.

-- Pregunta 11
EXPLAIN ANALYZE
SELECT count(*), sum(importe)
FROM ventas_grandes
WHERE cliente_id = 42
  AND fecha >= '2024-01-01' AND fecha < '2025-01-01';

-- Nodo: Bitmap Heap Scan sobre un Bitmap Index Scan (idx_ventas_cliente_fecha)
-- Tiempo: 6,395 ms (unas 17 veces más rápido que los 106,637 ms de la P9)
-- Resultado: 4407 ventas, el mismo que en la P9
-- Heap Blocks: exact=3888 (frente a 12.237)
-- Por qué: Con un rango de fechas sin funciones sobre la columna, las dos
--          condiciones entran en el Index Cond y el índice se aprovecha entero.
--          Ya no se descarta ninguna fila después: se leen solo las 4407 que
--          cumplen el filtro.

-- ---------------------------------------------------------------------
-- PARTE D · Vistas y vistas materializadas
-- ---------------------------------------------------------------------

-- Pregunta 12
CREATE VIEW v_facturacion_cliente AS
SELECT cliente_id,
       count(*)     AS ventas,
       sum(importe) AS facturacion
FROM ventas_grandes
GROUP BY cliente_id;

EXPLAIN ANALYZE
SELECT * FROM v_facturacion_cliente
ORDER BY facturacion DESC
LIMIT 3;

-- Nodo: Parallel Seq Scan on ventas_grandes -> Partial HashAggregate ->
--       Gather Merge -> Finalize GroupAggregate -> Sort (top-N heapsort) -> Limit
-- Tiempo: 585,588 ms
-- Por qué: Una vista no guarda datos: es solo una consulta guardada. Cada vez que
--          la usas, PostgreSQL recorre las 2 millones de filas y agrupa de nuevo.

-- Pregunta 13
CREATE MATERIALIZED VIEW mv_facturacion_cliente AS
SELECT cliente_id,
       count(*)     AS ventas,
       sum(importe) AS facturacion
FROM ventas_grandes
GROUP BY cliente_id;

EXPLAIN ANALYZE
SELECT * FROM mv_facturacion_cliente
ORDER BY facturacion DESC
LIMIT 3;

-- Nodo: Seq Scan on mv_facturacion_cliente -> Sort (top-N heapsort) -> Limit
-- Tiempo: 0,039 ms (unas 15.000 veces más rápido que los 585,588 ms de la vista)
-- Por qué: La vista materializada guarda el resultado ya calculado: solo tiene
--          91 filas, una por cliente, y no hay que tocar las 2 millones de ventas.
Por qué:

-- Pregunta 14
INSERT INTO ventas_grandes VALUES (2000001, 35, 1, '2024-12-31', 1000.00);

SELECT * FROM v_facturacion_cliente  WHERE cliente_id = 35;
SELECT * FROM mv_facturacion_cliente WHERE cliente_id = 35;

-- El tiempo del REFRESH se ve en Messages de pgAdmin (EXPLAIN no sirve aquí)
REFRESH MATERIALIZED VIEW mv_facturacion_cliente;

SELECT * FROM v_facturacion_cliente  WHERE cliente_id = 35;
SELECT * FROM mv_facturacion_cliente WHERE cliente_id = 35;

-- Nodo: no aplica
-- Tiempo del REFRESH: PENDIENTE (míralo en Messages; en las diapositivas, 233 ms)
-- Vista tras el INSERT: 35 | 22375 ventas | 5617242.36
-- Vista materializada antes del REFRESH: PENDIENTE (lo esperado: 22374 | 5616242.36)
-- Vista materializada tras el REFRESH: PENDIENTE (lo esperado: 22375 | 5617242.36)
-- Por qué: La vista siempre refleja la venta nueva porque recalcula en cada
--          consulta. La materializada guarda una foto y sigue con los datos
--          viejos hasta el REFRESH. Es el precio de tenerla ya calculada: hay
--          que decidir cada cuánto actualizarla.

-- Pregunta 15
DELETE FROM ventas_grandes WHERE venta_id = 2000001;
REFRESH MATERIALIZED VIEW mv_facturacion_cliente;

-- Comprobación: el cliente 35 vuelve a su valor original
SELECT * FROM mv_facturacion_cliente WHERE cliente_id = 35;

-- Nodo: no aplica
-- Tiempo: no aplica
-- Resultado: 35 | 22374 ventas | 5616242.36 (valor original; la diferencia es
--            justo la venta de 1000.00)
-- Por qué: Hay que refrescar la vista materializada para que deje de incluir
--  

-- =====================================================================
--  TUS TIEMPOS                         Diapositivas      Tu ordenador
-- =====================================================================
--  Cliente 42, sin índice              103 ms
--  Cliente 42, con índice              26 ms / 9 ms
--  cliente_id + 0 = 42                 77 ms
--  EXTRACT(YEAR FROM fecha) = 2024     60 ms
--  cliente_id > 5                      243 ms
--  Vista, top 3                        229 ms
--  Vista materializada, top 3          0,4 ms
--  REFRESH                             233 ms
-- =====================================================================

-- ---------------------------------------------------------------------
-- SI TERMINAS ANTES
-- ---------------------------------------------------------------------
-- Reto 4 · Un trigger de auditoría (diapositiva «Funciones, procedimientos y triggers»). Ejecuta cada bloque por separado.
-- 1) La tabla del historial: una fila por cada cambio de stock
CREATE TABLE historial_stock (
    id             serial PRIMARY KEY,
    product_id     smallint,
    stock_antes    smallint,
    stock_despues  smallint,
    cambiado_en    timestamptz DEFAULT now()
);

-- 2) La función que escribe en el historial (OLD = antes, NEW = después)
CREATE FUNCTION registrar_stock() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    INSERT INTO historial_stock (product_id, stock_antes, stock_despues)
    VALUES (OLD.product_id, OLD.units_in_stock, NEW.units_in_stock);
    RETURN NEW;
END $$;

-- 3) El trigger: después de cada UPDATE de units_in_stock en products
CREATE TRIGGER trg_historial_stock
AFTER UPDATE OF units_in_stock ON products
FOR EACH ROW EXECUTE FUNCTION registrar_stock();

-- 4) Pruébalo
UPDATE products SET units_in_stock = units_in_stock - 10 WHERE product_id = 1;
SELECT * FROM historial_stock;
UPDATE products SET unit_price = unit_price WHERE product_id = 1;
SELECT * FROM historial_stock;

-- 5) Un procedimiento almacenado: mover stock de un producto a otro
CREATE PROCEDURE mover_stock(origen int, destino int, unidades int)
LANGUAGE plpgsql AS $$
BEGIN
    UPDATE products SET units_in_stock = units_in_stock - unidades WHERE product_id = origen;
    UPDATE products SET units_in_stock = units_in_stock + unidades WHERE product_id = destino;
END $$;
CALL mover_stock(2, 1, 10);
SELECT * FROM historial_stock ORDER BY id;

-- 6) Deja todo como estaba: el stock de partida (Chai 39, Chang 17) y sin trigger
CALL mover_stock(1, 2, 10);
UPDATE products SET units_in_stock = units_in_stock + 10 WHERE product_id = 1;
SELECT product_id, product_name, units_in_stock FROM products WHERE product_id <= 2;
DROP TRIGGER trg_historial_stock ON products;
DROP FUNCTION registrar_stock();
DROP PROCEDURE mover_stock(int, int, int);
DROP TABLE historial_stock;

-- Reto 4 · Fila que aparece al restar 10 a Chai:
--          ¿Aparece otra al cambiar el precio? ¿Por qué?
--          Filas que añade CALL mover_stock(2, 1, 10) y por qué:
