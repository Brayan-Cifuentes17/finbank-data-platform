DROP TABLE IF EXISTS control_ingestas;

CREATE TABLE control_ingestas (
    nombre_tabla NVARCHAR(50) PRIMARY KEY,
    tipo_carga_default NVARCHAR(10) NOT NULL,   -- 'Full' o 'Delta'
    columna_control NVARCHAR(30) NULL,           -- NULL para las tablas Full (no aplica)
    checkpoint_date DATETIME NULL                -- hasta dónde se ha procesado (solo Delta)
);

INSERT INTO control_ingestas (nombre_tabla, tipo_carga_default, columna_control, checkpoint_date)
VALUES
    ('TB_CLIENTES_CORE',   'Full',  NULL,        NULL),
    ('TB_PRODUCTOS_CAT',   'Full',  NULL,        NULL),
    ('TB_SUCURSALES_RED',  'Full',  NULL,        NULL),
    ('TB_OBLIGACIONES',    'Full',  NULL,        NULL),
    ('TB_MOV_FINANCIEROS', 'Delta', 'fec_mov',   '2025-08-27'),
    ('TB_COMISIONES_LOG',  'Delta', 'fec_cobro', '2025-08-27');

SELECT * FROM control_ingestas;

