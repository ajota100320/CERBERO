# Checklist de Validación - Fase 5: Recetas + Costos + Producción

## PRE-REQUISITOS (Fase 1-4 completadas y validadas)
- [ ] Fase 1: Fundaciones (Multisucursal, Roles, Auditoría, Offline) → Deploy Staging OK
- [ ] Fase 2: Mermas 2.0 (Flujo completo, Stock, Notificaciones) → Deploy Staging OK
- [ ] Fase 3: Inventario Físico (Conteos, Ajustes, Tolerancias) → Deploy Staging OK
- [ ] Fase 4: Transferencias (Origen→Destino, Stock, Recepción) → Deploy Staging OK
- [ ] 6 usuarios de prueba funcionando en Staging
- [ ] Security Filters + User Roles + Offline Sync operativos en todas las tablas

---

## PASO 1: CREAR 5 TABLAS NUEVAS EN GOOGLE SHEETS (15 min)

### Hojas nuevas en `ERP_Fundaciones_Data`:

| Hoja | Columnas (cabeceras de CSVs) | Datos ejemplo |
|------|------------------------------|---------------|
| `Recetas` | `Receta_ID,Nombre,Categoria,Descripcion,Rendimiento_Porciones,Unidad_Rendimiento,Tiempo_Preparacion_Min,Tiempo_Coccion_Min,Dificultad,Version,Estado,Aprobada_Por,Fecha_Aprobacion,Costo_Total_Receta,Costo_Por_Porciona,Es_Activa,Sucursal_ID,Fecha_Creacion,Creado_Por,Sync_Pending?` | 3 filas del CSV |
| `Receta_Ingredientes` | `Receta_Ing_ID,Receta_ID,Ingrediente_ID,Cantidad,Unidad_Medida,Merma_Porcentaje,Costo_Unitario_Snapshot,Costo_Total_Linea,Es_Opcional,Orden,Fecha_Creacion,Creado_Por,Sync_Pending?` | 7 filas del CSV |
| `Produccion` | `Produccion_ID,Receta_ID,Sucursal_ID,Producida_Por,Fecha_Produccion,Cantidad_Producida,Unidad_Produccion,Lote,Estado,Observaciones,Costo_Teorico_Total,Costo_Real_Total,Variacion_Costo,Fecha_Creacion,Creado_Por,Sync_Pending?` | 2 filas del CSV |
| `Produccion_Detalle` | `Prod_Det_ID,Produccion_ID,Receta_Ing_ID,Ingrediente_ID,Cantidad_Teorica,Cantidad_Real,Unidad_Medida,Diferencia,Merma_Real_Porcentaje,Costo_Teorico_Linea,Costo_Real_Linea,Observacion,Fecha_Creacion,Creado_Por,Sync_Pending?` | 3 filas del CSV |
| `Costos_Historicos` | `Costo_ID,Entidad_Tipo,Entidad_ID,Sucursal_ID,Costo_Anterior,Costo_Nuevo,Variacion_Porcentaje,Variacion_Absoluta,Fuente_Cambio,Cambiado_Por,Fecha_Cambio,Aprobado_Por,Fecha_Aprobacion,Activo?,Fecha_Creacion,Creado_Por,Sync_Pending?` | 2 filas del CSV |

> **Tip:** Agrega columnas de auditoría estándar según `03_Columnas_Auditoria_Por_Tabla/Columnas_Recetas_Costos_Produccion.csv`

---

## PASO 2: VINCULAR 5 TABLAS EN APP SHEET STAGING (15 min)

**Data → Tables → + Table** × 5:

