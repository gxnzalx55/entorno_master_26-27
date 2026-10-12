-- =====================================================================
--  EL CASO DE LA CAJA PERDIDA  ·  misterio SQL sobre Northwind
--  Se carga automáticamente al arrancar el contenedor (después de 01_northwind.sql).
--  Crea el esquema "caso" con cinco tablas de pistas. Las tablas de Northwind
--  (customers, orders, order_details, products, shippers, employees...)
--  forman parte de la investigación.
-- =====================================================================

DROP SCHEMA IF EXISTS caso CASCADE;
CREATE SCHEMA caso;

-- ---------------------------------------------------------------------
-- 1. Registro de incidentes
-- ---------------------------------------------------------------------
CREATE TABLE caso.incidentes (
    incidente_id  serial PRIMARY KEY,
    fecha         date NOT NULL,
    lugar         text NOT NULL,
    descripcion   text NOT NULL
);

INSERT INTO caso.incidentes (fecha, lugar, descripcion) VALUES
('1998-03-02', 'Almacén de Seattle', 'Una carretilla golpea una estantería de conservas. Sin pérdidas de mercancía.'),
('1998-03-19', 'Almacén de Londres', 'Retraso en la salida de pedidos por huelga de transporte. Todos los pedidos salen al día siguiente.'),
('1998-04-06', 'Oficina de Tacoma',  'Se detecta un error en la facturación de un cliente de Alemania. Corregido por el departamento de ventas.'),
('1998-04-15', 'Almacén de Londres', 'Reclamación de un cliente de Madrid: el pedido llegó con dos días de retraso. El transportista lo atribuye a la niebla.'),
('1998-04-28', 'Almacén de Londres', 'Reclamación de un cliente de Sevilla: su ÚLTIMO pedido llegó con una caja menos. '
                                      'El conductor de la empresa de transporte que llevó ese pedido prestó declaración '
                                      'al día siguiente de la fecha de envío. Busca su declaración en caso.declaraciones.'),
('1998-04-28', 'Almacén de Seattle', 'Reclamación de un cliente de Barcelona por un error en la dirección de envío. No hay pérdida de mercancía.'),
('1998-05-04', 'Almacén de Londres', 'Revisión de inventario. Se confirma que falta una caja de cerveza desde finales de abril.');

-- ---------------------------------------------------------------------
-- 2. Declaraciones de testigos externos (transportistas)
-- ---------------------------------------------------------------------
CREATE TABLE caso.declaraciones (
    declaracion_id  serial PRIMARY KEY,
    fecha           date NOT NULL,
    nombre          text NOT NULL,
    empresa         text NOT NULL,
    declaracion     text NOT NULL
);

INSERT INTO caso.declaraciones (fecha, nombre, empresa, declaracion) VALUES
('1998-04-16', 'Peter Wilson',  'United Package',
 'El retraso del pedido de Madrid fue por la niebla en el aeropuerto. Nadie tocó la mercancía.'),
('1998-04-28', 'Mary Jones',    'Federal Shipping',
 'Ese día recogí tres pedidos en Londres por la tarde. Todo iba precintado y completo.'),
('1998-04-28', 'Tom Baker',     'United Package',
 'Recogí dos pedidos en Seattle a mediodía. Me los entregó el mismo vendedor que figuraba en el pedido.'),
('1998-04-28', 'Jack Robinson', 'Speedy Express',
 'Recogí el pedido en la puerta del almacén a primera hora, antes de las 8:00. '
 'NO me lo entregó el vendedor que figura en el pedido, sino un compañero de su misma oficina (la misma ciudad) '
 'que tiene el mismo jefe que él. Para abrir la puerta usó su tarjeta de acceso: me fijé en que el número '
 'de la tarjeta es el mismo que su extensión telefónica. Los accesos quedan registrados en caso.fichajes.'),
('1998-04-29', 'Jack Robinson', 'Speedy Express',
 'Quiero añadir que la caja pesaba menos de lo normal, pero no le di importancia.'),
('1998-04-29', 'Sam Porter',    'Federal Shipping',
 'Yo no trabajé el día 27. Estuve de baja toda la semana.');

-- ---------------------------------------------------------------------
-- 3. Fichajes de las puertas (el número de tarjeta es la extensión telefónica del empleado)
-- ---------------------------------------------------------------------
CREATE TABLE caso.fichajes (
    fichaje_id   serial PRIMARY KEY,
    fecha        date NOT NULL,
    hora         time NOT NULL,
    oficina      text NOT NULL,
    puerta       text NOT NULL,
    num_tarjeta  varchar(4) NOT NULL
);

