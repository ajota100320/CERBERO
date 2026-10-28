# 📖 README MAESTRO - ERP APP SHEET TEMPLO DEL SMASH
## Guía Completa de Despliegue Fase por Fase

---

## 🎯 VISIÓN GENERAL

Este proyecto implementa un **ERP completo multi-sucursal** para "Templo del Smash" en **AppSheet + Google Sheets**, desplegable en **6 fases secuenciales** con dependencias estrictas.

### Arquitectura Final (Post-Fase 6)

| Componente | Cantidad | Descripción |
|------------|----------|-------------|
| **Tablas nuevas** | 26 | 6 base + 20 funcionales |
| **Tablas extendidas** | 6 | Columnas auditoría, stock, costos |
| **Actions** | 73 | Lógica de negocio, flujos de estado |
| **Bots (Automation)** | 27 | Notificaciones, cálculos, SLA, escalados |
| **Tasks** | 70+ | Push notifications, jobs programados |
| **Vistas (UX)** | 69 | Por rol: Admin, Encargado, Operador |
| **Security Filters** | 48 | Row-level security multi-sucursal |
| **Tests de validación** | 128 | Casos de uso end-to-end |

---

## 📦 ESTRUCTURA DE ENTREGABLES

```
Entregas_Hermes/
├── Fundaciones/                          # FASE 1 - Base multi-sucursal
│   ├── 01_CSVs_Google_Sheets/           # 6 CSVs listos para importar
│   ├── 02_Security_Filters/             # 14 filtros de seguridad
│   ├── 03_Columnas_Auditoria_Por_Tabla/ # Columnas estándar
│   ├── 07_Documentacion/                # Offline, Permisos, Diccionario
│   └── 08_Instrucciones_Paso_A_Paso/    # Guía 9 pasos ~60 min
│
├── Fase2_Mermas_2.0/                    # FASE 2 - Mermas avanzadas
│   ├── 01_Columnas_Extendidas_Mermas.csv
│   ├── 02_Actions_Mermas_Flujo.json
│   ├── 03_Bots_Mermas.json
│   ├── 04_Tasks_Bots_Mermas.json
│   ├── 05_Views_Mermas.json
│   └── 06_Checklist_Validacion_Mermas.md
│
├── Fase3_Inventario_Fisico/             # FASE 3 - Conteos físicos
│   ├── 01_Tablas_Nuevas/                # 4 CSVs (Plantillas, Conteos, Items, Ajustes)
│   ├── 02_Security_Filters/
│   ├── 03_Columnas_Auditoria_Por_Tabla/
│   ├── 04_Actions_Inventario.json
│   ├── 05_Bots_Inventario.json
│   ├── 06_Tasks_Bots_Inventario.json
│   ├── 07_Views_Inventario.json
│   └── 08_Checklist_Validacion_Inventario.md
│
├── Fase4_Transferencias/                # FASE 4 - Traslados entre sucursales
│   ├── 01_Tablas_Nuevas/                # 3 CSVs (Ordenes, Items, Recepciones)
│   ├── 02_Security_Filters/
│   ├── 03_Columnas_Auditoria_Por_Tabla/
│   ├── 04_Actions_Transferencias.json
│   ├── 05_Bots_Transferencias.json
│   ├── 06_Tasks_Bots_Transferencias.json
│   ├── 07_Views_Transferencias.json
│   └── 08_Checklist_Validacion_Transferencias.md
│
├── Fase5_Recetas_Costos_Produccion/     # FASE 5 - Recetas, costeo, producción
│   ├── 01_Tablas_Nuevas/                # 5 CSVs (Recetas, R_Ing, Prod, P_Det, Costos_Hist)
│   ├── 02_Security_Filters/
│   ├── 03_Columnas_Auditoria_Por_Tabla/
│   ├── 04_Actions_Recetas_Costos_Produccion.json
│   ├── 05_Bots_Recetas_Costos_Produccion.json
│   ├── 06_Tasks_Bots_Recetas_Costos_Produccion.json
│   ├── 07_Views_Recetas_Costos_Produccion.json
│   └── 08_Checklist_Validacion_Recetas_Costos_Produccion.md
│
├── Fase6_Tareas_KPIs_Capacitacion_Incidencias/  # FASE 6 - Operaciones completas
│   ├── 01_Tablas_Nuevas/                # 8 CSVs (Tareas, Prog, Ejec, KPIs, Cap, Cap_Usu, Inc)
│   ├── 02_Security_Filters/
│   ├── 03_Columnas_Auditoria_Por_Tabla/
│   ├── 04_Actions_Fase6.json
│   ├── 05_Bots_Fase6.json
│   ├── 06_Tasks_Bots_Fase6.json
│   ├── 07_Views_Fase6.json
│   └── 08_Checklist_Validacion_Fase6.md
│
├── api_manifests/                       # MANIFIESTOS PARA API AUTOMÁTICA
│   ├── phase_1_fundaciones.json
│   ├── phase_2_mermas.json
│   ├── phase_3_inventario_fisico.json
│   ├── phase_4_transferencias.json
│   ├── phase_5_recetas_costos_produccion.json
│   └── phase_6_tareas_kpis_capacitacion_incidencias.json
│
├── config/
│   └── deploy_master.yaml               # Configuración maestra
│
├── deploy_master.py                     # SCRIPT MAESTRO DE DESPLIEGUE
│
└── README_MAESTRO.md                    # ESTE ARCHIVO
```