| Tabla | Source | Worksheet | Key | Row ID | Is Part Of? |
|-------|--------|-----------|-----|--------|-------------|
| `Recetas` | `ERP_Fundaciones_Data` | `Recetas` | `Receta_ID` | `Receta_ID` | No |
| `Receta_Ingredientes` | `ERP_Fundaciones_Data` | `Receta_Ingredientes` | `Receta_Ing_ID` | `Receta_Ing_ID` | **SÍ** → `Recetas` (Ref: `Receta_ID`) |
| `Produccion` | `ERP_Fundaciones_Data` | `Produccion` | `Produccion_ID` | `Produccion_ID` | No |
| `Produccion_Detalle` | `ERP_Fundaciones_Data` | `Produccion_Detalle` | `Prod_Det_ID` | `Prod_Det_ID` | **SÍ** → `Produccion` (Ref: `Produccion_ID`) |
| `Costos_Historicos` | `ERP_Fundaciones_Data` | `Costos_Historicos` | `Costo_ID` | `Costo_ID` | No |

> **Click "Regenerate Structure" después de las 5**

---

## PASO 3: CONFIGURAR COLUMNAS CRÍTICAS (30 min)

### Recetas:
- `Sucursal_ID` → Ref → Sucursales, **Initial Value**: `LOOKUP(USEREMAIL(), "Usuarios_Sucursales", "Email", "Sucursal_ID")`
- `Estado` → Enum: Borrador, En_Revision, Aprobada, Obsoleta
- **Valid_If Estado** (Máquina de estados): Ver Security Filters doc
- `Costo_Total_Receta` → App Formula: `SUM(FILTER("Receta_Ingredientes", [Receta_ID] = [_THISROW].[Receta_ID])[Costo_Total_Linea])`
- `Costo_Por_Porciona` → App Formula: `[Costo_Total_Receta] / [Rendimiento_Porciones]`
- `Es_Activa?` → Initial Value: TRUE
- `Version` → Initial Value: 1

### Receta_Ingredientes:
- `Receta_ID` → Ref → Recetas (Is Part Of = TRUE)
- `Ingrediente_ID` → Ref → Ingredientes_y_Stock
- `Unidad_Medida` → App Formula: `LOOKUP([Ingrediente_ID], "Ingredientes_y_Stock", "Ingrediente_ID", "Unidad_Base")`
- `Costo_Unitario_Snapshot` → Initial Value: `LOOKUP([Ingrediente_ID], "Ingredientes_y_Stock", "Ingrediente_ID", "Costo_Actual")`
- `Costo_Total_Linea` → App Formula: `[Cantidad] * [Costo_Unitario_Snapshot] * (1 + [Merma_Porcentaje]/100)`
- `Sucursal_ID` (auditoría) → App Formula: `LOOKUP([Receta_ID], "Recetas", "Receta_ID", "Sucursal_ID")`

### Produccion:
- `Receta_ID` → Ref → Recetas
- `Sucursal_ID` → App Formula: `LOOKUP([Receta_ID], "Recetas", "Receta_ID", "Sucursal_ID")`
- `Producida_Por` → Initial Value: `USEREMAIL()`
- `Fecha_Produccion` → Initial Value: `NOW()`
- `Estado` → Enum: En_Proceso, Completada, Cancelada, Con_Diferencias
- **Valid_If Estado**: Ver Security Filters doc
- `Lote` → Initial Value: `CONCATENATE("LOTE-", YEAR(NOW()), MONTH(NOW()), DAY(NOW()), "-", RANDBETWEEN(100,999))`
- `Costo_Teorico_Total` → App Formula: `[Cantidad_Producida] * LOOKUP([Receta_ID], "Recetas", "Receta_ID", "Costo_Por_Porciona")`
- `Variacion_Costo` → App Formula: `[Costo_Real_Total] - [Costo_Teorico_Total]`

