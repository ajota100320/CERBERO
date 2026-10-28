# Checklist de Validación - Fase 6: Tareas + Horarios + KPIs + Capacitación + Incidencias

## PRE-REQUISITOS (Fase 1-5 completadas y validadas)
- [ ] Fase 1: Fundaciones (Multisucursal, Roles, Auditoría, Offline) → Deploy Staging OK
- [ ] Fase 2: Mermas 2.0 (Flujo completo, Stock, Notificaciones) → Deploy Staging OK
- [ ] Fase 3: Inventario Físico (Conteos, Ajustes, Tolerancias) → Deploy Staging OK
- [ ] Fase 4: Transferencias (Origen→Destino, Stock, Recepción) → Deploy Staging OK
- [ ] Fase 5: Recetas + Costos + Producción (BOM, Costeo, Stock real) → Deploy Staging OK
- [ ] 6 usuarios de prueba funcionando en Staging
- [ ] Security Filters + User Roles + Offline Sync operativos en todas las tablas

---

## PASO 1: CREAR 8 TABLAS NUEVAS EN GOOGLE SHEETS (20 min)

### Hojas nuevas en `ERP_Fundaciones_Data`:

| Hoja | Columnas (cabeceras de CSVs) | Datos ejemplo |
|------|------------------------------|---------------|
| `Tareas` | `Tarea_ID,Nombre,Categoria,Descripcion,Es_Recurrente,Duracion_Estimada_Min,Es_Obligatoria,Checklist_JSON,Es_Activa,Sucursal_ID,Fecha_Creacion,Creado_Por,Sync_Pending?` | 6 filas del CSV |
| `Tarea_Programaciones` | `Prog_ID,Tarea_ID,Sucursal_ID,Frecuencia,Dias_Semana,Hora_Programada,Hora_Ventana_Fin,Responsable_Rol,Responsable_Usuario_Especifico,Es_Activa,Aplica_Festivos,Notificar_Antes_Min,Fecha_Creacion,Creado_Por,Sync_Pending?` | 6 filas del CSV |
| `Tarea_Ejecuciones` | `Ejec_ID,Prog_ID,Tarea_ID,Sucursal_ID,Ejecutada_Por,Fecha_Ejecucion,Hora_Inicio,Hora_Fin,Duracion_Real_Min,Estado,Checklist_Respuestas_JSON,Evidencia_Fotos,Observaciones,Incidencia_Generada?,Incidencia_ID,Fecha_Creacion,Creado_Por,Sync_Pending?` | 3 filas del CSV |
| `KPI_Definiciones` | `KPI_ID,Nombre,Categoria,Descripcion,Formula_AppSheet,Unidad_Medida,Frecuencia_Calculo,Sentido_Bueno,Umbral_Verde,Umbral_Amarillo,Umbral_Rojo,Responsable_Rol,Sucursal_ID,Es_Activa,Visible_Por_Rol,Fecha_Creacion,Creado_Por,Sync_Pending?` | 8 filas del CSV |
| `Registros_KPI` | `Registro_ID,KPI_ID,Sucursal_ID,Periodo_Inicio,Periodo_Fin,Valor,Estado_KPI,Tendencia,Fecha_Calculo,Calculado_Por,Sync_Pending?` | 8 filas del CSV |
| `Capacitaciones` | `Capac_ID,Titulo,Categoria,Descripcion,Contenido_URL,Duracion_Min,Tipo,Version,Estado,Aprobada_Por,Fecha_Aprobacion,Es_Obligatoria,Frecuencia_Renovacion_Meses,Sucursal_ID,Fecha_Creacion,Creado_Por,Sync_Pending?` | 6 filas del CSV |
| `Capacitaciones_Usuarios` | `Cap_Usu_ID,Capac_ID,Usuario_ID,Sucursal_ID,Estado,Fecha_Asignacion,Fecha_Vencimiento,Fecha_Completado,Puntuacion_Examen,Observaciones,Es_Recurrente?,Fecha_Proxima_Renovacion,Fecha_Creacion,Creado_Por,Sync_Pending?` | 8 filas del CSV |
| `Incidencias` | `Inc_ID,Titulo,Tipo,Severidad,Descripcion,Sucursal_ID,Reportada_Por,Asignada_A,Fecha_Reporte,Fecha_Asignacion,Fecha_Cierre,Estado,SLA_Horas,Tiempo_Respuesta_Horas,Tiempo_Resolucion_Horas,Solucion,Incidencia_Relacionada_ID,Origen_Incidencia,Evidencia_Inicial,Fecha_Creacion,Creado_Por,Sync_Pending?` | 5 filas del CSV |

