# CHANGELOG

Todos los cambios significativos del proyecto  se documentan en este archivo.

Autor: Brayan Alejandro Cifuentes Quiroga

---

## 2026-08-27

### Añadido
- Selección del escenario A (Banca — FinBank S.A.) y diseño general de la arquitectura Medallion sobre Azure (ADF + Databricks + ADLS Gen2 + Key Vault + Terraform).
- Diseño del modelo de datos de las 6 tablas fuente (`TB_CLIENTES_CORE`, `TB_PRODUCTOS_CAT`, `TB_SUCURSALES_RED`, `TB_OBLIGACIONES`, `TB_MOV_FINANCIEROS`, `TB_COMISIONES_LOG`) y de las capas Bronze/Silver/Gold.
- Generación de datos sintéticos con semilla fija (`seed=42`, `config.yaml`): 10.000 clientes, 50 productos, 200 sucursales, 30.000 obligaciones, ~500.000 movimientos financieros, 80.000 comisiones, con 12 meses de cobertura temporal.
- 4 anomalías intencionales inyectadas en `TB_MOV_FINANCIEROS`: duplicados exactos, fechas fuera de rango, montos inválidos, IDs huérfanos.
- Distribuciones realistas: edades con distribución normal, movimientos concentrados en horario 8am-10pm, ~5% de nulos controlados en `score_buro`.
- Salida en 2 formatos distintos: CSV (`TB_CLIENTES_CORE`, `TB_OBLIGACIONES`, `TB_MOV_FINANCIEROS`, `TB_COMISIONES_LOG`) y JSON (`TB_PRODUCTOS_CAT`, `TB_SUCURSALES_RED`).
- Script `load_data_to_sql.py`: creación de las 6 tablas (DDL explícito) y carga en Azure SQL Database, con verificación de carga (`SELECT COUNT(*)` por tabla).
- Diagrama Entidad-Relación de las 6 tablas de origen.

### Corregido
- Restricción de aprovisionamiento de Azure SQL en `eastus`/`eastus2` (`ProvisioningDisabled`) → desplegado en `centralus`.
- Rendimiento de carga a SQL: de fila por fila (`pymssql`) a `pyodbc` con `fast_executemany=True`, en lotes de 20.000 registros.
- Traducción incorrecta de `NaN` de pandas a `NULL` de SQL, resuelta con función de limpieza explícita (`_valor_limpio`).

---

## 2026-08-28

### Añadido
- Infraestructura completa desplegada vía Terraform (`/infra`): Resource Group, Storage Account/ADLS Gen2 (contenedores bronze/silver/gold), Azure SQL Server + Database, Key Vault, Databricks Workspace, Data Factory, Log Analytics Workspace, Action Group, Budget de control de gasto.
- Backend remoto de Terraform (Storage Account `sttfstatefbcq2026`, creado manualmente una sola vez antes de la primera ejecución de Terraform).
- Parametrización de variables (`variables.tf`) con `description` en cada una; archivos separados `dev.tfvars`/`pdn.tfvars` (sin credenciales) y `secrets.tfvars` (gitignored).
- Outputs del módulo (`outputs.tf`): nombres y endpoints de los recursos clave, para ser consumidos por scripts externos al propio Terraform.
- Linked Services y Datasets parametrizados en Azure Data Factory.
- Pipeline `pl_ppal_data_ingest`: Lookup (Databricks Notebook) + `ForEach` secuencial sobre las 6 tablas, con lógica dinámica Full/Delta Load.
- SKU de Databricks ajustado a `premium` (requerido más adelante por Unity Catalog).

### Corregido
- Nombre de SQL Server ajustado por conflicto de unicidad global de Azure (sufijo `fbcq2026` agregado).

---

## 2026-08-29