### Produccion_Detalle:
- `Produccion_ID` → Ref → Produccion (Is Part Of = TRUE)
- `Receta_Ing_ID` → Ref → Receta_Ingredientes
- `Ingrediente_ID` → Ref → Ingredientes_y_Stock
- `Cantidad_Teorica` → App Formula: `LOOKUP([Receta_Ing_ID], "Receta_Ingredientes", "Receta_Ing_ID", "Cantidad") * ([Cantidad_Producida] / LOOKUP([Produccion_ID], "Produccion", "Produccion_ID", "Cantidad_Producida"))`
- `Unidad_Medida` → App Formula: `LOOKUP([Ingrediente_ID], "Ingredientes_y_Stock", "Ingrediente_ID", "Unidad_Base")`
- `Diferencia` → App Formula: `[Cantidad_Real] - [Cantidad_Teorica]`
- `Merma_Real_Porcentaje` → App Formula: `IF([Cantidad_Teorica]<>0, ([Diferencia]/[Cantidad_Teorica])*100, 0)`
- `Costo_Teorico_Linea` → App Formula: `LOOKUP([Receta_Ing_ID], "Receta_Ingredientes", "Receta_Ing_ID", "Costo_Total_Linea") * ([Cantidad_Producida] / LOOKUP([Produccion_ID], "Produccion", "Produccion_ID", "Cantidad_Producida"))`
- `Costo_Real_Linea` → App Formula: `[Cantidad_Real] * LOOKUP([Ingrediente_ID], "Ingredientes_y_Stock", "Ingrediente_ID", "Costo_Actual")`
- `Sucursal_ID` (auditoría) → App Formula: `LOOKUP([Produccion_ID], "Produccion", "Produccion_ID", "Sucursal_ID")`

### Costos_Historicos:
- `Entidad_Tipo` → Enum: Ingrediente, Receta
- `Entidad_ID` → Text
- `Sucursal_ID` → Ref → Sucursales
- `Variacion_Porcentaje` → App Formula: `IF([Costo_Anterior]<>0, (([Costo_Nuevo]-[Costo_Anterior])/[Costo_Anterior])*100, 0)`
- `Variacion_Absoluta` → App Formula: `[Costo_Nuevo] - [Costo_Anterior]`
- `Fuente_Cambio` → Enum: Manual, Actualizacion_Proveedor, Recalculo_Ingredientes, Ajuste_Inventario, Produccion

---

## PASO 4: PEGAR 5 SECURITY FILTERS (5 min)

Desde `02_Security_Filters/Security_Filters_Recetas_Costos_Produccion.md`:

| Tabla | Expresión |
|-------|-----------|
| `Recetas` | `OR(USERROLE("Administrador"), AND([Es_Activa?] = TRUE, IN([Sucursal_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL()))))` |
| `Receta_Ingredientes` | `OR(USERROLE("Administrador"), IN([Receta_ID].[Sucursal_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL())))` |
| `Produccion` | `OR(USERROLE("Administrador"), IN([Sucursal_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL())))` |
| `Produccion_Detalle` | `OR(USERROLE("Administrador"), IN([Produccion_ID].[Sucursal_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL())))` |
| `Costos_Historicos` | `OR(USERROLE("Administrador"), IN([Sucursal_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL())))` |

---

## PASO 5: CREAR ACCIONES CLAVE (Behavior → Actions) (40 min)