> **Tip:** Agrega columnas de auditoría estándar según `03_Columnas_Auditoria_Por_Tabla/Columnas_Fase6.csv`

---

## PASO 2: VINCULAR 8 TABLAS EN APP SHEET STAGING (20 min)

**Data → Tables → + Table** × 8:

| Tabla | Source | Worksheet | Key | Row ID | Is Part Of? |
|-------|--------|-----------|-----|--------|-------------|
| `Tareas` | `ERP_Fundaciones_Data` | `Tareas` | `Tarea_ID` | `Tarea_ID` | No |
| `Tarea_Programaciones` | `ERP_Fundaciones_Data` | `Tarea_Programaciones` | `Prog_ID` | `Prog_ID` | No |
| `Tarea_Ejecuciones` | `ERP_Fundaciones_Data` | `Tarea_Ejecuciones` | `Ejec_ID` | `Ejec_ID` | No |
| `KPI_Definiciones` | `ERP_Fundaciones_Data` | `KPI_Definiciones` | `KPI_ID` | `KPI_ID` | No |
| `Registros_KPI` | `ERP_Fundaciones_Data` | `Registros_KPI` | `Registro_ID` | `Registro_ID` | No |
| `Capacitaciones` | `ERP_Fundaciones_Data` | `Capacitaciones` | `Capac_ID` | `Capac_ID` | No |
| `Capacitaciones_Usuarios` | `ERP_Fundaciones_Data` | `Capacitaciones_Usuarios` | `Cap_Usu_ID` | `Cap_Usu_ID` | No |
| `Incidencias` | `ERP_Fundaciones_Data` | `Incidencias` | `Inc_ID` | `Inc_ID` | No |

> **Click "Regenerate Structure" después de las 8**

---

## PASO 3: CONFIGURAR COLUMNAS CRÍTICAS (35 min)

### Tareas:
- `Sucursal_ID` → Ref → Sucursales, **Initial Value**: `LOOKUP(USEREMAIL(), "Usuarios_Sucursales", "Email", "Sucursal_ID")`
- `Checklist_JSON` → LongText (JSON array items: `{"item": "texto", "tipo": "boolean|numero|lista|cantidad"}`)
- `Es_Activa?` → Initial Value: TRUE

### Tarea_Programaciones:
- `Tarea_ID` → Ref → Tareas
- `Sucursal_ID` → **App Formula**: `LOOKUP([Tarea_ID], "Tareas", "Tarea_ID", "Sucursal_ID")`
- `Frecuencia` → Enum: Diaria, Semanal, Quincenal, Mensual, Personalizada
- `Dias_Semana` → Text: "1,2,3,4,5,6,7" (CSV, 1=Lun..7=Dom)
- `Hora_Programada` / `Hora_Ventana_Fin` → Time
- `Responsable_Rol` → Enum: Operador, Encargado, Administrador
- `Notificar_Antes_Min` → Initial Value: 15

### Tarea_Ejecuciones:
- `Prog_ID` → Ref → Tarea_Programaciones
- `Tarea_ID` → **App Formula**: `LOOKUP([Prog_ID], "Tarea_Programaciones", "Prog_ID", "Tarea_ID")`
- `Sucursal_ID` → **App Formula**: `LOOKUP([Prog_ID], "Tarea_Programaciones", "Prog_ID", "Sucursal_ID")`
- `Ejecutada_Por` → Initial Value: `USEREMAIL()`
- `Fecha_Ejecucion` → Initial Value: `TODAY()`
- `Hora_Inicio` → Initial Value: `NOW()`
- `Duracion_Real_Min` → **App Formula**: `[Hora_Fin] - [Hora_Inicio]`
- `Estado` → Enum: Pendiente, En_Proceso, Completada, Omitida, Con_Incidencia
- **Valid_If Estado**: Ver Security Filters doc
- `Incidencia_Generada?` + `Incidencia_ID` → Bot auto-genera si checklist falla

