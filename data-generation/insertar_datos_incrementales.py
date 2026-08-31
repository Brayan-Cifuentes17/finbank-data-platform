import pyodbc
import random
import yaml
import sys
from datetime import datetime, timedelta


def cargar_db_config(path="db_config.yaml"):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"ERROR: no se encontro '{path}'.")
        sys.exit(1)


IDS_CLIENTE_VALIDOS = list(range(100000, 110000))
PRODUCTOS_VALIDOS = [f"PROD-{i:03d}" for i in range(1, 51)]
CANALES = ["App Movil", "Portal Web", "Cajero Automatico", "Corresponsal Bancario"]
CIUDADES = ["Bogota", "Medellin", "Cali", "Barranquilla", "Lima", "Santiago",
            "Ciudad de Mexico", "Guadalajara", "Buenos Aires"]
TIPOS_MOV = ["pago_capital", "pago_interes", "transferencia", "retiro", "compra_tc", "desembolso"]

HOY = datetime.now()
N_MOVIMIENTOS_NUEVOS = 40
N_COMISIONES_NUEVAS = 15


def generar_id_mov(n):
    return f"MOV-INC-{n:04d}"


def generar_id_comision(n):
    return f"COM-INC-{n:04d}"


def insertar_movimientos(cursor):
    print(f"Insertando {N_MOVIMIENTOS_NUEVOS} movimientos nuevos con fecha {HOY.date()}...")
    for i in range(N_MOVIMIENTOS_NUEVOS):
        id_mov = generar_id_mov(i)
        id_cli = random.choice(IDS_CLIENTE_VALIDOS)
        cod_prod = random.choice(PRODUCTOS_VALIDOS)
        fec_mov = HOY.date()
        hra_mov = HOY.replace(
            hour=random.randint(6, 22), minute=random.randint(0, 59), second=random.randint(0, 59)
        ).time()
        vr_mov = round(random.uniform(5000, 300000), 2)
        tip_mov = random.choice(TIPOS_MOV)
        cod_canal = random.choice(CANALES)
        cod_ciudad = random.choice(CIUDADES)
        cod_estado_mov = "Aprobado"
        id_dispositivo = f"DEV-{random.randint(100000, 999999)}"
        num_cuenta = f"{random.randint(1000000000, 9999999999)}"

        cursor.execute("""
            INSERT INTO TB_MOV_FINANCIEROS
            (id_mov, id_cli, cod_prod, fec_mov, hra_mov, vr_mov, tip_mov,
             cod_canal, cod_ciudad, cod_estado_mov, id_dispositivo, num_cuenta)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, id_mov, id_cli, cod_prod, fec_mov, hra_mov, vr_mov, tip_mov,
             cod_canal, cod_ciudad, cod_estado_mov, id_dispositivo, num_cuenta)

    print(f"  {N_MOVIMIENTOS_NUEVOS} movimientos insertados.")


def insertar_comisiones(cursor):
    print(f"Insertando {N_COMISIONES_NUEVAS} comisiones nuevas con fecha {HOY.date()}...")
    tipos_comision = ["Comision Retiro Cajero", "Comision Transferencia",
                       "Comision Manejo Cuenta", "Comision Administracion"]
    for i in range(N_COMISIONES_NUEVAS):
        id_comision = generar_id_comision(i)
        id_cli = random.choice(IDS_CLIENTE_VALIDOS)
        cod_prod = random.choice(PRODUCTOS_VALIDOS)
        fec_cobro = HOY.date()
        vr_comision = round(random.uniform(2000, 40000), 2)
        tip_comision = random.choice(tipos_comision)
        estado_cobro = "Cobrado"

        cursor.execute("""
            INSERT INTO TB_COMISIONES_LOG
            (id_comision, id_cli, cod_prod, fec_cobro, vr_comision, tip_comision, estado_cobro)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, id_comision, id_cli, cod_prod, fec_cobro, vr_comision, tip_comision, estado_cobro)

    print(f"  {N_COMISIONES_NUEVAS} comisiones insertadas.")


def main():
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
    cursor = conn.cursor()

    insertar_movimientos(cursor)
    insertar_comisiones(cursor)

    conn.commit()
    print("\nCommit exitoso. Datos nuevos disponibles en el origen.")
    print(f"Ahora corre pl_finbank_master -- Bronze deberia capturar SOLO estas "
          f"{N_MOVIMIENTOS_NUEVOS + N_COMISIONES_NUEVAS} filas nuevas (mas lo que "
          f"ya estaba pendiente por el checkpoint), demostrando carga Delta real.")

    cursor.close()
    conn.close()


if __name__ == "__main__":
    main()