| Acción | Tabla | Tipo | Qué hace | Show_If |
|--------|-------|------|----------|---------|
| `Receta_Crear_Borrador` | Recetas | App: go to view | Abre formulario nueva receta | Encargado/Admin |
| `Receta_Enviar_Revision` | Recetas | Data: set values | Estado=En_Revision | Estado=Borrador, Encargado propietario |
| `Receta_Aprobar` | Recetas | Data: set values | Estado=Aprobada, calcula costos, Aprobada_Por, Fecha_Aprobacion, Version+1 | Estado=En_Revision, **Solo Admin** |
| `Receta_Rechazar` | Recetas | Data: set values + Input | Estado=Borrador, requiere comentario | Estado=En_Revision, **Solo Admin** |
| `Receta_Clonar_Nueva_Version` | Recetas | Data: add row + RefAction | Clona receta aprobada → nueva versión Borrador | Estado=Aprobada, Encargado propietario/Admin |
| `Action_Clonar_Ingredientes_Receta` | Receta_Ingredientes | Data: add row (set) | Copia ingredientes a nueva versión | System action |
| `Receta_Agregar_Ingrediente` | Receta_Ingredientes | Data: add row | Agrega línea a receta en Borrador/En_Revision | Estado∈{Borrador,En_Revision}, Encargado propietario |
| `Produccion_Iniciar` | Recetas | App: go to view | Abre formulario iniciar producción | Estado=Aprobada, Activa, Operador/Encargado/Admin |
| `Produccion_Registrar` | Produccion | Data: add row + RefAction | Crea producción + líneas detalle desde receta | Operador/Encargado/Admin |
| `Action_Crear_Detalle_Produccion_Desde_Receta` | Produccion_Detalle | Data: add row (set) | Crea líneas detalle para cada ingrediente | System action |
| `Produccion_Registrar_Consumo_Real` | Produccion_Detalle | Data: set values | Operador ingresa Cantidad_Real + Observacion | Estado=En_Proceso, Operador/Encargado/Admin |
| `Produccion_Completar` | Produccion | Data: execute on set | Descuenta stock real + genera históricos + calcula variación | Estado=En_Proceso, Encargado propietario/Admin |
| `Action_Finalizar_Produccion` | Produccion_Detalle | Data: execute on set | Para cada ingrediente → aplica consumo | System action |
| `Action_Aplicar_Consumo_Real_Stock` | Ingredientes_y_Stock | Data: execute on set | Busca ingrediente en sucursal | System action |
| `Action_Descontar_Stock_Produccion` | Ingredientes_y_Stock | Data: set values | Stock_Actual = Stock_Actual - Cantidad_Real | System action (Admin) |
| `Produccion_Cancelar` | Produccion | Data: set values | Estado=Cancelada (NO descuenta stock) | Estado=En_Proceso, Encargado/Admin |
| `Costo_Actualizar_Ingrediente` | Ingredientes_y_Stock | Data: set values + Input + RefAction | Actualiza Costo_Actual → histórico + recalcula recetas | **Solo Admin** |
| `Action_Generar_Historico_Costo_Ingrediente` | Costos_Historicos | Data: add row | Crea registro histórico ingrediente | System action |

---

## PASO 6: IMPORTAR BOTS + TASKS (Automation → Import) (15 min)

1. **Automation → Bots → Import** → `05_Bots_Recetas_Costos_Produccion.json`
2. **Automation → Tasks → Import** → `06_Tasks_Bots_Recetas_Costos_Produccion.json`
3. Verifica 7 bots creados:
   - `Bot_Receta_Flujo_Estados` (trigger: cambio Estado Recetas)
   - `Bot_Produccion_Flujo` (trigger: cambio Estado Produccion)
   - `Bot_Produccion_Detalle_Completo` (trigger: Cantidad_Real en Detalle)
   - `Bot_Costo_Ingrediente_Cambio` (trigger: cambio Costo_Actual Ingredientes)
   - `Bot_Costo_Receta_Variacion_Diaria` (schedule: 08:00 diario)
   - `Bot_Produccion_Vencida_Sin_Completar` (schedule: 09:00 diario)
4. **Enable = ON** en todos

---

## PASO 7: IMPORTAR VISTAS (UX → Views → Import) (15 min)

`07_Views_Recetas_Costos_Produccion.json` → 15 vistas:
- Admin: Todas recetas, Todas producciones, Costos históricos, Dashboard costos global
- Encargado: Mis recetas, Mis producciones, Mis costos, Dashboard producción sucursal
- Operador: Recetas activas (solo ver), Iniciar producción, Registrar consumos reales
- Formularios: Nueva receta, Editar receta, Nueva producción

---

## PASO 8: CONFIG_GLOBAL NUEVAS CLAVES (5 min)

En hoja `Config_Global` agrega:

| Config_ID | Clave | Valor | Tipo | Descripcion | Editable_Por_Rol |
|-----------|-------|-------|------|-------------|------------------|
| CFG_015 | `UMBRAL_VARIACION_COSTO_CRITICA` | `10` | Number | % variación costo ingrediente para alerta crítica a Admin | Administrador |
| CFG_016 | `UMBRAL_MERMA_REAL_ALERTA` | `15` | Number | % merma real en producción para alerta | Administrador |
| CFG_017 | `HORAS_ALERTA_PRODUCCION_ESTANCADA` | `24` | Number | Horas sin completar antes de alerta | Administrador |
| CFG_018 | `RECALCULAR_COSTOS_RECETAS_AUTO` | `TRUE` | Yes/No | Recalcular costos recetas automáticamente al cambiar costo ingrediente | Administrador |