### KPI_Definiciones:
- `Formula_AppSheet` → LongText (guarda fórmula como string, Bot la evalúa)
- `Frecuencia_Calculo` → Enum: Diaria, Semanal, Quincenal, Mensual
- `Sentido_Bueno` → Enum: Mayor, Menor, Rango
- `Umbral_Verde/Amarillo/Rojo` → Decimal
- `Visible_Por_Rol` → Text: "Administrador,Encargado" (CSV)

### Registros_KPI:
- `KPI_ID` → Ref → KPI_Definiciones
- `Sucursal_ID` → **App Formula**: `LOOKUP([KPI_ID], "KPI_Definiciones", "KPI_ID", "Sucursal_ID")`
- `Estado_KPI` → Enum: Verde, Amarillo, Rojo
- **App Formula Estado_KPI** (evaluada por Bot):
```
SWITCH([KPI_ID].[Sentido_Bueno],
  "Mayor", IF([Valor] >= [KPI_ID].[Umbral_Verde], "Verde", IF([Valor] >= [KPI_ID].[Umbral_Amarillo], "Amarillo", "Rojo")),
  "Menor", IF([Valor] <= [KPI_ID].[Umbral_Verde], "Verde", IF([Valor] <= [KPI_ID].[Umbral_Amarillo], "Amarillo", "Rojo")),
  "Rango", IF(AND([Valor] >= [KPI_ID].[Umbral_Verde], [Valor] <= [KPI_ID].[Umbral_Amarillo]), "Verde", IF([Valor] <= [KPI_ID].[Umbral_Rojo], "Amarillo", "Rojo")),
  "Verde"
)
```

### Capacitaciones:
- `Sucursal_ID` → Ref → Sucursales, Initial Value: `LOOKUP(USEREMAIL(), "Usuarios_Sucursales", "Email", "Sucursal_ID")`
- `Estado` → Enum: Borrador, En_Revision, Aprobada, Obsoleta
- `Es_Obligatoria` → Initial Value: TRUE
- `Frecuencia_Renovacion_Meses` → Initial Value: 12

### Capacitaciones_Usuarios:
- `Capac_ID` → Ref → Capacitaciones
- `Usuario_ID` → Initial Value: `USEREMAIL()`
- `Sucursal_ID` → **App Formula**: `LOOKUP([Capac_ID], "Capacitaciones", "Capac_ID", "Sucursal_ID")`
- `Estado` → Enum: Pendiente, En_Progreso, Completada, Vencida, Eximida
- `Fecha_Vencimiento` → **App Formula**: `[Fecha_Asignacion] + [Capac_ID].[Frecuencia_Renovacion_Meses] * 30`
- `Es_Recurrente?` → Initial Value: TRUE
- `Fecha_Proxima_Renovacion` → **App Formula**: `[Fecha_Completado] + [Capac_ID].[Frecuencia_Renovacion_Meses] * 30`

### Incidencias:
- `Sucursal_ID` → Ref → Sucursales, Initial Value: `LOOKUP(USEREMAIL(), "Usuarios_Sucursales", "Email", "Sucursal_ID")`
- `Reportada_Por` → Initial Value: `USEREMAIL()`
- `Fecha_Reporte` → Initial Value: `NOW()`
- `Estado` → Enum: Abierta, En_Proceso, Escalada, Resuelta, Cerrada, Cancelada
- **Valid_If Estado**: Ver Security Filters doc
- `SLA_Horas` → Initial Value por Severidad: Crítica=1, Alta=4, Media=8, Baja=24 (Valid_If o Bot al crear)
- `Tiempo_Respuesta_Horas` → **App Formula**: `([Fecha_Asignacion] - [Fecha_Reporte]) * 24`
- `Tiempo_Resolucion_Horas` → **App Formula**: `([Fecha_Cierre] - [Fecha_Reporte]) * 24`
- `Origen_Incidencia` → Enum: Tarea_Ejecucion, Produccion, Mermas, Inventario, Transferencia, Manual, Cliente
- `Evidencia_Inicial` → Image

