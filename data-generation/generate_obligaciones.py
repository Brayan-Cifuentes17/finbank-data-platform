import random
import numpy as np
import pandas as pd
from datetime import date, timedelta
from generate_clientes import cargar_config


def generar_obligaciones(config: dict, df_clientes: pd.DataFrame, df_productos: pd.DataFrame) -> pd.DataFrame:
    seed = config["seed"]
    random.seed(seed + 3)
    np.random.seed(seed + 3)

    n = config["volumenes"]["obligaciones"]
    fecha_inicio = date.fromisoformat(config["periodo"]["fecha_inicio"])
    fecha_fin = date.fromisoformat(config["periodo"]["fecha_fin"])

    
    ids_clientes = df_clientes["id_cli"].tolist()
    productos_credito = df_productos[df_productos["tip_prod"].isin(
        ["Credito Libre Inversion", "Credito Rotativo", "Tarjeta Digital"]
    )][["cod_prod", "tasa_ea", "plazo_max_meses", "cuota_min"]].to_dict("records")

    if not productos_credito:
        raise ValueError("No hay productos de credito generados")

    buckets = [
        (0, 0, 0.80),        # al dia
        (1, 30, 0.10),       # rango 1
        (31, 60, 0.05),      # rango 2
        (61, 90, 0.03),      # rango 3
        (91, 365, 0.02),     # deteriorado
    ]
    pesos_bucket = [b[2] for b in buckets]

    calificaciones_riesgo = ["Bajo", "Medio", "Alto"]

    registros = []
    for i in range(n):
        id_cli = random.choice(ids_clientes)
        prod = random.choice(productos_credito)
        cod_prod = prod["cod_prod"]
        plazo = int(prod["plazo_max_meses"]) if prod["plazo_max_meses"] else random.choice([12, 24, 36])

        vr_aprobado = round(random.uniform(1_000_000, 50_000_000), 0)
        vr_desembolsado = round(vr_aprobado * random.uniform(0.85, 1.0), 0)

        fec_desembolso_dias = random.randint(0, (fecha_fin - fecha_inicio).days)
        fec_desembolso = fecha_inicio + timedelta(days=fec_desembolso_dias)
        fec_venc = fec_desembolso + timedelta(days=plazo * 30)

        vr_cuota = round(vr_desembolsado / max(plazo, 1) * random.uniform(1.02, 1.08), 0)  

        idx_bucket = np.random.choice(len(buckets), p=pesos_bucket)
        lo, hi, _ = buckets[idx_bucket]
        dias_mora_act = random.randint(lo, hi)


        meses_transcurridos = min(plazo, max(0, (fecha_fin - fec_desembolso).days // 30))
        pct_pagado = min(0.95, meses_transcurridos / max(plazo, 1))
        sdo_capital = round(vr_desembolsado * (1 - pct_pagado), 0)
        sdo_capital = max(sdo_capital, 0)

        num_cuotas_pend = max(plazo - meses_transcurridos, 0)


        if dias_mora_act == 0:
            calif_riesgo = np.random.choice(calificaciones_riesgo, p=[0.85, 0.13, 0.02])
        elif dias_mora_act <= 30:
            calif_riesgo = np.random.choice(calificaciones_riesgo, p=[0.30, 0.55, 0.15])
        else:
            calif_riesgo = np.random.choice(calificaciones_riesgo, p=[0.05, 0.25, 0.70])

        registros.append({
            "id_oblig": f"OBL-{i+1:06d}",
            "id_cli": id_cli,
            "cod_prod": cod_prod,
            "vr_aprobado": vr_aprobado,
            "vr_desembolsado": vr_desembolsado,
            "sdo_capital": sdo_capital,
            "vr_cuota": vr_cuota,
            "fec_desembolso": fec_desembolso.isoformat(),
            "fec_venc": fec_venc.isoformat(),
            "dias_mora_act": dias_mora_act,
            "num_cuotas_pend": num_cuotas_pend,
            "calif_riesgo": calif_riesgo,
        })

    return pd.DataFrame(registros)


if __name__ == "__main__":
    cfg = cargar_config()
    out_dir = cfg["salida"]["directorio"]

    df_clientes = pd.read_csv(f"{out_dir}/tb_clientes_core.csv")
    df_productos = pd.read_json(f"{out_dir}/tb_productos_cat.json")

    df_obligaciones = generar_obligaciones(cfg, df_clientes, df_productos)
    df_obligaciones.to_csv(f"{out_dir}/tb_obligaciones.csv", index=False, encoding="utf-8")

    print(f"Generadas {len(df_obligaciones)} obligaciones -> {out_dir}/tb_obligaciones.csv")
    print(df_obligaciones.head(5).to_string())

    print("\nValidacion de integridad referencial:")
    huerfanos_cli = ~df_obligaciones["id_cli"].isin(df_clientes["id_cli"])
    huerfanos_prod = ~df_obligaciones["cod_prod"].isin(df_productos["cod_prod"])
    print(f"  id_cli huerfanos: {huerfanos_cli.sum()} (debe ser 0)")
    print(f"  cod_prod huerfanos: {huerfanos_prod.sum()} (debe ser 0)")

    print("\nDistribucion de dias_mora_act (verificación de buckets):")
    bins = [-1, 0, 30, 60, 90, 10000]
    labels = ["Al dia (0)", "Rango 1 (1-30)", "Rango 2 (31-60)", "Rango 3 (61-90)", "Deteriorado (>90)"]
    print(pd.cut(df_obligaciones["dias_mora_act"], bins=bins, labels=labels).value_counts(normalize=True).round(3))

    print("\nConsistencia financiera - debe ser 0 en todos los casos:")
    print(f"  sdo_capital > vr_desembolsado: {(df_obligaciones['sdo_capital'] > df_obligaciones['vr_desembolsado']).sum()}")
    print(f"  vr_desembolsado > vr_aprobado: {(df_obligaciones['vr_desembolsado'] > df_obligaciones['vr_aprobado']).sum()}")
