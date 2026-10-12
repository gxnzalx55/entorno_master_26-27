-- =====================================================================
--  CAPA ORO · Northwind como modelo en estrella para Power BI
--  Almacenamiento, visualización y procesamiento de datos · Sesión 8
--
--  Hechos:      oro.fact_ventas    una fila por línea de pedido
--  Dimensiones: oro.dim_fecha      hecha
--               oro.dim_empleado   hecha
--               oro.dim_producto   la escribes tú (A COMPLETAR)
--               oro.dim_cliente    la escribes tú (A COMPLETAR)
--
--  Son vistas: no copian datos, se calculan cada vez que alguien las
--  consulta. Power BI las ve como si fueran tablas.
--  Cómo se usa: ábrelo en pgAdmin (Query Tool sobre northwind), completa
--  las dos dimensiones y ejecuta el fichero entero (F5). Se puede
--  ejecutar las veces que haga falta: CREATE OR REPLACE sustituye la vista.
-- =====================================================================

CREATE SCHEMA IF NOT EXISTS oro;

-- ---------------------------------------------------------------------
-- HECHOS · granularidad: una fila por pedido y producto (línea de pedido)
-- Se pasan los precios a numeric para que el importe sea exacto, sin los
-- decimales sueltos de los números de coma flotante.
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW oro.fact_ventas AS
SELECT od.order_id                    AS pedido_id,
       od.product_id                  AS producto_id,
       o.customer_id                  AS cliente_id,
       o.employee_id                  AS empleado_id,
       o.order_date                   AS fecha_pedido,
       o.shipped_date                 AS fecha_envio,       -- vacía si el pedido no se ha enviado
       od.quantity                    AS cantidad,
       od.unit_price::numeric         AS precio_unitario,
       od.discount::numeric           AS descuento,
       od.unit_price::numeric * od.quantity * (1 - od.discount::numeric) AS importe
FROM order_details od
JOIN orders o ON o.order_id = od.order_id;

-- ---------------------------------------------------------------------
-- DIMENSIÓN FECHA · un día por fila, años completos y sin huecos
-- Power BI solo deja marcar una tabla como «tabla de fechas» si las fechas
-- son únicas y continuas.
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW oro.dim_fecha AS
SELECT d::date                                        AS fecha,
       extract(year    FROM d)::int                   AS anio,
       'T' || extract(quarter FROM d)::int            AS trimestre,
       extract(month   FROM d)::int                   AS mes,
       (ARRAY['enero','febrero','marzo','abril','mayo','junio','julio','agosto',
              'septiembre','octubre','noviembre','diciembre'])[extract(month FROM d)::int] AS nombre_mes,
       to_char(d, 'YYYY-MM')                          AS anio_mes,
       extract(isodow  FROM d)::int                   AS dia_semana   -- 1 = lunes, 7 = domingo
FROM generate_series(DATE '1996-01-01', DATE '1998-12-31', INTERVAL '1 day') AS d;

-- ---------------------------------------------------------------------
-- DIMENSIÓN EMPLEADO · con el nombre de su jefe (la tabla se une consigo misma)
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW oro.dim_empleado AS
SELECT e.employee_id                                AS empleado_id,
       e.first_name || ' ' || e.last_name           AS empleado,
       e.last_name                                  AS apellido,
       e.title                                      AS cargo,
       e.city                                       AS ciudad,
       e.country                                    AS pais,
       coalesce(j.first_name || ' ' || j.last_name, '(sin jefe)') AS jefe
FROM employees e
LEFT JOIN employees j ON j.employee_id = e.reports_to;

-- ---------------------------------------------------------------------
-- DIMENSIÓN PRODUCTO · A COMPLETAR
-- Una fila por producto con estas columnas:
--   producto_id, producto, categoria, proveedor, pais_proveedor y descatalogado
-- La categoría está en categories y el proveedor en suppliers: hacen falta
-- dos JOIN. Así el copo de nieve (products → categories) queda aplanado.
-- descatalogado: en products es un entero (0 o 1); conviértelo en verdadero
-- o falso con  p.discontinued = 1
-- ---------------------------------------------------------------------
-- COMPLETA: quita los dos guiones de cada línea y termina la consulta
-- CREATE OR REPLACE VIEW oro.dim_producto AS
-- SELECT p.product_id    AS producto_id,
--        ...
-- FROM products p
-- JOIN ...
-- JOIN ...;

-- ---------------------------------------------------------------------
-- DIMENSIÓN CLIENTE · A COMPLETAR
-- Una fila por cliente con estas columnas:
--   cliente_id (customer_id), cliente (company_name), ciudad, region y pais
-- Deja region tal como viene, con sus valores vacíos: la limpiaremos en
-- Power Query.
-- ---------------------------------------------------------------------
-- COMPLETA: quita los dos guiones de cada línea y termina la consulta
-- CREATE OR REPLACE VIEW oro.dim_cliente AS
-- SELECT customer_id     AS cliente_id,
--        ...
-- FROM customers;

-- ---------------------------------------------------------------------
-- COMPROBACIONES · ejecútalas después de crear las vistas
-- ---------------------------------------------------------------------
-- 1) Filas de cada tabla: 2.155 líneas, 1.096 fechas, 9 empleados,
--    77 productos y 91 clientes
SELECT (SELECT count(*) FROM oro.fact_ventas)  AS lineas,
       (SELECT count(*) FROM oro.dim_fecha)    AS fechas,
       (SELECT count(*) FROM oro.dim_empleado) AS empleados,
       (SELECT count(*) FROM oro.dim_producto) AS productos,
       (SELECT count(*) FROM oro.dim_cliente)  AS clientes;

-- 2) La granularidad: cada pareja pedido y producto aparece una sola vez
--    (las dos cifras tienen que ser iguales: 2.155)
SELECT count(*) AS filas,
       count(DISTINCT (pedido_id, producto_id)) AS parejas_distintas
FROM oro.fact_ventas;

-- 3) Facturación total: 1.265.793,04
SELECT round(sum(importe), 2) AS facturacion FROM oro.fact_ventas;

-- 4) Facturación por empleado en 1997: Peacock, 128.809,79
--    (la misma cifra servirá en la sesión 9 para comprobar la primera medida DAX)
SELECT e.apellido, round(sum(f.importe), 2) AS facturacion_1997
FROM oro.fact_ventas f
JOIN oro.dim_empleado e ON e.empleado_id = f.empleado_id
WHERE f.fecha_pedido BETWEEN DATE '1997-01-01' AND DATE '1997-12-31'
GROUP BY e.apellido
ORDER BY facturacion_1997 DESC;