---

## PASO 4: PEGAR 8 SECURITY FILTERS (5 min)

Desde `02_Security_Filters/Security_Filters_Fase6.md`:

| Tabla | Expresión |
|-------|-----------|
| `Tareas` | `OR(USERROLE("Administrador"), AND([Es_Activa?] = TRUE, IN([Sucursal_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL()))))` |
| `Tarea_Programaciones` | `OR(USERROLE("Administrador"), IN([Sucursal_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL())))` |
| `Tarea_Ejecuciones` | `OR(USERROLE("Administrador"), IN([Sucursal_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL())))` |
| `KPI_Definiciones` | `OR(USERROLE("Administrador"), AND([Es_Activa?] = TRUE, OR([Sucursal_ID] = "", IN([Sucursal_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL())))))` |
| `Registros_KPI` | `OR(USERROLE("Administrador"), IN([Sucursal_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL())))` |
| `Capacitaciones` | `OR(USERROLE("Administrador"), AND([Es_Activa?] = TRUE, IN([Sucursal_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL()))))` |
| `Capacitaciones_Usuarios` | `OR(USERROLE("Administrador"), AND([Usuario_ID] = USEREMAIL()), IN([Sucursal_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL())))` |
| `Incidencias` | `OR(USERROLE("Administrador"), IN([Sucursal_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL())))` |

---

## PASO 5: CREAR ACCIONES CLAVE (Behavior → Actions) (45 min)

| Acción | Tabla | Tipo | Qué hace | Show_If |
|--------|-------|------|----------|---------|
| `Tarea_Crear_Nueva` | Tareas | App: go to view | Formulario nueva tarea | Encargado/Admin |
| `Tarea_Programar` | Tareas | App: go to view | Abre formulario programar tarea | Encargado/Admin |
| `Tarea_Clonar` | Tareas | Data: add row | Duplica tarea + programa | Encargado/Admin |
| `Tarea_Ejecutar_Iniciar` | Tarea_Ejecuciones | Data: set values | Estado=En_Proceso, Hora_Inicio=NOW() | Estado=Pendiente, Rol responsable |
| `Tarea_Ejecutar_Completar` | Tarea_Ejecuciones | Data: set values + RefAction | Estado=Completada, Hora_Fin=NOW(), Checklist, Evidencia | Estado=En_Proceso, Rol responsable |
| `Tarea_Ejecutar_Omitir` | Tarea_Ejecuciones | Data: set values | Estado=Omitida, requiere justificación | Estado=Pendiente, Encargado/Admin |
| `Action_Generar_Incidencia_Desde_Checklist` | Tarea_Ejecuciones | Data: add row (Incidencias) | Crea incidencia si checklist tiene fallos críticos | Estado=Con_Incidencia, System |
| `Capacitacion_Crear` | Capacitaciones | App: go to view | Formulario nueva capacitación | Encargado/Admin |
| `Capacitacion_Aprobar` | Capacitaciones | Data: set values | Estado=Aprobada, Aprobada_Por, Fecha_Aprobacion | Estado=En_Revision, Admin |
| `Capacitacion_Asignar_Usuarios` | Capacitaciones | Data: add row (set) | Asigna a usuarios por rol/sucursal | Admin/Encargado |
| `Capacitacion_Iniciar` | Capacitaciones_Usuarios | Data: set values | Estado=En_Progreso | Estado=Pendiente, Usuario asignado |
| `Capacitacion_Completar` | Capacitaciones_Usuarios | Data: set values | Estado=Completada, Fecha_Completado=NOW(), Puntuación | Estado=En_Progreso, Usuario asignado |
| `Capacitacion_Eximir` | Capacitaciones_Usuarios | Data: set values | Estado=Eximida, requiere justificación | Encargado/Admin |
| `Incidencia_Reportar_Nueva` | Incidencias | App: go to view | Formulario nueva incidencia | Todos roles |
| `Incidencia_Asignar` | Incidencias | Data: set values | Asignada_A, Fecha_Asignacion=NOW(), Estado=En_Proceso | Estado=Abierta, Encargado/Admin |
| `Incidencia_Resolver` | Incidencias | Data: set values | Estado=Resuelta, Solucion, Fecha_Cierre=NOW() | Estado=En_Proceso, Asignado/Admin |
| `Incidencia_Cerrar` | Incidencias | Data: set values | Estado=Cerrada (validación final) | Estado=Resuelta, Encargado/Admin |
| `Incidencia_Escalar` | Incidencias | Data: set values | Estado=Escalada, Asignada_A=Admin | Estado∈{Abierta,En_Proceso}, Encargado/Admin |
| `Action_Calcular_KPI_Single` | Registros_KPI | Data: add row | Evalúa Formula_AppSheet, escribe registro | System (Bot) |

