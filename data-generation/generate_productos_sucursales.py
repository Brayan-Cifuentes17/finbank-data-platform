import random
import numpy as np
import pandas as pd
import json
from generate_clientes import cargar_config

COORDENADAS_CIUDAD = {
    "Bogotá": (4.7110, -74.0721),
    "Medellín": (6.2442, -75.5812),
    "Cali": (3.4516, -76.5320),
    "Barranquilla": (10.9639, -74.7964),
    "Ciudad de México": (19.4326, -99.1332),
    "Guadalajara": (20.6597, -103.3496),
    "Lima": (-12.0464, -77.0428),
    "Santiago": (-33.4489, -70.6693),
    "Buenos Aires": (-34.6037, -58.3816),
}


def generar_productos(config: dict) -> pd.DataFrame:
    seed = config["seed"]
    random.seed(seed + 1)   
    np.random.seed(seed + 1)

    n = config["volumenes"]["productos"]

    #productos
    catalogo_familias = [
        #tip_prod, desc_base, rango_tasa_ea, familia
        ("Credito Libre Inversion", "Credito de Libre Inversion", (0.18, 0.30), "credito"),
        ("Credito Rotativo", "Cupo Rotativo", (0.25, 0.35), "credito"),
        ("Tarjeta Digital", "Tarjeta de Credito Digital", (0.22, 0.32), "credito"),
        ("Cuenta de Ahorro", "Cuenta de Ahorro Digital", (0.0, 0.02), "ahorro"),
        ("Servicio Transaccional", "Pagos PSE / Transferencias ACH", (0.0, 0.0), "transaccional"),
        ("Corresponsalia", "Servicio de Corresponsalia Bancaria", (0.0, 0.0), "transaccional"),
    ]

    registros = []
    for i in range(n):
        tip_prod, desc_base, rango_tasa, familia = random.choice(catalogo_familias)
        tasa_ea = round(random.uniform(*rango_tasa), 4)

        if familia == "credito":
            plazo_max_meses = random.choice([12, 24, 36, 48, 60])
            cuota_min = round(random.uniform(50000, 300000), 0)
            comision_admin = round(random.uniform(5000, 25000), 0)
        else:
            plazo_max_meses = 0
            cuota_min = 0.0
            comision_admin = round(random.uniform(0, 8000), 0)

        registros.append({
            "cod_prod": f"PROD-{i+1:03d}",
            "desc_prod": f"{desc_base} {i+1}",
            "tip_prod": tip_prod,
            "tasa_ea": tasa_ea,
            "plazo_max_meses": plazo_max_meses,
            "cuota_min": cuota_min,
            "comision_admin": comision_admin,
            "estado_prod": "Activo" if random.random() > 0.05 else "Inactivo",
        })

    return pd.DataFrame(registros)


def generar_sucursales(config: dict) -> pd.DataFrame:
    seed = config["seed"]
    random.seed(seed + 2)
    np.random.seed(seed + 2)

    n = config["volumenes"]["sucursales"]

    tipos_punto = ["Sucursal Fisica", "Corresponsal Bancario", "Cajero Automatico", "Punto Digital"]
    pesos_tipo = [0.30, 0.35, 0.25, 0.10]  

    
    ciudades_pool = []
    for pais in config["paises"]:
        for ciudad in pais["ciudades"]:
            ciudades_pool.append((ciudad, pais["nombre"]))

    registros = []
    for i in range(n):
        ciudad, pais = random.choice(ciudades_pool)
        tip_punto = np.random.choice(tipos_punto, p=pesos_tipo)  
        lat_base, lon_base = COORDENADAS_CIUDAD[ciudad]
        # variar
        lat = round(lat_base + random.uniform(-0.05, 0.05), 6)
        lon = round(lon_base + random.uniform(-0.05, 0.05), 6)

        registros.append({
            "cod_suc": f"SUC-{i+1:04d}",
            "nom_suc": f"{tip_punto} {ciudad} {i+1}",
            "tip_punto": tip_punto,
            "ciudad": ciudad,
            "depto": pais,
            "latitud": lat,
            "longitud": lon,
            "activo": True if random.random() > 0.03 else False,
        })

    return pd.DataFrame(registros)


if __name__ == "__main__":
    cfg = cargar_config()
    out_dir = cfg["salida"]["directorio"]

    df_productos = generar_productos(cfg)
    df_sucursales = generar_sucursales(cfg)

    df_productos.to_json(f"{out_dir}/tb_productos_cat.json", orient="records", indent=2, force_ascii=False)
    df_sucursales.to_json(f"{out_dir}/tb_sucursales_red.json", orient="records", indent=2, force_ascii=False)

    print(f"Generados {len(df_productos)} productos -> {out_dir}/tb_productos_cat.json")
    print(df_productos.head(5).to_string())
    print(f"\nDistribución de familia (tip_prod):")
    print(df_productos["tip_prod"].value_counts())

    print(f"\nGeneradas {len(df_sucursales)} sucursales -> {out_dir}/tb_sucursales_red.json")
    print(df_sucursales.head(5).to_string())
    print(f"\nDistribución de tip_punto:")
    print(df_sucursales["tip_punto"].value_counts(normalize=True).round(3))
