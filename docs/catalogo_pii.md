# Identificación y Etiquetado de Información de Identificación Personal (PII)
---

## Metodología

Se revisaron las 6 tablas de origen (Bronze) columna por columna, clasificando cada una como PII o no-PII según si permite identificar, contactar, o rastrear a una persona. Para cada columna PII se documenta si se enmascara (y desde qué capa) o si se mantiene legible por necesidad de negocio, con la justificación correspondiente.

---

## TB_CLIENTES_CORE

| Columna | ¿PII? | Enmascarada desde | Justificación |
|---|---|---|---|
| `id_cli` | No | — | Identificador técnico interno, no expone información personal por sí solo |
| `nomb_cli`, `apell_cli` | **Sí** |Silver (`nombre_completo_hash`, SHA-256) | Se enmascara siguiendo el texto literal del documento, que cita "nombres" como ejemplo explícito de PII a proteger. Consecuencia asumida: la vista comercial de Gold (`agg_vista_comercial_cliente`) pierde la capacidad de identificar clientes por nombre legible; se prioriza el cumplimiento estricto sobre la conveniencia analítica |
| `num_doc` | **Sí** |Silver (`num_doc_hash`, SHA-256) | Identificador único y sensible (cédula/documento), riesgo directo de suplantación |
| `tip_doc` | No | — | Solo indica el tipo de documento (CC, CE), no el valor en sí |
| `fec_nac` | **Sí** | No enmascarada | Dato sensible por sí solo, pero necesario para calcular `edad` (campo de negocio). Se documenta como PII de bajo riesgo cuando se usa solo para derivar edad, sin exponer la fecha exacta en los reportes finales de Gold (Gold solo expone `edad`, no `fec_nac`) |
| `score_buro` | No | — | Dato financiero, no identifica a la persona por sí solo |
| `ciudad_res`, `depto_res` | No (a nivel individual) | — | Información geográfica agregable, no identifica a una persona específica de forma aislada |
| `estado_cli`, `cod_segmento`, `canal_adquis`, `fec_alta` | No | — | Datos operativos/comerciales, sin relación directa con identidad personal |

## TB_MOV_FINANCIEROS

| Columna | ¿PII? | Enmascarada desde | Justificación |
|---|---|---|---|
| `num_cuenta` | **Sí** | Silver (`num_cuenta_hash`, SHA-256) | Identificador financiero directo, alto riesgo si se expone |
| `id_dispositivo` | **Sí** (parcial) | No enmascarada | Podría usarse para rastrear el dispositivo de un cliente, pero es un identificador de dispositivo (ej. `DEV-XXXXXX`), no una persona directamente. Se documenta como dato sensible de bajo riesgo, sin enmascarar por su utilidad en análisis de fraude por canal |
| `id_cli` | No | — | Igual que en clientes, identificador técnico |
| `vr_mov`, `fec_mov`, `hra_mov`, `tip_mov`, `cod_canal`, `cod_ciudad`, `cod_estado_mov` | No | — | Datos transaccionales, no identifican a la persona por sí solos |

## TB_OBLIGACIONES

Ninguna columna de esta tabla contiene PII directa (`id_cli`, `id_oblig`, montos, fechas, calificación de riesgo) — todas son datos financieros/operativos ligados a un cliente mediante `id_cli`, pero sin exponer información de identidad por sí mismas.

## TB_COMISIONES_LOG

Igual que `TB_OBLIGACIONES` — sin columnas PII directas.

## TB_PRODUCTOS_CAT y TB_SUCURSALES_RED

Tablas de catálogo (productos y puntos de atención); ninguna columna contiene información de identificación personal.

---

## Resumen de columnas PII enmascaradas (implementadas)

| Tabla origen | Columna original | Columna resultante (Silver) | Método |
|---|---|---|---|
| TB_CLIENTES_CORE | `num_doc` | `num_doc_hash` | SHA-256 |
| TB_CLIENTES_CORE | `nomb_cli` + `apell_cli` | `nombre_completo_hash` | SHA-256 |
| TB_MOV_FINANCIEROS | `num_cuenta` | `num_cuenta_hash` | SHA-256 |

## Resumen de columnas PII identificadas pero NO enmascaradas (con justificación documentada)

| Tabla origen | Columna | Razón para no enmascarar |
|---|---|---|
| TB_CLIENTES_CORE | `fec_nac` | Se usa solo para derivar `edad`; Gold no expone la fecha exacta |
| TB_MOV_FINANCIEROS | `id_dispositivo` | Bajo riesgo individual, útil para análisis de fraude por canal |