---

## PASO 6: IMPORTAR BOTS + TASKS (Automation → Import) (20 min)

1. **Automation → Bots → Import** → `05_Bots_Fase6.json` (crear archivo con los 8 bots)
2. **Automation → Tasks → Import** → `06_Tasks_Bots_Fase6.json`
3. Verifica bots creados:
   - `Bot_Tareas_Programador_Diario` (schedule: 06:00 diario → crea Tarea_Ejecuciones de hoy)
   - `Bot_Tareas_Notificaciones` (trigger: Tarea_Ejecuciones Estado)
   - `Bot_Tareas_Checklist_Incidencia` (trigger: Tarea_Ejecuciones Completada → evalúa checklist)
   - `Bot_KPIs_Calculador` (schedule: 07:00 diario/semanal/mensual según frecuencia)
   - `Bot_KPIs_Alertas` (trigger: Registros_KPI Estado_KPI cambia)
   - `Bot_Capacitaciones_Vencimientos` (schedule: 08:00 diario → alertas + auto-vencidas + renovaciones)
   - `Bot_Incidencias_SLA_Escalado` (schedule: cada 30 min → SLA vencidos + escalado)
   - `Bot_Incidencias_Flujo` (trigger: Incidencias Estado)
4. **Enable = ON** en todos

---

## PASO 7: IMPORTAR VISTAS (UX → Views → Import) (15 min)

`07_Views_Fase6.json` → 22 vistas:
- Admin: Todas tareas, Programaciones, KPIs Dashboard global, Capacitaciones, Incidencias, Dashboard Operaciones
- Encargado: Mis tareas, Programaciones, Ejecuciones hoy/histórico, KPIs mi sucursal, Capacitaciones equipo, Incidencias mi sucursal, Dashboard mi sucursal
- Operador: Tareas hoy (Deck), Ejecutar/Completar/Omitir, Mis capacitaciones, Mis incidencias
- Formularios: Nueva tarea, Nueva programación, Ejecutar tarea, Completar tarea, Nueva capacitación, Nueva incidencia, Resolver incidencia

---

## PASO 8: CONFIG_GLOBAL NUEVAS CLAVES (5 min)

En hoja `Config_Global` agrega:

| Config_ID | Clave | Valor | Tipo | Descripcion | Editable_Por_Rol |
|-----------|-------|-------|------|-------------|------------------|
| CFG_019 | `UMBRAL_CHECKLIST_INCIDENCIA_CRITICA` | `3` | Number | Nº items fallidos en checklist para auto-generar incidencia | Administrador |
| CFG_020 | `SLA_CRITICA_HORAS` | `1` | Number | SLA horas severidad Crítica | Administrador |
| CFG_021 | `SLA_ALTA_HORAS` | `4` | Number | SLA horas severidad Alta | Administrador |
| CFG_022 | `SLA_MEDIA_HORAS` | `8` | Number | SLA horas severidad Media | Administrador |
| CFG_023 | `SLA_BAJA_HORAS` | `24` | Number | SLA horas severidad Baja | Administrador |
| CFG_024 | `DIAS_ALERTA_CAPACITACION_ANTES_VENCER` | `7,3,1` | Text | Días antes de vencimiento para alertar (CSV) | Administrador |
| CFG_025 | `HORA_GENERACION_EJECUCIONES_DIARIAS` | `06:00` | Time | Hora para generar ejecuciones del día | Administrador |