---

## PASO 9: REGENERATE + DEPLOY STAGING (5 min)

1. **Data → Tables → Regenerate Structure**
2. **App → Settings → Deployment → Deploy → Staging**
3. Abre Staging → Login 3 roles

---

## TESTS DE VALIDACIÓN FASE 5 (Mínimo 90 min con 5 usuarios: Admin, Encargado1, Encargado2, Operador1, Operador2)

### 🔴 TEST A: CICLO VIDA RECETA (Borrador → Aprobada → Producción)
| # | Acción | Usuario | Resultado Esperado |
|---|--------|---------|-------------------|
| A1 | Encargado 1 → "Nueva Receta" → Completa datos → Guarda | Encargado 1 | Receta creada, Estado=Borrador, Version=1, Sucursal_ID=Suc1, Costo_Por_Porciona=0 |
| A2 | Encargado 1 → "Agregar Ingrediente" × 5 items (carne, pan, queso, lechuga, tomate) | Encargado 1 | 5 líneas en Receta_Ingredientes, Costo_Unitario_Snapshot congelado, Costo_Total_Linea calculado |
| A3 | Encargado 1 → "Enviar a Revisión" | Encargado 1 | Estado=En_Revision, **Push a Admin** "Receta en revisión" |
| A4 | Admin → Ve receta En_Revision → "Aprobar" | Admin | Estado=Aprobada, Version=2, Costo_Total_Receta y Costo_Por_Porciona calculados, **Push a Encargado 1 "Aprobada"** |
| A5 | Operador 1A (Suc1) → Ve receta aprobada → "Iniciar Producción" → Cantidad=10 | Operador 1A | Producción creada Estado=En_Proceso, **5 líneas en Produccion_Detalle** con Cantidad_Teorica, Lote generado, **Push a Encargado 1 "Producción iniciada"** |
| A6 | Operador 1A → En cada línea detalle → Ingresa Cantidad_Real (algunas con diferencia) | Operador 1A | Cantidad_Real guardada, Diferencia y Merma_Real_Porcentaje calculados, Costo_Real_Linea = Cantidad_Real × Costo_Actual |
| A7 | Operador 1A → Cuando todas tienen Real → "Completar Producción" | Operador 1A | **Stock Ingredientes_y_Stock descuenta Cantidad_Real**, Costo_Real_Total sumado, Variacion_Costo calculado, Estado=Completada/Con_Diferencias, **Push a Encargado 1 "Completada"**, **Costos_Historicos generado si variación > umbral** |

### 🟡 TEST B: VERSIONADO RECETAS
| # | Escenario | Resultado Esperado |
|---|-----------|-------------------|
| B1 | Encargado 1 → Receta Aprobada → "Clonar Nueva Versión" | Nueva receta Version+1, Estado=Borrador, ingredientes copiados con Costo_Unitario_Snapshot **actualizado a costo actual** |
| B2 | Admin → Receta Aprobada → "Rechazar" (con comentario) | Estado=Borrador, Observaciones incluye "Rechazado por Admin: ...", **Push a Encargado "Devuelta a borrador"** |

### 🟢 TEST C: COSTOS + HISTÓRICO + ALERTAS
| # | Acción | Resultado |
|---|--------|-----------|
| C1 | Admin → Ingredientes_y_Stock → Carne → Costo_Actual: 120 → 140 (Fuente: Proveedor) | **Costos_Historicos** creado: Entidad=Ingrediente, Variación=16.7%, **Push a Admin "ALERTA COSTO CRÍTICO"** (si > 10%), **Recetas con carne recalculan Costo_Por_Porciona** |
| C2 | Job diario 08:00 → Task_Recalcular_Costos_Recetas_Diario | Todas las recetas Aprobadas/Activas recalculan costo desde ingredientes actuales |
| C3 | Job diario 08:00 → Task_Reporte_Variaciones_Costos_Diario | **Push a Admin** resumen variaciones > 2% últimas 24h |