---

## 🔗 DEPENDENCIAS ENTRE FASES (CRÍTICO)

```
┌─────────────┐
│   FASE 1    │  ← BASE: Usuarios, Sucursales, Roles, Auditoría, Offline, Config
│ Fundaciones │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   FASE 2    │  ← Extiende: Registro_de_Mermas_y_Vencimientos + Ingredientes_y_Stock
│  Mermas 2.0 │     Requiere: Security Filters Fase 1, User Roles, Auditoría
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   FASE 3    │  ← Nuevas: Plantillas, Conteos, Items, Ajustes
│ Inventario  │     Requiere: Ingredientes_y_Stock (F1), Mermas 2.0 (F2), Seguridad
│  Físico     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   FASE 4    │  ← Nuevas: Ordenes, Items, Recepciones Transferencia
│Transferencias│     Requiere: Ingredientes_y_Stock (F1), Inventario (F3), Seguridad
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   FASE 5    │  ← Nuevas: Recetas, R_Ing, Produccion, P_Det, Costos_Hist
│  Recetas +  │     Requiere: Ingredientes_y_Stock (F1), Mermas (F2), Transferencias (F4)
│ Costos +    │
│ Producción  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   FASE 6    │  ← Nuevas: 8 tablas operativas
│ Tareas +    │     Requiere: TODO LO ANTERIOR (integración total)
│ KPIs + Cap  │
│ + Incidencias
└─────────────┘
```

**REGLA DE ORO: No saltar fases. Cada fase valida la anterior antes de continuar.**

---

## ⏱️ TIEMPOS ESTIMADOS DE DESPLIEGUE MANUAL (Staging)

| Fase | Tiempo Setup | Tests Validación | Total Estimado |
|------|--------------|------------------|----------------|
| **1** Fundaciones | 60 min | 15 min | **~75 min** |
| **2** Mermas 2.0 | 45 min | 20 min | **~65 min** |
| **3** Inventario Físico | 60 min | 25 min | **~85 min** |
| **4** Transferencias | 75 min | 30 min | **~105 min** |
| **5** Recetas + Costos + Prod | 90 min | 35 min | **~125 min** |
| **6** Tareas + KPIs + Cap + Inc | 120 min | 45 min | **~165 min** |
| **TOTAL** | **~7.5 horas** | **~2.7 horas** | **~10.5 horas** |

> **Con API automatizada (deploy_master.py)**: ~15-20 min total (secuencial con validación)

---

## 🚀 OPCIÓN A: DESPLIEGUE MANUAL (PASO A PASO)

### Prerrequisitos
1. Cuenta Google con acceso a AppSheet (appsheet.com)
2. Google Sheet `ERP_Fundaciones_Data` creado y compartido
3. 6 usuarios de prueba creados con emails reales
4. AppSheet App creada (puede estar vacía inicialmente)

### Orden de Ejecución por Fase

#### FASE 1: FUNDACIONES (Base)
```bash
# 1. Importar 6 CSVs a Google Sheets (hojas nuevas)
#    Carpeta: Fundaciones/01_CSVs_Google_Sheets/

# 2. En AppSheet Editor → Data → Tables → + Table × 6
#    Vincular cada hoja, configurar Keys, Is Part Of

# 3. Pegar 14 Security Filters (Fundaciones/02_Security_Filters/)
#    Data → Tables → [tabla] → Security Filter

# 4. Aplicar columnas de auditoría (Fundaciones/03_Columnas_Auditoria_Por_Tabla/)
#    Data → Tables → [tabla] → Columns → Add virtual columns

# 5. Configurar User Roles (Admin, Encargado, Operador)
#    Security → User Roles → Add role + assign emails

# 6. Habilitar Offline Sync
#    App → Settings → Offline → Enable

# 7. Regenerate Structure + Deploy → Staging

# 8. TESTS: Guia_Despliegue_Fase1_Fundaciones.md (15 tests)
```