---

## PASO 9: REGENERATE + DEPLOY STAGING (5 min)

1. **Data → Tables → Regenerate Structure**
2. **App → Settings → Deployment → Deploy → Staging**
3. Abre Staging → Login 3 roles

---

## TESTS DE VALIDACIÓN FASE 6 (Mínimo 120 min con 5 usuarios: Admin, Encargado1, Encargado2, Operador1, Operador2)

### 🔴 TEST A: CICLO TAREAS PROGRAMADAS (Apertura → Cierre)
| # | Acción | Usuario | Resultado Esperado |
|---|--------|---------|-------------------|
| A1 | 06:00 Job diario → genera `Tarea_Ejecuciones` para hoy según `Tarea_Programaciones` | Bot (auto) | Ejecuciones creadas Estado=Pendiente, **Push a responsables 15 min antes** |
| A2 | 07:00 Operador 1A → Ve "Tareas Hoy" → "Apertura Local" → "Iniciar" | Operador 1A | Estado=En_Proceso, Hora_Inicio=NOW(), abre formulario checklist |
| A3 | Operador 1A → Completa checklist (booleanos, números, lista) → "Completar" | Operador 1A | Estado=Completada, Hora_Fin=NOW(), Duracion_Real, Checklist_Respuestas_JSON, **Push a Encargado 1 "Completada"** |
| A4 | Operador 1B → "Cierre Local" → Iniciar → Completar (checklist todo OK) | Operador 1B | Estado=Completada, **% Cumplimiento KPI_004 sube** |
| A5 | Encargado 1 → Ve histórico ejecuciones → ve duraciones reales vs estimadas | Encargado 1 | Dashboard muestra métricas |

### 🟡 TEST B: CHECKLIST CON FALLOS → INCIDENCIA AUTO
| # | Escenario | Resultado |
|---|-----------|-----------|
| B1 | Operador en "Limpieza Profunda" → Checklist item "Filtros extractores" = FALSE (crítico) | Al "Completar" → **Bot detecta fallo crítico ≥ umbral (3)** → Crea `Incidencia` Tipo=Mantenimiento, Severidad=Alta, Origen=Tarea_Ejecucion, `Incidencia_Generada?`=TRUE, `Incidencia_ID` vinculada |
| B2 | Encargado ve incidencia auto-generada desde tarea | **Push a Encargado/Admin "Incidencia generada desde tarea: Limpieza Profunda"** |

### 🟢 TEST C: KPIs - CÁLCULO + SEMÁFORO + ALERTAS
| # | Acción | Resultado |
|---|--------|-----------|
| C1 | Job 07:00 → Calcula KPI_001 (Ticket prom), KPI_002 (% Merma), KPI_004 (% Cumplimiento tareas) | `Registros_KPI` creados con Valor, Estado_KPI (Verde/Amarillo/Rojo), Tendencia |
| C2 | KPI_004 (% Cumplimiento) cae a 82% (era 92%) | **Estado_KPI=Amarillo**, **Push a Encargado/Admin "🟡 ATENCIÓN: % Cumplimiento Tareas"** |
| C3 | KPI_008 (Incidencias Críticas Abiertas) = 3 | **Estado_KPI=Rojo**, **Push inmediato "🔴 CRÍTICO: Incidencias Críticas Abiertas"** |
| C4 | Admin ve Dashboard KPIs → Gráficos tendencias semanales | Charts funcionando |

