import random
import yaml
import numpy as np
import pandas as pd
from datetime import date
from faker import Faker

def cargar_config(path="config.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def generar_clientes(config: dict) -> pd.DataFrame:
    seed = config["seed"]
    random.seed(seed)
    np.random.seed(seed)
    fake = Faker("es_CO")
    Faker.seed(seed)

    n = config["volumenes"]["clientes"]
    fecha_inicio = date.fromisoformat(config["periodo"]["fecha_inicio"])
    fecha_fin = date.fromisoformat(config["periodo"]["fecha_fin"])

    # cod_segmento-distribucion ponderada (piramide de ingresos) 
    segmentos = ["Basico", "Estandar", "Premium", "Elite"]
    pesos_segmento = [0.45, 0.35, 0.15, 0.05]

    # ciudades ponderadas por pais
    ciudades_pool = []
    pesos_ciudad = []
    for pais in config["paises"]:
        peso_pais = 0.45 if pais["nombre"] == "Colombia" else 0.55 / (len(config["paises"]) - 1)
        for ciudad in pais["ciudades"]:
            ciudades_pool.append((ciudad, pais["nombre"]))
            pesos_ciudad.append(peso_pais / len(pais["ciudades"]))
    pesos_ciudad = np.array(pesos_ciudad) / sum(pesos_ciudad)

    # edades
    edades = np.random.normal(loc=38, scale=12, size=n)
    edades = np.clip(edades, 18, 80).astype(int)
    hoy = date(2026, 8, 27)
    fechas_nac = [date(hoy.year - e, random.randint(1, 12), random.randint(1, 28)) for e in edades]

    #score_buro normal 
    scores = np.random.normal(loc=650, scale=100, size=n)
    scores = np.clip(scores, 150, 950).astype(int)

    canales_adquis = ["App Movil", "Portal Web", "Corresponsal Bancario"]

    registros = []
    for i in range(n):
        idx_ciudad = np.random.choice(len(ciudades_pool), p=pesos_ciudad)
        ciudad, pais_res = ciudades_pool[idx_ciudad]

        fec_alta_dias = random.randint(0, (fecha_fin - fecha_inicio).days)
        fec_alta = fecha_inicio + pd.Timedelta(days=fec_alta_dias).to_pytimedelta()

        registros.append({
            "id_cli": 100000 + i,
            "nomb_cli": fake.first_name(),
            "apell_cli": fake.last_name(),
            "tip_doc": "CC",
            "num_doc": fake.unique.numerify("##########"),
            "fec_nac": fechas_nac[i].isoformat(),
            "fec_alta": fec_alta.isoformat(),
            "cod_segmento": np.random.choice(segmentos, p=pesos_segmento),
            "score_buro": int(scores[i]),
            "ciudad_res": ciudad,
            "depto_res": pais_res,
            "estado_cli": "Activo",
            "canal_adquis": random.choice(canales_adquis),
        })

    df = pd.DataFrame(registros)

    #insert de de nulos  
    pct_nulos = config["calidad"]["pct_nulos"]
    for col in ["score_buro", "depto_res"]:
        idx_nulos = df.sample(frac=pct_nulos, random_state=seed).index
        df.loc[idx_nulos, col] = None

    return df


if __name__ == "__main__":
    cfg = cargar_config()
    df_clientes = generar_clientes(cfg)

    import os
    out_dir = cfg["salida"]["directorio"]
    os.makedirs(out_dir, exist_ok=True)
    out_path = f"{out_dir}/tb_clientes_core.csv"
    df_clientes.to_csv(out_path, index=False, encoding="utf-8")

    print(f"Generados {len(df_clientes)} registros de clientes.")
    print(f"Guardado en: {out_path}")
    print("\nVista previa:")
    print(df_clientes.head(5).to_string())
    print("\nResumen de nulos por columna:")
    print(df_clientes.isnull().sum())
    print("\nDistribucion de cod_segmento:")
    print(df_clientes["cod_segmento"].value_counts(normalize=True).round(3))