#### FASE 2: MERMAS 2.0
```bash
# 1. Agregar columnas extendidas a Registro_de_Mermas_y_Vencimientos
#    (Fase2_Mermas_2.0/01_Columnas_Extendidas_Mermas.csv)

# 2. Importar Actions (02_Actions_Mermas_Flujo.json)
#    Behavior → Actions → Import

# 3. Importar Bots (03_Bots_Mermas.json)
#    Automation → Bots → Import

# 4. Importar Tasks (04_Tasks_Bots_Mermas.json)
#    Automation → Tasks → Import

# 5. Importar Views (05_Views_Mermas.json)
#    UX → Views → Import

# 6. Regenerate + Deploy Staging + Tests (06_Checklist_Validacion_Mermas.md)
```

#### FASE 3: INVENTARIO FÍSICO
```bash
# 1. Crear 4 tablas nuevas en Sheets (CSVs en 01_Tablas_Nuevas/)
# 2. Vincular en AppSheet con Is Part Of (Conteos → Items)
# 3. Security Filters (02_Security_Filters/)
# 4. Columnas auditoría (03_Columnas_Auditoria_Por_Tabla/)
# 5. Actions (04_Actions_Inventario.json) - 12 actions
# 6. Bots (05_Bots_Inventario.json) - 4 bots
# 7. Tasks (06_Tasks_Bots_Inventario.json)
# 8. Views (07_Views_Inventario.json) - 8 vistas
# 7. Config_Global: CFG_010, CFG_011, CFG_012
# 8. Regenerate + Deploy + Tests (08_Checklist_Validacion_Inventario.md)
```

#### FASE 4: TRANSFERENCIAS
```bash
# 1. 3 tablas nuevas en Sheets (01_Tablas_Nuevas/)
# 2. Vincular: Ordenes → Items (Is Part Of)
# 3. Security Filters (3 filtros multi-sucursal)
# 4. Actions (14 actions - flujo estados completo)
# 5. Bots (4) + Tasks (8) - notificaciones por estado
# 6. Views (9) - Origen, Destino, Preparar, Despachar, Recibir, Dashboard
# 7. Config_Global: CFG_013, CFG_014
# 8. Tests: 22 casos (flujo completo + edge cases + integración F2,F3)
```

#### FASE 5: RECETAS + COSTOS + PRODUCCIÓN
```bash
# 1. 5 tablas nuevas en Sheets (Recetas, R_Ing, Produccion, P_Det, Costos_Hist)
# 2. Vincular: Recetas → R_Ing (Is Part Of), Produccion → P_Det (Is Part Of)
# 3. Security Filters (5 filtros - herencia sucursal)
# 4. Actions (19) - versionado recetas, producción, costeo, histórico
# 5. Bots (7) + Tasks (14) - recálculo costos diario, alertas variación
# 6. Views (15) - Admin global, Encargado sucursal, Operador producción
# 7. Config_Global: CFG_015, CFG_016, CFG_017, CFG_018
# 8. Tests: 25 casos (ciclo vida receta + producción + costos + integración)
```

#### FASE 6: TAREAS + KPIs + CAPACITACIÓN + INCIDENCIAS
```bash
# 1. 8 tablas nuevas en Sheets (Tareas, Prog, Ejec, KPIs, Reg_KPI, Cap, Cap_Usu, Inc)
# 2. Security Filters (8 filtros - operador ve solo sus asignaciones)
# 3. Actions (20) - ejecución tareas, checklists, incidencias, capacitaciones
# 4. Bots (8) + Tasks (19) - scheduler tareas, KPIs, SLA incidencias, vencimientos cap
# 4. Views (22) - Dashboards Admin/Encargado, Deck Operador "Hoy"
# 5. Config_Global: CFG_019 al CFG_025
# 6. Tests: 28 casos (ciclo tareas + KPIs + capacitación + incidencias + integración total)
```

---

## 🤖 OPCIÓN B: DESPLIEGUE AUTOMATIZADO VIA API (RECOMENDADO CUANDO TENGAS ACCESO)

### Preparación Previa
```bash
# 1. Google Cloud Project
gcloud projects create templo-smash-erp
gcloud services enable appsheet.googleapis.com sheets.googleapis.com drive.googleapis.com

# 2. Service Account con roles
gcloud iam service-accounts create erp-deployer
gcloud projects add-iam-policy-binding templo-smash-erp \
  --member="serviceAccount:erp-deployer@templo-smash-erp.iam.gserviceaccount.com" \
  --role="roles/editor"

# 3. Descargar JSON credenciales
gcloud iam service-accounts keys create ./credentials/service-account.json \
  --iam-account=erp-deployer@templo-smash-erp.iam.gserviceaccount.com

# 4. Editar config/deploy_master.yaml
#    - spreadsheet_id: TU_SPREADSHEET_ID
#    - project_id: templo-smash-erp
```

