# Catálogo de Datos — Capas Silver y Gold
---

## CAPA SILVER

### silver.clientes
| Campo | Tipo | Origen | Sensible |
|---|---|---|---|
| id_cli | INT | TB_CLIENTES_CORE.id_cli | No |
| nombre_completo_hash | STRING | Calculado (hash de nomb_cli + apell_cli) | Sí (protegido) |
| tip_doc | STRING | TB_CLIENTES_CORE.tip_doc | No |
| num_doc_hash | STRING | Calculado (hash de num_doc) | Sí (protegido) |
| fec_nac | DATE | TB_CLIENTES_CORE.fec_nac | Sí |
| edad | INT | Calculado (desde fec_nac) | No |
| fec_alta | DATE | TB_CLIENTES_CORE.fec_alta | No |
| cod_segmento | STRING | TB_CLIENTES_CORE.cod_segmento | No |
| score_buro | INT | TB_CLIENTES_CORE.score_buro | No |
| score_buro_nulo | INT (0/1) | Calculado (indicador de nulo) | No |
| ciudad_res | STRING | TB_CLIENTES_CORE.ciudad_res (normalizado) | No |
| depto_res | STRING | TB_CLIENTES_CORE.depto_res (normalizado, nulo→"No informado") | No |
| estado_cli | STRING | TB_CLIENTES_CORE.estado_cli | No |
| canal_adquis | STRING | TB_CLIENTES_CORE.canal_adquis | No |

### silver.productos
| Campo | Tipo | Origen | Sensible |
|---|---|---|---|
| cod_prod | STRING | TB_PRODUCTOS_CAT.cod_prod | No |
| desc_prod | STRING | TB_PRODUCTOS_CAT.desc_prod | No |
| tip_prod | STRING | TB_PRODUCTOS_CAT.tip_prod | No |
| tasa_ea | DECIMAL | TB_PRODUCTOS_CAT.tasa_ea | No |
| plazo_max_meses | INT | TB_PRODUCTOS_CAT.plazo_max_meses | No |
| cuota_min | DECIMAL | TB_PRODUCTOS_CAT.cuota_min | No |
| comision_admin | DECIMAL | TB_PRODUCTOS_CAT.comision_admin | No |
| estado_prod | STRING | TB_PRODUCTOS_CAT.estado_prod | No |
| tasa_mensual_equiv | DOUBLE | Calculado ((1+tasa_ea)^(1/12)-1) | No |
| familia_producto | STRING | Calculado (clasificación por tip_prod) | No |
| ingestion_timestamp, source_system, batch_id | TIMESTAMP/STRING | Auditoría de Bronze | No |

### silver.sucursales
| Campo | Tipo | Origen | Sensible |
|---|---|---|---|
| cod_suc | STRING | TB_SUCURSALES_RED.cod_suc | No |
| nom_suc | STRING | TB_SUCURSALES_RED.nom_suc | No |
| tip_punto | STRING | TB_SUCURSALES_RED.tip_punto | No |
| ciudad, depto | STRING | TB_SUCURSALES_RED.ciudad/depto | No |
| latitud, longitud | DOUBLE | TB_SUCURSALES_RED.latitud/longitud | No |
| activo | BOOLEAN | TB_SUCURSALES_RED.activo | No |
| ingestion_timestamp, source_system, batch_id | TIMESTAMP/STRING | Auditoría de Bronze | No |

### silver.obligaciones
| Campo | Tipo | Origen | Sensible |
|---|---|---|---|
| id_oblig | STRING | TB_OBLIGACIONES.id_oblig | No |
| id_cli | INT | TB_OBLIGACIONES.id_cli (FK validada contra silver.clientes) | No |
| cod_prod | STRING | TB_OBLIGACIONES.cod_prod (FK validada) | No |
| vr_aprobado, vr_desembolsado, sdo_capital, vr_cuota | DECIMAL | TB_OBLIGACIONES | No |
| fec_desembolso, fec_venc | DATE | TB_OBLIGACIONES | No |
| dias_mora_act | INT | TB_OBLIGACIONES.dias_mora_act | No |
| num_cuotas_pend | INT | TB_OBLIGACIONES.num_cuotas_pend | No |
| calif_riesgo | STRING | TB_OBLIGACIONES.calif_riesgo | No |
| ingestion_timestamp, source_system, batch_id | TIMESTAMP/STRING | Auditoría de Bronze | No |