### Añadido
- Migración de `control_ingestas` y `log_ingestas` de Azure SQL Database a tablas Delta Lake en Databricks (`_control/`), autenticadas vía Secret Scope de Databricks respaldado por Azure Key Vault.
- Notebooks `nb_get_control_config` (lectura de configuración) y `nb_update_checkpoint_and_log` (actualización de checkpoint + registro de log de ejecución, incluyendo tamaño de archivo generado).
- Parámetros `filtro_tabla` y `run_full_load` en el pipeline de Bronze, para reprocesamiento selectivo de una tabla específica sin tocar las demás.
- Capa Silver completa (`nb_bronze_to_silver`): 6 funciones de transformación, con 3 funciones de ayuda genéricas (`registrar_errores`, `enmascarar_columnas`, `validar_fk`).
- Enmascaramiento SHA-256 de columnas PII (`num_doc`, `num_cuenta`, y posteriormente `nombre_completo`) desde la capa Silver.
- Cálculo de `ind_sospechoso` (detección de fraude, ventana móvil de 30 días, umbral de 3 desviaciones estándar) en Silver.
- Tabla `errores_pipeline` para registrar rechazos de calidad de datos (FK inexistente, fechas/montos inválidos), sin detener el procesamiento.
- Capa Gold completa (`nb_silver_to_gold`): 4 dimensiones, 3 hechos, 3 agregaciones, tabla `cltv_12m`, y tabla de KPIs ejecutivos `kpis_cartera_diarios`.
- Reglas de negocio de Gold: `bucket_mora` (5 rangos), clasificación regulatoria A/B/C/D/E, provisión estimada, CLTV.
- 5 pruebas de calidad de datos sobre Gold (`nb_data_quality`).
- Normalización de formato de texto (`initcap`/`trim`) en columnas categóricas.
- Pipeline maestro `pl_finbank_master`: Bronze → Silver → Gold → Calidad, con dependencias `Succeeded` explícitas.
- Manejo de errores por tabla dentro del `ForEach`: ramas `LogAndAlert_CopyFailed`/`LogAndAlert_CheckpointFailed`, notebook `nb_log_pipeline_error`, tabla `log_errores_pipeline`.
- Alerta de fallo vía Azure Monitor (Log Analytics Query Alert sobre `ADFActivityRun`, con detalle de pipeline/tarea/error/hora) hacia el Action Group.
- Idempotencia demostrada por primera vez (2 corridas completas con resultados idénticos).

### Cambiado
- Bronze: de generar un archivo con timestamp único por corrida a sobrescribir la partición del día (previene crecimiento descontrolado de archivos).
- Silver: de `overwrite` total del histórico acumulado a `MERGE INTO` (upsert) sobre `clientes`, `obligaciones`, `movimientos_financieros` y `comisiones`, leyendo solo la partición del día.
- Checkpoint: de fecha semilla fija a `NULL` = "nunca ha corrido" (detección automática de primera ejecución).
- Filtro de checkpoint: `>` → `>=`, para no arriesgar pérdida de registros en el borde exacto del corte (seguro por el `MERGE` posterior en Silver).

### Corregido
- Error de límite (off-by-one) en el checkpoint inicial de `TB_COMISIONES_LOG`.
- Checkpoint de `TB_MOV_FINANCIEROS` corrompido por una anomalía intencional con fecha futura (año 2030): el cálculo del nuevo checkpoint ahora excluye fechas posteriores al momento de ejecución.
- Error de esquema (`DELTA_FAILED_TO_MERGE_FIELDS`) al escribir `log_ingestas`, resuelto definiendo el esquema explícitamente.
- `dim_canal.es_canal_digital` calculado incorrectamente.
- Query KQL de la alerta de fallo (`Error.message` → `tostring(Error)`).
- Destino del Diagnostic Setting de ADF (`AzureDiagnostics` genérico → `Dedicated`, necesario para que existiera la tabla `ADFActivityRun`).

---

## 2026-08-30

### Añadido
- Particionamiento físico en tablas Delta de Gold: `dim_clientes` (por `segmento_legible`), `fact_transacciones` (por `periodo_particion`), `fact_cartera` (por `bucket_mora`), `fact_rentabilidad_cliente` (por `periodo_mes`); clustering (`OPTIMIZE ZORDER`) en `kpis_cartera_diarios` y `agg_vista_comercial_cliente`.
- Reporte de calidad de datos por ejecución en Silver (`reporte_calidad_silver`): % de nulos por columna, registros rechazados, % de conformidad.
- Unity Catalog configurado de forma completa: Access Connector, Storage Credential, 3 External Locations, grupos `rol_ingeniero`/`rol_analista` con usuarios reales de Azure AD.
- Demostración de acceso denegado (Analista, `PERMISSION_DENIED` en Silver) y permitido (Ingeniero, lectura Silver + escritura Gold) con usuarios reales.
- Enmascaramiento SHA-256 extendido a `nombre_completo`.
- Documentos `catalogo_pii.md` y `catalogo_datos.md` en `/docs`.
- Reporte diario de ejecución (`nb_reporte_diario`): registros por capa y rechazados, con duración real tomada de `ADFPipelineRun`.
- Alerta de anomalía de volumen (>30% vs. promedio de 7 ejecuciones previas), reutilizando el canal de la alerta de fallo con mensaje diferenciado (`ANOMALIA_VOLUMEN:`).
- Trigger diario programado (02:00 hora Bogotá), desactivado por defecto por control de costos.
- Flujo completo de CI/CD con Azure DevOps (`azure-pipelines.yml`): 3 etapas (Validar, DesplegarDev, DesplegarPdn con aprobación manual), incluyendo despliegue automático de los pipelines de ADF al entorno `pdn`.
- Entorno `pdn` desplegado exitosamente de punta a punta a través del pipeline de CI/CD (primera ejecución real).
- Script `insertar_datos_incrementales.py` para demostrar carga Delta con datos genuinamente nuevos.