### Ejecución

```bash
# DRY-RUN (simulación - seguro, por defecto)
python deploy_master.py --phase all --env staging --dry-run

# DESPLIEGUE REAL STAGING
python deploy_master.py --phase all --env staging --no-dry-run

# SOLO FASES ESPECÍFICAS
python deploy_master.py --phase 1,2,3 --env staging --no-dry-run

# PRODUCCIÓN (requiere confirmación manual)
python deploy_master.py --phase all --env production --no-dry-run
```

### Qué Hace el Script Automáticamente
1. **Valida dependencias** entre fases
2. **Crea tablas en Sheets** via Sheets API (cabeceras + datos ejemplo)
3. **Registra tablas en AppSheet** via AppSheet API
4. **Aplica Security Filters** via API
5. **Crea Actions, Bots, Tasks** via Automation API
6. **Importa Vistas** via UX API
7. **Regenerate Structure + Deploy**
8. **Ejecuta tests de validación** (via API o Playwright)
9. **Genera reporte JSON + Markdown** con métricas completas

---

## ✅ CHECKLIST MAESTRO PRE-DESPLIEGUE

### Infraestructura
- [ ] Google Cloud Project creado y APIs habilitadas
- [ ] Service Account con roles Editor/Sheets/Drive
- [ ] Credenciales JSON en `./credentials/service-account.json`
- [ ] Spreadsheet `ERP_Fundaciones_Data` creado
- [ ] Spreadsheet ID configurado en `config/deploy_master.yaml`

### Usuarios de Prueba (6 mínimo)
| Rol | Email | Sucursal | Fase Mínima |
|-----|-------|----------|-------------|
| Administrador | admin@test.com | Global | 1 |
| Encargado | encargado1@test.com | Sucursal 1 | 1 |
| Encargado | encargado2@test.com | Sucursal 2 | 1 |
| Operador | operador1a@test.com | Sucursal 1 | 1 |
| Operador | operador1b@test.com | Sucursal 1 | 2 |
| Operador | operador2a@test.com | Sucursal 2 | 2 |

### AppSheet App
- [ ] App creada en appsheet.com
- [ ] Conectada al Spreadsheet `ERP_Fundaciones_Data`
- [ ] Deployment profile "Staging" configurado

---

## 🧪 ESTRATEGIA DE TESTING

### Por Fase (ejecutar en orden)
1. **Tests Unitarios** → Cada action/bot/vista individual
2. **Tests de Integración** → Flujos cruzados (ej: Transferencia → Stock → Merma)
3. **Tests de Seguridad** → Security Filters por rol, offline sync
4. **Tests de Regresión** → Verificar que fases anteriores no se rompen
5. **Tests UAT** → Con usuarios reales en Staging

### Matriz de Cobertura Mínima
| Fase | Unit | Integración | Seguridad | Regresión | UAT |
|------|------|-------------|-----------|-----------|-----|
| 1 | 5 | 3 | 4 | 0 | 3 |
| 2 | 4 | 5 | 3 | 3 | 3 |
| 3 | 5 | 5 | 4 | 3 | 3 |
| 4 | 6 | 6 | 4 | 3 | 3 |
| 5 | 8 | 8 | 4 | 3 | 2 |
| 6 | 10 | 8 | 5 | 3 | 2 |

---

## 📊 MÉTRICAS DE ÉXITO (KPIs DE DESPLIEGUE)

| Métrica | Target | Crítico |
|---------|--------|---------|
| Tiempo total despliegue (API) | < 20 min | ✅ |
| Tasa éxito tests automatizados | 100% | ✅ |
| Security Filters sin bypass | 100% | ✅ |
| Offline sync funcional | 100% | ✅ |
| Notificaciones Push entregadas | > 99% | ✅ |
| Zero data loss en migraciones | 100% | ✅ |
| Rollback time < 5 min | ✅ | ✅ |

---

## 🔄 ROLLBACK Y RECUPERACIÓN

### Si una Fase Falla en Staging
```bash
# 1. AppSheet → Deployment → History → Rollback to previous
# 2. Revisar logs en deployment_report.json
# 3. Corregir en archivos fuente (CSVs, JSONs, MDs)
# 4. Re-ejecutar solo la fase fallida:
python deploy_master.py --phase 4 --env staging --no-dry-run
```