INSERT INTO caso.fichajes (fecha, hora, oficina, puerta, num_tarjeta) VALUES
('1998-04-26', '06:30', 'London',  'Almacén',   '428'),
('1998-04-26', '09:05', 'London',  'Principal', '465'),
('1998-04-27', '06:48', 'London',  'Almacén',   '452'),
('1998-04-27', '06:55', 'London',  'Almacén',   '3453'),
('1998-04-27', '07:20', 'Seattle', 'Almacén',   '2344'),
('1998-04-27', '08:40', 'London',  'Almacén',   '428'),
('1998-04-27', '09:02', 'London',  'Principal', '428'),
('1998-04-27', '09:15', 'London',  'Principal', '465'),
('1998-04-27', '09:30', 'Seattle', 'Principal', '5467'),
('1998-04-27', '10:10', 'Tacoma',  'Principal', '3457'),
('1998-04-28', '06:50', 'London',  'Almacén',   '452'),
('1998-04-28', '09:00', 'London',  'Principal', '428');

-- ---------------------------------------------------------------------
-- 4. Interrogatorios a la plantilla de Northwind (uno por empleado)
-- ---------------------------------------------------------------------
CREATE TABLE caso.interrogatorios (
    employee_id  smallint PRIMARY KEY REFERENCES public.employees (employee_id),
    fecha        date NOT NULL,
    declaracion  text NOT NULL
);

INSERT INTO caso.interrogatorios (employee_id, fecha, declaracion) VALUES
(1, '1998-04-30', 'El 27 estuve en Seattle todo el día preparando la visita de un cliente. No sé nada de ninguna caja.'),
(2, '1998-04-30', 'Como vicepresidente no bajo nunca al almacén. Supongo que habrá sido un error de inventario.'),
(3, '1998-04-30', 'La noche del 25 llamé a Londres para cerrar un pedido de un cliente de Irlanda. Nada más.'),
(4, '1998-04-30', 'El 26 hice varias llamadas a Londres para revisar precios. Es lo normal a fin de mes.'),
(5, '1998-04-30', 'Llegué pronto el 27 porque tenía que revisar unos albaranes. Mi equipo es de total confianza.'),
(6, '1998-04-30', 'El día 27 llegué a la oficina a las nueve, como siempre. Pueden comprobarlo en los fichajes.'),
(7, '1998-04-30', 'Yo gestioné ese pedido, pero cuando llegué ya había salido. Me pareció raro, pero no pregunté.'),
(8, '1998-04-30', 'Yo coordino las ventas desde Seattle. El 26 llamé a varias oficinas para cuadrar la agenda.'),
(9, '1998-04-30', 'Si me preguntan por la caja, solo diré que yo no decidí nada. La noche anterior al envío alguien me llamó a mi '
                  'extensión y me dio instrucciones. No sé quién era; solo sé que presumía de haber sido en 1997 el número uno '
                  'en ventas de su ciudad, aunque no de toda la empresa. Las llamadas internas quedan en caso.llamadas.');

-- ---------------------------------------------------------------------
-- 5. Registro de llamadas internas (extensión de origen -> extensión de destino)
-- ---------------------------------------------------------------------
CREATE TABLE caso.llamadas (
    llamada_id    serial PRIMARY KEY,
    fecha         date NOT NULL,
    hora          time NOT NULL,
    ext_origen    varchar(4) NOT NULL,
    ext_destino   varchar(4) NOT NULL,
    duracion_seg  integer NOT NULL
);

INSERT INTO caso.llamadas (fecha, hora, ext_origen, ext_destino, duracion_seg) VALUES
('1998-04-25', '18:10', '3355', '452',  240),
('1998-04-26', '10:15', '3453', '452',   60),
('1998-04-26', '16:40', '5176', '452',  120),
('1998-04-26', '21:47', '3457', '452',  310),
('1998-04-26', '22:05', '2344', '452',   45),
('1998-04-26', '12:00', '5176', '428',   30),
('1998-04-27', '11:00', '465',  '428',   90),
('1998-04-27', '12:30', '3457', '3453', 180);

COMMENT ON SCHEMA caso IS 'Misterio SQL de clase: El caso de la caja perdida';