### silver.comisiones
| Campo | Tipo | Origen | Sensible |
|---|---|---|---|
| id_comision | STRING | TB_COMISIONES_LOG.id_comision | No |
| id_cli | INT | TB_COMISIONES_LOG.id_cli (FK validada) | No |
| cod_prod | STRING | TB_COMISIONES_LOG.cod_prod (FK validada) | No |
| fec_cobro | DATE | TB_COMISIONES_LOG.fec_cobro | No |
| vr_comision | DECIMAL | TB_COMISIONES_LOG.vr_comision | No |
| tip_comision | STRING | TB_COMISIONES_LOG.tip_comision | No |
| estado_cobro | STRING | TB_COMISIONES_LOG.estado_cobro | No |
| ingestion_timestamp, source_system, batch_id | TIMESTAMP/STRING | Auditoría de Bronze | No |

### silver.movimientos_financieros
| Campo | Tipo | Origen | Sensible |
|---|---|---|---|
| id_mov | STRING | TB_MOV_FINANCIEROS.id_mov | No |
| id_cli | INT | TB_MOV_FINANCIEROS.id_cli (FK validada) | No |
| cod_prod | STRING | TB_MOV_FINANCIEROS.cod_prod (FK validada) | No |
| fec_mov | DATE | TB_MOV_FINANCIEROS.fec_mov (validado rango 2015–hoy) | No |
| hra_mov | TIMESTAMP | TB_MOV_FINANCIEROS.hra_mov | No |
| vr_mov | DECIMAL | TB_MOV_FINANCIEROS.vr_mov (validado > 0) | No |
| tip_mov | STRING | TB_MOV_FINANCIEROS.tip_mov | No |
| cod_canal | STRING | TB_MOV_FINANCIEROS.cod_canal | No |
| cod_ciudad | STRING | TB_MOV_FINANCIEROS.cod_ciudad (normalizado) | No |
| cod_estado_mov | STRING | TB_MOV_FINANCIEROS.cod_estado_mov | No |
| id_dispositivo | STRING | TB_MOV_FINANCIEROS.id_dispositivo | Sí (bajo riesgo, no enmascarado) |
| promedio_movil_30d | DECIMAL | Calculado (ventana móvil 30 días por cliente) | No |
| stddev_movil_30d | DOUBLE | Calculado (ventana móvil 30 días por cliente) | No |
| ind_sospechoso | INT (0/1) | Calculado (vr_mov > promedio + 3·desviación) | No |
| num_cuenta_hash | STRING | Calculado (hash de num_cuenta) | Sí (protegido) |
| ingestion_timestamp, source_system, batch_id | TIMESTAMP/STRING | Auditoría de Bronze | No |

---

## CAPA GOLD

### gold.dim_clientes
| Campo | Tipo | Origen | Sensible |
|---|---|---|---|
| id_cli | INT | silver.clientes.id_cli | No |
| nombre_completo_hash | STRING | silver.clientes.nombre_completo_hash | Sí (protegido) |
| tip_doc, num_doc_hash | STRING | silver.clientes | Sí (num_doc_hash, protegido) |
| fec_nac, edad, fec_alta | DATE/INT | silver.clientes | fec_nac: Sí |
| segmento_legible | STRING | silver.clientes.cod_segmento (renombrado) | No |
| score_buro, score_buro_nulo | INT | silver.clientes | No |
| ciudad_res, depto_res, estado_cli, canal_adquis | STRING | silver.clientes | No |

### gold.dim_productos
| Campo | Tipo | Origen | Sensible |
|---|---|---|---|
| cod_prod | STRING | silver.productos.cod_prod | No |
| descripcion_producto | STRING | silver.productos.desc_prod (renombrado) | No |
| tipo_producto | STRING | silver.productos.tip_prod (renombrado) | No |
| familia_producto, tasa_ea, tasa_mensual_equiv, plazo_max_meses, cuota_min, comision_admin, estado_prod | Varios | silver.productos | No |

### gold.dim_geografia
| Campo | Tipo | Origen | Sensible |
|---|---|---|---|
| id_geografia | LONG | Calculado (ID generado) | No |
| ciudad, depto | STRING | silver.sucursales (deduplicado) | No |

### gold.dim_canal
| Campo | Tipo | Origen | Sensible |
|---|---|---|---|
| id_canal | LONG | Calculado (ID generado) | No |
| tip_punto | STRING | silver.sucursales.tip_punto (deduplicado) | No |
| es_canal_digital | BOOLEAN | Calculado (tip_punto == "Punto Digital") | No |