### Si Producción Tiene Incidente Crítico
1. **Inmediato**: AppSheet → Deployment → Disable App (modo mantenimiento)
2. **Rollback**: Deployment → History → Última versión estable
3. **Comunicar**: Webhook/Slack a stakeholders
4. **Post-mortem**: Análisis de causa raíz en 24h

---

## 📈 ROADMAP POST-FASE 6 (Cuando API esté operativa)

| Prioridad | Iniciativa | Descripción | Esfuerzo |
|-----------|------------|-------------|----------|
| **P0** | Master Deploy Script | Automatizar todo con deploy_master.py | Hecho ✅ |
| **P0** | API Manifests | JSON listos para agente autónomo | Hecho ✅ |
| **P1** | Webhooks Salientes | POS, Contabilidad, RRHH externos | 2-3 semanas |
| **P1** | Apps Script Backend | Costeo estándar, nóminas, facturación | 3-4 semanas |
| **P2** | PowerBI/Looker Connector | Dashboards ejecutivos externos | 1-2 semanas |
| **P2** | Multi-tenant SaaS | Clonar app por cliente via Config_Global | 4-6 semanas |
| **P3** | Mobile App Nativa | Capacitor/React Native wrapper | 8-12 semanas |
| **P3** | IA Predictiva | Forecast ventas, stock óptimo, personal | 6-8 semanas |

---

## 🆘 SOPORTE Y ESCALACIÓN

### Niveles de Soporte
| Nivel | Qué Cubre | SLA | Contacto |
|-------|-----------|-----|----------|
| **L1** | Dudas uso, checklists, validación manual | 4h | Chat interno |
| **L2** | Errores deploy, bugs actions/bots, security filters | 2h | Video call |
| **L3** | Arquitectura, migración datos, performance, API | 1h | Llamada directa |

### Escalación Automática
- Deploy falla 2 veces → Alerta L2
- Test crítico falla en Staging → Bloqueo deploy Prod + Alerta L3
- Security Filter bypass detectado → Alerta L3 inmediata

---

## 📝 CONTROL DE VERSIONES Y CHANGELOG

### Versioning Scheme
```
MAJOR.MINOR.PATCH-FASE
Ej: 1.0.0-F1  → Fundaciones completa
    1.2.0-F3  → Fundaciones + Mermas + Inventario
    2.0.0-F6  → ERP Completo (6 fases)
```

### Changelog Resumido
| Versión | Fecha | Fases | Cambios Principales |
|---------|-------|-------|---------------------|
| 1.0.0-F1 | 2026-07-30 | 1 | Multi-sucursal, Roles, Auditoría, Offline |
| 1.1.0-F2 | 2026-07-30 | 1-2 | Mermas 2.0: Estados, Stock, Merma auto, Notificaciones |
| 1.2.0-F3 | 2026-07-30 | 1-3 | Inventario Físico: Plantillas, Conteos, Tolerancias, Ajustes |
| 1.3.0-F4 | 2026-07-30 | 1-4 | Transferencias: Origen→Destino, Stock dual, Recepción diffs |
| 1.4.0-F5 | 2026-07-30 | 1-5 | Recetas BOM, Costeo, Versionado, Producción real vs teórico |
| **2.0.0-F6** | **2026-07-30** | **1-6** | **ERP COMPLETO: Tareas, KPIs, Capacitación, Incidencias, SLA** |

---

## 🎯 PRÓXIMOS PASOS INMEDIATOS (TU ACCIÓN)

1. **Revisa** `config/deploy_master.yaml` → Pon tu `spreadsheet_id` y `project_id`
2. **Crea** Service Account en GCP → Descarga JSON a `./credentials/service-account.json`
3. **Ejecuta** dry-run: `python deploy_master.py --phase all --env staging --dry-run`
4. **Valida** reporte generado → `deployment_report.md`
5. **Cuando tengas API acceso real**: `python deploy_master.py --phase 1 --env staging --no-dry-run`
6. **Itera** fase por fase hasta completar las 6

---

## 📞 CONTACTO Y RECURSOS

- **Documentación AppSheet API**: https://developers.google.com/appsheet/api
- **Google Sheets API**: https://developers.google.com/sheets/api
- **AppSheet Automation**: https://help.appsheet.com/automation
- **Security Filters Guide**: https://help.appsheet.com/security-filters

---

**🎉 ¡TERRENO 100% PREPARADO PARA DESPLIEGUE AUTOMÁTICO CUANDO TENGAS API ACCESO!**

*Generado automáticamente por Hermes Agent - Polymath Elite Agent*
*Fecha: 2026-07-30 | Versión: 2.0.0-F6*