### 🔴 TEST D: CAPACITACIONES - ASIGNACIÓN + RENOVACIÓN
| # | Acción | Resultado |
|---|--------|-----------|
| D1 | Admin → "Seguridad Alimentaria" (Obligatoria, 12 meses) → "Asignar a todos Operadores Sucursal 1" | 2 filas `Capacitaciones_Usuarios` creadas: Usuario1, Usuario2, Estado=Pendiente, Fecha_Vencimiento=+365 días |
| D2 | Operador 1A → Ve "Mis Capacitaciones" → "Iniciar" → Ve contenido (URL Drive) → "Completar" (puntuación 90) | Estado=Completada, Fecha_Completado=NOW(), Puntuacion_Examen=90, **Bot crea próxima asignación automática para +12 meses** |
| D3 | Operador 2A → No completa antes de Fecha_Vencimiento | Job diario → Estado=Vencida, **Push "📚 Capacitación VENCIDA: Seguridad Alimentaria"** |
| D4 | Encargado 1 → Ve "Gestión Capacitaciones" → Filtra Vencidas → "Eximir" a Operador 2A (con justificación) | Estado=Eximida, Observaciones incluye justificación |

### 🔴 TEST E: INCIDENCIAS - FLUJO COMPLETO + SLA + ESCALADO
| # | Acción | Resultado |
|---|--------|-----------|
| E1 | Operador 1A → "Reportar Incidencia" → Tipo=Mantenimiento, Severidad=Alta, "Fuga nevera" + Foto | Incidencia creada Estado=Abierta, Fecha_Reporte=NOW(), SLA_Horas=4, **Push a Encargado 1 "Nueva incidencia Alta"** |
| E2 | Encargado 1 → Asigna a sí mismo → "En Proceso" | Estado=En_Proceso, Fecha_Asignacion=NOW(), **Tiempo_Respuesta_Horas calculado** |
| E3 | Encargado 1 → "Resolver" → Solución: "Junta reemplazada, nevera OK" | Estado=Resuelta, Fecha_Cierre=NOW(), Tiempo_Resolucion_Horas=2.5, **Push a Encargado "✅ RESUELTA: Fuga nevera (2.5h ✅ CUMPLIDO)"** |
| E4 | Encargado 1 → "Cerrar" (validación final) | Estado=Cerrada |
| E5 | Incidencia Crítica sin asignar > 1h | **Job 30 min → Push a Admin "⏰ SLA VENCIDO: Incendio freidora [Critica] - 1.2h"** |
| E6 | Incidencia en En_Proceso supera SLA sin resolver | **Bot detecta → Observaciones auto "⚠️ SLA VENCIDO: 5.2h > 4h", Push Admin "Escalada recomendada"** |
| E7 | Encargado 2 → "Escalar" incidencia Media que no resuelve | Estado=Escalada, Asignada_A=Admin, **Push a Admin "🔺 ESCALADA: Queja cliente hamburguesa fría"** |

### 🟢 TEST F: INTEGRACIÓN FASE 2-5
| # | Acción | Resultado |
|---|--------|-----------|
| F1 | Tarea "Inventario Diario Críticos" → Operador detecta diferencia >5% en Carne | Checklist item falla → **Incidencia auto-generada Tipo=Inventario** + **Bot Mermas 2.0 alerta stock crítico** |
| F2 | Producción (Fase 5) → Merma real > umbral en ingrediente | **Incidencia auto-generada Tipo=Producción, Severidad=Media** |
| F3 | Transferencia (Fase 4) → Recepción con diferencias críticas | **Incidencia auto-generada Tipo=Transferencia** |

### 🔴 TEST G: OFFLINE + SYNC
| # | Escenario | Resultado |
|---|-----------|-----------|
| G1 | Operador 1A completa "Apertura Local" offline (modo avión) | Guarda local, Sync_Pending=TRUE en Tarea_Ejecuciones |
| G2 | Operador 1B reporta incidencia offline + foto | Guarda local, Sync_Pending=TRUE |
| G3 | WiFi ON → Sync manual | Ejecuciones subidas, incidencias creadas, notificaciones se envían, KPIs recalculan en próximo job |

---

## CRITERIOS ACEPTACIÓN FASE 6