### Corregido
- Checkpoints desincronizados al limpiar Bronze/Silver/Gold sin resetearlos.
- Falso positivo de "50% rechazados" en `productos`/`sucursales` (comparaba contra el histórico acumulado de Bronze en vez del conjunto deduplicado).
- Ventana móvil de 30 días en `movimientos_financieros` calculando 100% de nulos: corregido para combinar el historial ya persistido en Silver con las filas nuevas del día, solo para efectos del cálculo.
- Bug de contaminación de historial en la alerta de anomalía de volumen: los reintentos automáticos (`retry: 3`) agregaban filas al log antes de fallar, sesgando el promedio de comparación en corridas sucesivas. Se corrigió invirtiendo el orden (validar antes de registrar).
- Extensión `TerraformInstaller` de Azure DevOps Marketplace descontinuada durante el desarrollo → reemplazada por instalación directa de Terraform vía `curl`.
- Autenticación de Terraform contra Azure en CI/CD: Workload Identity Federation no soportada por el proveedor `azurerm` vía sesión de Azure CLI de tipo Service Principal → Service Connection reconfigurado con credencial clásica (`az ad sp create-for-rbac`).
- `deployment` jobs de Azure DevOps sin `checkout: self` (no descargan el repositorio por defecto, a diferencia de los `job` normales).
- Variable `alert_email` sin valor por defecto bloqueando el pipeline de CI/CD en espera de entrada interactiva; `client_ip_address` convertida en opcional (`default = ""`) con el recurso de firewall asociado condicionado por `count`.
- Desajuste del `key` del backend remoto de Terraform entre el entorno local y el pipeline de CI/CD, causando que no reconociera la infraestructura ya existente.
- Permisos insuficientes del Service Principal de CI/CD sobre Key Vault (`secrets get`) y sobre asignación de roles (`User Access Administrator`).
- Dependencia circular entre el trigger de ADF y el pipeline `pl_finbank_master` (el trigger requiere que el pipeline exista) — resuelta con un `apply` de Terraform en 2 pasos, con el despliegue de pipelines de ADF en medio.
- Candado (`lease`) huérfano en el archivo de estado remoto de Terraform tras una ejecución cancelada, liberado directamente sobre el blob de Azure Storage.
- Región de SQL Server en `pdn.tfvars` corregida de `eastus2` (no disponible) a `centralus`.

---

## 2026-08-31

### Añadido
- Diagrama Entidad-Relación finalizado y agregado a `/docs`.
- Corrida final de verificación en 3 pasos: Full Load limpio, repetición sin cambios (idempotencia confirmada: 494.500 filas idénticas en `movimientos_financieros`), y carga incremental real tras `insertar_datos_incrementales.py` (494.500 → 494.540, +40 filas netas, con Bronze leyendo 2.148 y Silver absorbiendo la diferencia sin duplicados vía `MERGE`).
- `nb_setup_control_tables.py` simplificado: las 6 tablas nacen con `checkpoint_date = NULL`, eliminando la necesidad de una fecha semilla manual.
- Documentación completa y exhaustiva del `README.md`: 13 secciones cubriendo justificación de sector/plataforma, arquitectura, generación de datos (Fase 1), infraestructura (Fase 2) con inventario completo de recursos, pipeline explicado con cada decisión justificada (Fase 3), orquestación (Fase 4), gobierno y seguridad (Fase 5), limitaciones conocidas documentadas con honestidad, índice de evidencias, y el flujo de CI/CD dev→pdn con los hallazgos técnicos reales de su implementación.
- Checklist de cumplimiento verificable por fase, cruzando cada requisito del documento de la prueba contra la evidencia real generada durante el desarrollo.
- ~32 capturas de evidencia recolectadas y referenciadas en el README, integradas en el contexto narrativo de cada sección (no solo en un anexo).

### Corregido
- Numeración de secciones y referencias cruzadas internas del README, tras la inserción de nuevas secciones durante la redacción.
