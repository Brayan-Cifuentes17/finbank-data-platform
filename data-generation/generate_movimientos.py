import random
import numpy as np
import pandas as pd
from datetime import date, datetime, timedelta
from generate_clientes import cargar_config


def generar_movimientos(config: dict, df_clientes: pd.DataFrame, df_productos: pd.DataFrame) -> pd.DataFrame:
    seed = config["seed"]
    random.seed(seed + 4)
    np.random.seed(seed + 4)

    n_base = config["volumenes"]["movimientos"]
    fecha_inicio = date.fromisoformat(config["periodo"]["fecha_inicio"])
    fecha_fin = date.fromisoformat(config["periodo"]["fecha_fin"])
    dias_totales = (fecha_fin - fecha_inicio).days

    pct = config["anomalias"]
    n_duplicados = int(n_base * pct["pct_duplicados"])
    n_fechas_malas = int(n_base * pct["pct_fechas_fuera_rango"])
    n_huerfanos = int(n_base * pct["pct_ids_huerfanos"])
    n_montos_malos = int(n_base * pct["pct_montos_invalidos"])
    n_limpios = n_base - n_fechas_malas - n_huerfanos - n_montos_malos

    ids_clientes = df_clientes["id_cli"].tolist()
    ids_productos = df_productos[df_productos["estado_prod"] == "Activo"]["cod_prod"].tolist()


    cuentas_por_cliente = {
        cli: f"CTA-{random.randint(10**9, 10**10 - 1)}" for cli in ids_clientes
    }


    tipos_mov = ["pago_interes", "pago_capital", "desembolso", "compra_tc", "retiro", "transferencia"]
    pesos_tipos_mov = [0.20, 0.25, 0.10, 0.20, 0.15, 0.10]

    canales = ["App Movil", "Portal Web", "Corresponsal Bancario", "Cajero Automatico"]
    pesos_canales = [0.45, 0.30, 0.15, 0.10]

    estados_mov = ["Aprobado", "Rechazado", "Pendiente"]
    pesos_estados = [0.94, 0.04, 0.02]

    ciudades_pool = df_clientes["ciudad_res"].unique().tolist()

    def _hora_pico():
        """Distribución de horas concentrada en horario laboral con picos 12pm y 6pm."""
        r = random.random()
        if r < 0.20:
            return random.randint(11, 13)   
        elif r < 0.45:
            return random.randint(17, 19)   
        elif r < 0.90:
            return random.randint(8, 21)    
        else:
            return random.randint(0, 23)    

    def _monto_lognormal():

        return round(float(np.random.lognormal(mean=10.5, sigma=1.1)), 0)

    def _fila_base(id_cli, cod_prod, fec_mov_dt, vr_mov, tip_mov):
        return {
            "id_mov": None,  
            "id_cli": id_cli,
            "cod_prod": cod_prod,
            "num_cuenta": cuentas_por_cliente.get(id_cli, f"CTA-{random.randint(10**9, 10**10-1)}"),
            "fec_mov": fec_mov_dt.date().isoformat(),
            "hra_mov": fec_mov_dt.strftime("%H:%M:%S"),
            "vr_mov": vr_mov,
            "tip_mov": tip_mov,
            "cod_canal": np.random.choice(canales, p=pesos_canales),
            "cod_ciudad": random.choice(ciudades_pool),
            "cod_estado_mov": np.random.choice(estados_mov, p=pesos_estados),
            "id_dispositivo": f"DEV-{random.randint(100000,999999)}",
        }

    registros = []
 
    for _ in range(n_limpios):
        id_cli = random.choice(ids_clientes)
        cod_prod = random.choice(ids_productos)
        dia_offset = random.randint(0, dias_totales)
        hora = _hora_pico()
        fec_mov_dt = datetime.combine(fecha_inicio, datetime.min.time()) + timedelta(
            days=dia_offset, hours=hora, minutes=random.randint(0, 59), seconds=random.randint(0, 59)
        )
        vr_mov = _monto_lognormal()
        tip_mov = np.random.choice(tipos_mov, p=pesos_tipos_mov)
        registros.append(_fila_base(id_cli, cod_prod, fec_mov_dt, vr_mov, tip_mov))

    #echas fuera de rango
    for _ in range(n_fechas_malas):
        id_cli = random.choice(ids_clientes)
        cod_prod = random.choice(ids_productos)

        if random.random() < 0.5:
            fec_mov_dt = datetime(random.randint(2005, 2014), random.randint(1, 12), random.randint(1, 28))
        else:
            fec_mov_dt = datetime(2030, random.randint(1, 12), random.randint(1, 28))
        vr_mov = _monto_lognormal()
        tip_mov = np.random.choice(tipos_mov, p=pesos_tipos_mov)
        fila = _fila_base(id_cli, cod_prod, fec_mov_dt, vr_mov, tip_mov)
        registros.append(fila)

    #Anomalia IDs huerfanos 
    max_id_valido = max(ids_clientes)
    for _ in range(n_huerfanos):
        id_cli_huerfano = max_id_valido + random.randint(1, 99999) 
        cod_prod = random.choice(ids_productos)
        dia_offset = random.randint(0, dias_totales)
        fec_mov_dt = datetime.combine(fecha_inicio, datetime.min.time()) + timedelta(days=dia_offset, hours=_hora_pico())
        vr_mov = _monto_lognormal()
        tip_mov = np.random.choice(tipos_mov, p=pesos_tipos_mov)
        fila = _fila_base(id_cli_huerfano, cod_prod, fec_mov_dt, vr_mov, tip_mov)
        registros.append(fila)

    #anomalia montos invalidos 
    for _ in range(n_montos_malos):
        id_cli = random.choice(ids_clientes)
        cod_prod = random.choice(ids_productos)
        dia_offset = random.randint(0, dias_totales)
        fec_mov_dt = datetime.combine(fecha_inicio, datetime.min.time()) + timedelta(days=dia_offset, hours=_hora_pico())
        vr_mov = random.choice([0, -round(random.uniform(1000, 50000), 0)])
        tip_mov = np.random.choice(tipos_mov, p=pesos_tipos_mov)
        fila = _fila_base(id_cli, cod_prod, fec_mov_dt, vr_mov, tip_mov)
        registros.append(fila)

    # 
    for i, r in enumerate(registros):
        r["id_mov"] = f"MOV-{i+1:07d}"

    df = pd.DataFrame(registros)

    filas_a_duplicar = df.sample(n=n_duplicados, random_state=seed)
    df = pd.concat([df, filas_a_duplicar], ignore_index=True) 

    return df.sample(frac=1, random_state=seed).reset_index(drop=True)