### 🔴 TEST D: PRODUCCIÓN EDGE CASES
| # | Escenario | Resultado |
|---|-----------|-----------|
| D1 | Operador inicia producción pero NO registra todos los consumos reales | **No puede completar** (botón Completar no visible hasta que todas las líneas tengan Real > 0) |
| D2 | Producción en En_Proceso > 24h sin completar | **Job 09:00 → Push a Encargado/Admin "Producción estancada >24h"** |
| D3 | Operador cancela producción en En_Proceso | Estado=Cancelada, **NO descuenta stock**, líneas detalle quedan |
| D4 | Merma_Real_Porcentaje > umbral (ej. 20%) en alguna línea | Al completar → **Costos_Historicos generado para ingrediente con Fuente=Produccion**, alerta si configurada |
| D5 | Encargado 2 (Sucursal 2) intenta ver receta de Encargado 1 | **No ve** (Security Filter por Sucursal_ID) |

### 🟢 TEST E: INTEGRACIÓN FASE 2-4
| # | Acción | Resultado |
|---|--------|-----------|
| E1 | Producción descuenta stock → Ingrediente baja a Stock_Minimo | **Bot Mermas 2.0** dispara alerta stock crítico |
| E2 | Transferencia (Fase 4) recibe ingredientes → Stock sube | Recetas de esa sucursal recalculan costos en próximo job 08:00 |

### 🔴 TEST F: OFFLINE + SYNC
| # | Escenario | Resultado |
|---|-----------|-----------|
| F1 | Operador 1A registra consumos reales offline (modo avión) | Guarda local, Sync_Pending=TRUE en Produccion_Detalle |
| F2 | Operador 1A completa producción offline | Estado=Completada local, Sync_Pending=TRUE |
| F3 | WiFi ON → Sync manual | Stock descuenta, Costos_Historicos crea, notificaciones se envían |

---

## CRITERIOS ACEPTACIÓN FASE 5

| Criterio | Obligatorio |
|----------|-------------|
| Receta: Borrador → En_Revision → Aprobada (Solo Admin aprueba) | ✅ |
| Costos calculados automáticamente: Costo_Total_Receta, Costo_Por_Porciona | ✅ |
| Versionado: Clonar receta aprobada → nueva versión Borrador con costos actualizados | ✅ |
| Producción: En_Proceso → Completada (Operador registra Real, Encargado/Admin completa) | ✅ |
| Stock descuenta **Cantidad_Real** (no teórica) al completar producción | ✅ |
| Costos_Historicos auto-generado: cambio costo ingrediente + variación producción | ✅ |
| Alertas: Costo crítico > umbral → Push Admin | ✅ |
| Alertas: Producción estancada > 24h → Push Encargado/Admin | ✅ |
| Alertas: Detalle completo → Push Operador "Listo para completar" | ✅ |
| Seguridad: Encargado ve solo su sucursal, Admin ve todo | ✅ |
| Job diario 08:00 recalcula costos recetas + reporte variaciones | ✅ |
| Offline: Registro consumos/completar offline → Sync posterior OK | ✅ |
| Integración Fase 2: Stock bajo por producción → Alerta Mermas | ✅ |
| Regenerate Structure sin errores + Deploy Staging OK | ✅ |

---

## REGISTRO EJECUCIÓN FASE 5

| Fecha | Ejecutado Por | Tests A/B/C/D/E/F Pasados | Bloqueadores | Firmado |
|-------|---------------|---------------------------|--------------|---------|
| | | A: / 7 | | |
| | | B: / 2 | | |
| | | C: / 3 | | |
| | | D: / 5 | | |
| | | E: / 2 | | |
| | | F: / 3 | | |

---

## PRÓXIMO: FASE 6 - TAREAS + HORARIOS + KPIs + CAPACITACIÓN + INCIDENCIAS