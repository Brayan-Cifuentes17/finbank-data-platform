import yaml
import pandas as pd
import pyodbc
import math
import sys


def cargar_db_config(path="db_config.yaml"):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"ERROR: no se encontro '{path}'.")
        sys.exit(1)


DDL_TABLAS = {
    "TB_CLIENTES_CORE": """
        CREATE TABLE TB_CLIENTES_CORE (
            id_cli INT PRIMARY KEY,
            nomb_cli NVARCHAR(100),
            apell_cli NVARCHAR(100),
            tip_doc NVARCHAR(10),
            num_doc NVARCHAR(20),
            fec_nac DATE,
            fec_alta DATE,
            cod_segmento NVARCHAR(20),
            score_buro INT NULL,
            ciudad_res NVARCHAR(50),
            depto_res NVARCHAR(50) NULL,
            estado_cli NVARCHAR(20),
            canal_adquis NVARCHAR(30)
        )
    """,
    "TB_PRODUCTOS_CAT": """
        CREATE TABLE TB_PRODUCTOS_CAT (
            cod_prod NVARCHAR(20) PRIMARY KEY,
            desc_prod NVARCHAR(100),
            tip_prod NVARCHAR(50),
            tasa_ea DECIMAL(6,4),
            plazo_max_meses INT,
            cuota_min DECIMAL(18,2),
            comision_admin DECIMAL(18,2),
            estado_prod NVARCHAR(20)
        )
    """,
    "TB_SUCURSALES_RED": """
        CREATE TABLE TB_SUCURSALES_RED (
            cod_suc NVARCHAR(20) PRIMARY KEY,
            nom_suc NVARCHAR(100),
            tip_punto NVARCHAR(30),
            ciudad NVARCHAR(50),
            depto NVARCHAR(50),
            latitud DECIMAL(9,6),
            longitud DECIMAL(9,6),
            activo BIT
        )
    """,
    "TB_OBLIGACIONES": """
        CREATE TABLE TB_OBLIGACIONES (
            id_oblig NVARCHAR(20) PRIMARY KEY,
            id_cli INT,
            cod_prod NVARCHAR(20),
            vr_aprobado DECIMAL(18,2),
            vr_desembolsado DECIMAL(18,2),
            sdo_capital DECIMAL(18,2),
            vr_cuota DECIMAL(18,2),
            fec_desembolso DATE,
            fec_venc DATE,
            dias_mora_act INT,
            num_cuotas_pend INT,
            calif_riesgo NVARCHAR(10)
        )
    """,
    "TB_MOV_FINANCIEROS": """
        CREATE TABLE TB_MOV_FINANCIEROS (
            id_mov NVARCHAR(20) PRIMARY KEY,
            id_cli INT,
            cod_prod NVARCHAR(20),
            num_cuenta NVARCHAR(30),
            fec_mov DATE,
            hra_mov TIME,
            vr_mov DECIMAL(18,2),
            tip_mov NVARCHAR(30),
            cod_canal NVARCHAR(30),
            cod_ciudad NVARCHAR(50),
            cod_estado_mov NVARCHAR(20),
            id_dispositivo NVARCHAR(20) NULL
        )
    """,
    "TB_COMISIONES_LOG": """
        CREATE TABLE TB_COMISIONES_LOG (
            id_comision NVARCHAR(20) PRIMARY KEY,
            id_cli INT,
            cod_prod NVARCHAR(20),
            fec_cobro DATE,
            vr_comision DECIMAL(18,2),
            tip_comision NVARCHAR(50),
            estado_cobro NVARCHAR(20)
        )
    """,
}

ARCHIVOS_ORIGEN = {
    "TB_CLIENTES_CORE": ("tb_clientes_core.csv", "csv"),
    "TB_PRODUCTOS_CAT": ("tb_productos_cat.json", "json"),
    "TB_SUCURSALES_RED": ("tb_sucursales_red.json", "json"),
    "TB_OBLIGACIONES": ("tb_obligaciones.csv", "csv"),
    "TB_MOV_FINANCIEROS": ("tb_mov_financieros.csv", "csv"),
    "TB_COMISIONES_LOG": ("tb_comisiones_log.csv", "csv"),
}

DDL_TABLAS["TB_MOV_FINANCIEROS"] = DDL_TABLAS["TB_MOV_FINANCIEROS"].replace(
    "id_mov NVARCHAR(20) PRIMARY KEY,", "id_mov NVARCHAR(20),"
)


def crear_tablas(conn):
    cursor = conn.cursor()
    cursor.fast_executemany = False
    for nombre_tabla, ddl in DDL_TABLAS.items():
        cursor.execute(f"IF OBJECT_ID('{nombre_tabla}', 'U') IS NOT NULL DROP TABLE {nombre_tabla}")
        cursor.execute(ddl)
        print(f"  Tabla {nombre_tabla} creada.")
    conn.commit()
    cursor.close()


def _valor_limpio(v):
    if v is None:
        return None
    if isinstance(v, float) and math.isnan(v):
        return None
    return v


def cargar_tabla(conn, nombre_tabla, archivo, formato, carpeta_output):
    ruta = f"{carpeta_output}/{archivo}"
    df = pd.read_json(ruta) if formato == "json" else pd.read_csv(ruta)

    columnas = ",".join(df.columns)
    placeholders = ",".join(["?"] * len(df.columns))
    insert_sql = f"INSERT INTO {nombre_tabla} ({columnas}) VALUES ({placeholders})"

    cursor = conn.cursor()
    cursor.fast_executemany = True
    registros = [
        tuple(_valor_limpio(v) for v in row)
        for row in df.itertuples(index=False, name=None)
    ]

    batch_size = 20000
    
    total = len(registros)
    for i in range(0, total, batch_size):
        lote = registros[i:i + batch_size]
        cursor.executemany(insert_sql, lote)
        conn.commit()
        print(f"    {min(i + batch_size, total):,} / {total:,} registros cargados...", end="\r")

    print(f"  {nombre_tabla}: {total:,} registros cargados desde {archivo}.          ")
    cursor.close()


def verificar_carga(conn):
    print("\n---Evidencia de carga: SELECT COUNT(*) por tabla---")
    cursor = conn.cursor()
    for nombre_tabla in DDL_TABLAS.keys():
        cursor.execute(f"SELECT COUNT(*) FROM {nombre_tabla}")
        count = cursor.fetchone()[0]
        print(f"  {nombre_tabla:22s} {count:>8,} registros")
    cursor.close()


if __name__ == "__main__":
    cfg = cargar_db_config()

    print(f"Conectando a {cfg['server']}...")
    conn_str = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={cfg['server']};"
        f"DATABASE={cfg['database']};"
        f"UID={cfg['user']};"
        f"PWD={cfg['password']};"
        "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
    )
    conn = pyodbc.connect(conn_str)
    print("Conexion exitosa.\n")

    print("Creando las 6 tablas...")
    crear_tablas(conn)

    print("\nCargando datos...")
    for nombre_tabla, (archivo, formato) in ARCHIVOS_ORIGEN.items():
        cargar_tabla(conn, nombre_tabla, archivo, formato, carpeta_output="output")

    verificar_carga(conn)

    conn.close()
    print("\nCarga completa.")