| Criterio | Obligatorio |
|----------|-------------|
| Job 06:00 genera ejecuciones del día según programaciones activas | ✅ |
| Push 15 min antes a responsables (rol/usuario) | ✅ |
| Checklist dinámico (boolean, numero, lista, cantidad) funcional en formulario | ✅ |
| Checklist fallos críticos ≥ umbral → Incidencia auto (Tipo, Severidad, Origen, Vinculada) | ✅ |
| KPIs calculados por Bot según Formula_AppSheet + Frecuencia | ✅ |
| Semáforo KPI (Verde/Amarillo/Rojo) según umbrales y Sentido_Bueno | ✅ |
| Push alerta cambio semáforo KPI a roles Visible_Por_Rol | ✅ |
| Capacitaciones: Asignación masiva por rol/sucursal | ✅ |
| Renovación automática al completar (Es_Recurrente=TRUE) | ✅ |
| Alertas 7/3/1 días antes + Auto-vencida + Eximir | ✅ |
| Incidencias: Flujo Abierta→En_Proceso→Resuelta→Cerrada | ✅ |
| SLA por severidad (Crítica=1, Alta=4, Media=8, Baja=24) | ✅ |
| Tiempo_Respuesta / Tiempo_Resolución auto-calculados | ✅ |
| Job 30 min: SLA vencidos → Observaciones + Push Admin | ✅ |
| Escalado manual + auto-notificación Admin | ✅ |
| Integración: Tarea fallo → Incidencia + Mermas/Producción/Transferencia alertas | ✅ |
| Seguridad: Encargado ve su sucursal, Operador ve sus asignaciones, Admin ve todo | ✅ |
| Offline: Ejecutar tarea, Reportar incidencia, Completar capacitación → Sync OK | ✅ |
| Regenerate Structure sin errores + Deploy Staging OK | ✅ |

---

## REGISTRO EJECUCIÓN FASE 6

| Fecha | Ejecutado Por | Tests A/B/C/D/E/F/G Pasados | Bloqueadores | Firmado |
|-------|---------------|----------------------------|--------------|---------|
| | | A: / 5 | | |
| | | B: / 2 | | |
| | | C: / 4 | | |
| | | D: / 4 | | |
| | | E: / 7 | | |
| | | F: / 3 | | |
| | | G: / 3 | | |

---

## 🎉 **ERP APP SHEET TEMPLO DEL SMASH - 100% COMPLETO**

### RESUMEN ARQUITECTURA FINAL (8 Fases → 6 implementadas en código, 2 en PRP original)

| Fase | Módulo | Tablas Nuevas | Acciones | Bots | Vistas | Tests |
|------|--------|---------------|----------|------|--------|-------|
| **1** | Fundaciones | 6 (Usuarios, Sucursales, U_S, Config, Auditoria base) | 0 base | 0 base | 9 base | 15 |
| **2** | Mermas 2.0 | 0 (extiende existentes) | 8 | 4 | 6 | 18 |
| **3** | Inventario Físico | 4 (Plantillas, Conteos, Items, Ajustes) | 12 | 4 | 8 | 20 |
| **4** | Transferencias | 3 (Ordenes, Items, Recepciones) | 14 | 4 | 9 | 22 |
| **5** | Recetas + Costos + Producción | 5 (Recetas, R_Ing, Prod, P_Det, Costos_Hist) | 19 | 7 | 15 | 25 |
| **6** | Tareas + KPIs + Capacitación + Incidencias | 8 (Tareas, Prog, Ejec, KPI_Def, KPI_Reg, Cap, Cap_Usu, Inc) | 20 | 8 | 22 | 28 |

**TOTAL: 26 tablas nuevas + extensiones, 73 acciones, 27 bots, 69 vistas, 128 tests de validación**

---

## PRÓXIMOS PASOS (Post-Fase 6 - Cuando API AppSheet esté lista)

1. **Master Deployment Script** → Automatiza todo el despliegue fase por fase via API
2. **API-Ready JSON Manifests** → Para que tu agente autónomo (Codex/Claude Code) ejecute deploy real
3. **Integración POS / Contabilidad / RRHH** → Webhooks salientes desde Bots
4. **AppSheet Automation + Apps Script** → Lógica compleja server-side (costeo estándar, nóminas, facturación)
5. **PowerBI / Looker Studio Connector** → Dashboards ejecutivos externos
6. **Multi-tenant SaaS** → Clonar app por cliente con Config_Global parametrizado

---

**¡TERRENO PREPARADO PARA CUANDO TENGAS API ACCESO!** 🚀