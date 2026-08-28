import random
import numpy as np
import pandas as pd
from datetime import date, datetime, timedelta
from generate_clientes import cargar_config


def generar_comisiones(config: dict, df_clientes: pd.DataFrame, df_productos: pd.DataFrame) -> pd.DataFrame:
    seed = config["seed"]
    random.seed(seed + 5)
    np.random.seed(seed + 5)

    n = config["volumenes"]["comisiones"]
    fecha_inicio = date.fromisoformat(config["periodo"]["fecha_inicio"])
    fecha_fin = date.fromisoformat(config["periodo"]["fecha_fin"])
    dias_totales = (fecha_fin - fecha_inicio).days

    ids_clientes = df_clientes["id_cli"].tolist()
    ids_productos = df_productos["cod_prod"].tolist()

    tipos_comision = [
        "Comision Administracion",
        "Comision Manejo Cuenta",
        "Comision Retiro Cajero",
        "Comision Transferencia",
        "Comision Consulta Saldo",
    ]
    pesos_tipos = [0.30, 0.25, 0.20, 0.15, 0.10]

  
    estados_cobro = ["Cobrado", "Pendiente", "Rechazado"]
    pesos_estados = [0.85, 0.10, 0.05]

    registros = []
    for i in range(n):
        id_cli = random.choice(ids_clientes)
        cod_prod = random.choice(ids_productos)

        dia_offset = random.randint(0, dias_totales)
        fec_cobro = fecha_inicio + timedelta(days=dia_offset)

        tip_comision = np.random.choice(tipos_comision, p=pesos_tipos)
     
        vr_comision = round(random.uniform(2000, 45000), 0)

        registros.append({
            "id_comision": f"COM-{i+1:06d}",
            "id_cli": id_cli,
            "cod_prod": cod_prod,
            "fec_cobro": fec_cobro.isoformat(),
            "vr_comision": vr_comision,
            "tip_comision": tip_comision,
            "estado_cobro": np.random.choice(estados_cobro, p=pesos_estados),
        })

    return pd.DataFrame(registros)


if __name__ == "__main__":
    cfg = cargar_config()
    out_dir = cfg["salida"]["directorio"]

    df_clientes = pd.read_csv(f"{out_dir}/tb_clientes_core.csv")
    df_productos = pd.read_json(f"{out_dir}/tb_productos_cat.json")

    df_comisiones = generar_comisiones(cfg, df_clientes, df_productos)
    df_comisiones.to_csv(f"{out_dir}/tb_comisiones_log.csv", index=False, encoding="utf-8")

    print(f"Generadas {len(df_comisiones)} comisiones -> {out_dir}/tb_comisiones_log.csv")
    print(df_comisiones.head(5).to_string())

    print("\nValidacion de integridad referencial:")
    huerfanos_cli = (~df_comisiones["id_cli"].isin(df_clientes["id_cli"])).sum()
    huerfanos_prod = (~df_comisiones["cod_prod"].isin(df_productos["cod_prod"])).sum()
    print(f"  id_cli huérfanos: {huerfanos_cli} (debe ser 0)")
    print(f"  cod_prod huérfanos: {huerfanos_prod} (debe ser 0)")

    print("\nDistribucion de estado_cobro:")
    print(df_comisiones["estado_cobro"].value_counts(normalize=True).round(3))

    print("\nMonto total 'efectivamente cobrado':")
    total_cobrado = df_comisiones[df_comisiones["estado_cobro"] == "Cobrado"]["vr_comision"].sum()
    print(f"  ${total_cobrado:,.0f}")