### gold.fact_transacciones
| Campo | Tipo | Origen | Sensible |
|---|---|---|---|
| id_mov, id_cli, cod_prod, fec_mov, hra_mov, vr_mov, tip_mov, cod_canal, cod_ciudad, cod_estado_mov | Varios | silver.movimientos_financieros | No |
| vr_mov_usd | DECIMAL | Calculado (vr_mov / tasa fija COP-USD) | No |
| promedio_movil_30d, stddev_movil_30d, ind_sospechoso | Varios | silver.movimientos_financieros (ya calculado ahí) | No |
| flag_horario_habil | BOOLEAN | Calculado (hora entre 8am-6pm) | No |
| periodo_particion | STRING | Calculado (año-mes de fec_mov, columna de partición) | No |

### gold.fact_cartera
| Campo | Tipo | Origen | Sensible |
|---|---|---|---|
| id_oblig, id_cli, cod_prod, vr_aprobado, vr_desembolsado, sdo_capital, vr_cuota, fec_desembolso, fec_venc, num_cuotas_pend, calif_riesgo | Varios | silver.obligaciones | No |
| dias_mora_act | INT | silver.obligaciones | No |
| bucket_mora | STRING | Calculado (clasificación en 5 rangos de dias_mora_act) | No |
| clasificacion_regulatoria | STRING | Calculado (A/B/C/D/E, desde bucket_mora) | No |
| provision_estimada | DECIMAL | Calculado (sdo_capital × % según clasificación) | No |

### gold.fact_rentabilidad_cliente
| Campo | Tipo | Origen | Sensible |
|---|---|---|---|
| id_cli | INT | silver.movimientos_financieros / silver.comisiones | No |
| periodo_mes | STRING | Calculado (año-mes) | No |
| ingreso_intereses | DECIMAL | Calculado (suma vr_mov donde tip_mov='pago_interes') | No |
| ingreso_comisiones | DECIMAL | Calculado (suma vr_comision donde estado_cobro='Cobrado') | No |
| ingreso_total | DECIMAL | Calculado (ingreso_intereses + ingreso_comisiones) | No |

### gold.agg_mora_por_segmento_region
| Campo | Tipo | Origen | Sensible |
|---|---|---|---|
| segmento_legible, ciudad_res | STRING | gold.dim_clientes | No |
| total_obligaciones, monto_total_cartera, monto_en_mora | INT/DECIMAL | Calculado (agregación sobre gold.fact_cartera) | No |
| tasa_mora_pct | DOUBLE | Calculado (monto_en_mora / monto_total_cartera × 100) | No |

### gold.agg_transacciones_por_canal_ciudad
| Campo | Tipo | Origen | Sensible |
|---|---|---|---|
| cod_canal, cod_ciudad | STRING | gold.fact_transacciones | No |
| total_transacciones, monto_total, monto_promedio, total_sospechosas | INT/DECIMAL | Calculado (agregación sobre gold.fact_transacciones) | No |

### gold.cltv_12m
| Campo | Tipo | Origen | Sensible |
|---|---|---|---|
| id_cli | INT | gold.fact_rentabilidad_cliente | No |
| total_ingreso_intereses_12m, total_ingreso_comisiones_12m, cltv_12m | DECIMAL | Calculado (suma de 12 meses por cliente) | No |

### gold.agg_vista_comercial_cliente
| Campo | Tipo | Origen | Sensible |
|---|---|---|---|
| id_cli | INT | gold.dim_clientes | No |
| nombre_completo_hash | STRING | gold.dim_clientes.nombre_completo_hash | Sí (protegido) |
| segmento_legible, ciudad_res, estado_cli | STRING | gold.dim_clientes | No |
| num_obligaciones | INT | Calculado (conteo desde gold.fact_cartera) | No |
| num_transacciones | INT | Calculado (conteo desde gold.fact_transacciones) | No |
| cltv_12m | DECIMAL | gold.cltv_12m | No |
| orden_riesgo_max | INT | Calculado (peor bucket_mora entre sus obligaciones) | No |

### gold.kpis_cartera_diarios
| Campo | Tipo | Origen | Sensible |
|---|---|---|---|
| fecha | DATE | Calculado (fecha de ejecución) | No |
| cod_prod, segmento_legible, ciudad_res | STRING | gold.fact_cartera + gold.dim_clientes | No |
| total_obligaciones_activas, monto_total_cartera, monto_en_mora, clientes_en_mora | INT/DECIMAL | Calculado (agregación) | No |
| tasa_mora_pct | DOUBLE | Calculado | No |

---

## Notas generales

- Todas las tablas Silver y Gold están en formato Delta Lake.
- Las columnas marcadas "Sí (protegido)" ya están enmascaradas con SHA-256 desde Silver — el dato original nunca llega a Gold.
- Ver `catalogo_pii.md` para el detalle completo de identificación de PII en las tablas de origen (Bronze).
- El perfil Analista solo tiene acceso a la capa Gold