if __name__ == "__main__":
    cfg = cargar_config()
    out_dir = cfg["salida"]["directorio"]

    df_clientes = pd.read_csv(f"{out_dir}/tb_clientes_core.csv")
    df_productos = pd.read_json(f"{out_dir}/tb_productos_cat.json")

    df_mov = generar_movimientos(cfg, df_clientes, df_productos)
    df_mov.to_csv(f"{out_dir}/tb_mov_financieros.csv", index=False, encoding="utf-8")

    print(f"Generados {len(df_mov)} movimientos = {out_dir}/tb_mov_financieros.csv")
    print(df_mov.head(5).to_string())

    print("\n=== Verificación de las 4 anomalias intencionales ===")
    dup = df_mov["id_mov"].duplicated().sum()
    print(f"1. Duplicados exactos (id_mov repetido): {dup}")

    fechas = pd.to_datetime(df_mov["fec_mov"])
    fuera_rango = ((fechas.dt.year < 2015) | (fechas.dt.year > 2027)).sum()
    print(f"2. Fechas fuera de rango: {fuera_rango}")

    huerfanos = (~df_mov["id_cli"].isin(df_clientes["id_cli"])).sum()
    print(f"3. IDs huerfanos (id_cli inexistente): {huerfanos}")

    invalidos = (df_mov["vr_mov"] <= 0).sum()
    print(f"4. Montos invalidos (vr_mov <= 0): {invalidos}")

    print(f"\nTotal de filas con alguna anomalia: {dup + fuera_rango + huerfanos + invalidos} de {len(df_mov)}")

    print("\nDistribucion de tip_mov :")
    print(df_mov["tip_mov"].value_counts(normalize=True).round(3))

    print("\nDistribucion de hra_mov agrupada por franja ")
    horas = pd.to_datetime(df_mov["hra_mov"], format="%H:%M:%S").dt.hour
    print(pd.cut(horas, bins=[-1, 7, 10, 13, 16, 19, 23],
                 labels=["madrugada(0-7)", "manana(8-10)", "pico_almuerzo(11-13)",
                         "tarde(14-16)", "pico_salida(17-19)", "noche(20-23)"]
                 ).value_counts(normalize=True).round(3))

    print("\nEstadísticas de vr_mov ")
    print(df_mov[df_mov["vr_mov"] > 0]["vr_mov"].describe())
