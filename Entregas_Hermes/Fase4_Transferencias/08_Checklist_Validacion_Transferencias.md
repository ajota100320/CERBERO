# Checklist de Validación - Fase 4: Transferencias entre Sucursales

## PRE-REQUISITOS (Fase 1 + 2 + 3 completadas y validadas)
- [ ] Fase 1: Fundaciones (Multisucursal, Roles, Auditoría, Offline) → Deploy Staging OK
- [ ] Fase 2: Mermas 2.0 (Flujo completo, Stock, Notificaciones) → Deploy Staging OK
- [ ] Fase 3: Inventario Físico (Conteos, Ajustes, Tolerancias) → Deploy Staging OK
- [ ] 6 usuarios de prueba funcionando en Staging
- [ ] Security Filters + User Roles + Offline Sync operativos en todas las tablas

---

## PASO 1: CREAR 3 TABLAS NUEVAS EN GOOGLE SHEETS (10 min)

### Hojas nuevas en `ERP_Fundaciones_Data`:

| Hoja | Columnas (cabeceras de CSVs) | Datos ejemplo |
|------|------------------------------|---------------|
| `Ordenes_Transferencia` | `Orden_ID,Estado,Sucursal_Origen_ID,Sucursal_Destino_ID,Solicitada_Por,Fecha_Solicitud,Aprobada_Origen_Por,Fecha_Aprobacion_Origen,Aprobada_Destino_Por,Fecha_Aprobacion_Destino,Preparada_Por,Fecha_Preparacion,Despachada_Por,Fecha_Despacho,Recibida_Por,Fecha_Recepcion,Observaciones,Fecha_Creacion,Creado_Por,Sync_Pending?` | 2 filas del CSV |
| `Items_Transferencia` | `Item_ID,Orden_ID,Ingrediente_ID,Cantidad_Solicitada,Unidad_Medida,Cantidad_Preparada,Cantidad_Despachada,Cantidad_Recibida,Diferencia_Recepcion,Estado_Item,Observacion_Preparador,Observacion_Receptor,Fecha_Creacion,Creado_Por,Sync_Pending?` | 3 filas del CSV |
| `Recepciones_Transferencia` | `Recepcion_ID,Orden_ID,Item_ID,Ingrediente_ID,Cantidad_Recibida,Cantidad_Esperada,Diferencia,Estado_Recepcion,Recibida_Por,Fecha_Recepcion,Observaciones,Foto_Evidencia,Requiere_Ajuste?,Ajuste_Generado_ID,Fecha_Creacion,Creado_Por,Sync_Pending?` | 2 filas del CSV |

> **Tip:** Agrega columnas de auditoría estándar según `03_Columnas_Auditoria_Por_Tabla/Columnas_Transferencias.csv`

---

## PASO 2: VINCULAR 3 TABLAS EN APP SHEET STAGING (10 min)

**Data → Tables → + Table** × 3:

| Tabla | Source | Worksheet | Key | Row ID | Is Part Of? |
|-------|--------|-----------|-----|--------|-------------|
| `Ordenes_Transferencia` | `ERP_Fundaciones_Data` | `Ordenes_Transferencia` | `Orden_ID` | `Orden_ID` | No |
| `Items_Transferencia` | `ERP_Fundaciones_Data` | `Items_Transferencia` | `Item_ID` | `Item_ID` | **SÍ** → `Ordenes_Transferencia` (Ref: `Orden_ID`) |
| `Recepciones_Transferencia` | `ERP_Fundaciones_Data` | `Recepciones_Transferencia` | `Recepcion_ID` | `Recepcion_ID` | No |

> **Click "Regenerate Structure" después de las 3**

---

## PASO 3: CONFIGURAR COLUMNAS CRÍTICAS (15 min)

### Ordenes_Transferencia:
- `Sucursal_Origen_ID` → Ref → Sucursales, **Initial Value**: `LOOKUP(USEREMAIL(), "Usuarios_Sucursales", "Email", "Sucursal_ID")`, **Valid_If**: `IN([_THIS], SELECT(Sucursales[Sucursal_ID], [Activa?]=TRUE))`
- `Sucursal_Destino_ID` → Ref → Sucursales, **Valid_If**: `AND(IN([_THIS], SELECT(Sucursales[Sucursal_ID], [Activa?]=TRUE)), [_THIS] <> [Sucursal_Origen_ID])`
- `Estado` → Enum: Borrador, Solicitada, Aprobada_Origen, Aprobada_Destino, En_Preparacion, Despachada, En_Transito, Recibida_Completa, Recibida_Con_Diferencias, Cancelada
- **Valid_If Estado** (Máquina de estados): Ver `Security_Filters_Transferencias.md`
- `Solicitada_Por` → Initial Value: `USEREMAIL()`
- `Fecha_Solicitud` → Initial Value: `NOW()`
- `Sucursal_ID` (auditoría) → App Formula: `LOOKUP([Sucursal_Origen_ID], "Sucursales", "Sucursal_ID", "Sucursal_ID")`
- `Sync_Pending?` → Initial Value: TRUE

### Items_Transferencia:
- `Orden_ID` → Ref → Ordenes_Transferencia (Is Part Of = TRUE)
- `Ingrediente_ID` → Ref → Ingredientes_y_Stock
- `Unidad_Medida` → App Formula: `LOOKUP([Ingrediente_ID], "Ingredientes_y_Stock", "Ingrediente_ID", "Unidad_Base")`
- `Estado_Item` → Enum: Pendiente, Preparado, Despachado, Recibido, Con_Diferencias
- `Diferencia_Recepcion` → App Formula: `[Cantidad_Recibida] - [Cantidad_Despachada]`
- `Sucursal_ID` (auditoría) → App Formula: `LOOKUP([Orden_ID], "Ordenes_Transferencia", "Orden_ID", "Sucursal_Origen_ID")`

### Recepciones_Transferencia:
- `Orden_ID` → Ref → Ordenes_Transferencia
- `Item_ID` → Ref → Items_Transferencia
- `Ingrediente_ID` → Ref → Ingredientes_y_Stock
- `Cantidad_Esperada` → App Formula: `LOOKUP([Item_ID], "Items_Transferencia", "Item_ID", "Cantidad_Despachada")`
- `Diferencia` → App Formula: `[Cantidad_Recibida] - [Cantidad_Esperada]`
- `Estado_Recepcion` → Enum: Completa, Con_Diferencias, Parcial, Rechazada
- `Recibida_Por` → Initial Value: `USEREMAIL()`
- `Fecha_Recepcion` → Initial Value: `NOW()`
- `Sucursal_ID` (auditoría) → App Formula: `LOOKUP([Orden_ID], "Ordenes_Transferencia", "Orden_ID", "Sucursal_Destino_ID")`

---

## PASO 4: PEGAR 3 SECURITY FILTERS (5 min)

Desde `02_Security_Filters/Security_Filters_Transferencias.md`:

| Tabla | Expresión |
|-------|-----------|
| `Ordenes_Transferencia` | `OR(IN([Sucursal_Origen_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL())), IN([Sucursal_Destino_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL())), USERROLE("Administrador"))` |
| `Items_Transferencia` | `OR(IN([Orden_ID].[Sucursal_Origen_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL())), IN([Orden_ID].[Sucursal_Destino_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL())), USERROLE("Administrador"))` |
| `Recepciones_Transferencia` | `OR(IN([Orden_ID].[Sucursal_Destino_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL())), USERROLE("Administrador"))` |

---

## PASO 5: CREAR ACCIONES CLAVE (Behavior → Actions) (25 min)

| Acción | Tabla | Tipo | Qué hace | Show_If |
|--------|-------|------|----------|---------|
| `Transferencia_Crear_Solicitud` | Sucursales | App: go to view | Abre formulario nueva orden | Encargado/Admin de la sucursal |
| `Transferencia_Solicitar` | Ordenes_Transferencia | Data: set values | Estado=Solicitada, Solicitada_Por=USEREMAIL(), Fecha_Solicitud=NOW() | Estado=Borrador, Encargado origen |
| `Transferencia_Agregar_Item` | Items_Transferencia | Data: add row | Agrega ingrediente a orden | Estado Borrador/Solicitada, Encargado origen |
| `Transferencia_Aprobar_Origen` | Ordenes_Transferencia | Data: set values | Estado=Aprobada_Origen, Aprobada_Origen_Por, Fecha_Aprobacion_Origen | Estado=Solicitada, Encargado origen |
| `Transferencia_Aprobar_Destino` | Ordenes_Transferencia | Data: set values | Estado=Aprobada_Destino, Aprobada_Destino_Por, Fecha_Aprobacion_Destino | Estado=Aprobada_Origen, Encargado destino |
| `Transferencia_Iniciar_Preparacion` | Ordenes_Transferencia | Data: set values | Estado=En_Preparacion, Preparada_Por, Fecha_Preparacion | Estado=Aprobada_Destino, Encargado origen |
| `Item_Preparar` | Items_Transferencia | Data: set values | Cantidad_Preparada, Estado_Item=Preparado | Estado=En_Preparacion, Operador/Encargado/Admin |
| `Transferencia_Despachar` | Ordenes_Transferencia | Data: set values + ReferencedAction | Estado=Despachada, Despachada_Por, Fecha_Despacho + **Descuenta stock origen** | Estado=En_Preparacion, Encargado origen |
| `Action_Descontar_Stock_Transferencia_Origen` | Ingredientes_y_Stock | Data: execute action on set of rows | Para cada item → Stock_Actual = Stock_Actual - Cantidad_Despachada | System action (Admin) |
| `Transferencia_Marcar_En_Transito` | Ordenes_Transferencia | Data: set values | Estado=En_Transito | Estado=Despachada, Admin |
| `Recepcion_Registrar` | Recepciones_Transferencia | Data: add row | Registra recepción física con Cantidad_Recibida | Estado Despachada/En_Transito, Operador/Encargado destino |
| `Transferencia_Completar_Recepcion` | Ordenes_Transferencia | Data: set values + ReferencedAction | Estado final (Completa/Con_Diferencias) + **Suma stock destino** | Estado Despachada/En_Transito, Encargado destino |
| `Action_Aplicar_Stock_Transferencia_Destino` | Ingredientes_y_Stock | Data: execute action on set of rows | Para cada item → Stock_Actual = Stock_Actual + Cantidad_Recibida | System action (Admin) |
| `Transferencia_Cancelar` | Ordenes_Transferencia | Data: set values | Estado=Cancelada | Estados pre-despacho, Encargado origen/destino/Admin |
| `Transferencia_Generar_Ajuste_Diferencias` | Ordenes_Transferencia | Data: execute action on set of rows | Genera Ajustes_Inventario (Fase 3) para diferencias | Estado=Recibida_Con_Diferencias, Admin |

---

## PASO 6: IMPORTAR BOTS + TASKS (Automation → Import) (10 min)

1. **Automation → Bots → Import** → `05_Bots_Transferencias.json`
2. **Automation → Tasks → Import** → `06_Tasks_Bots_Transferencias.json`
3. Verifica bots creados:
   - `Bot_Transferencia_Flujo_Estados` (trigger: cada cambio de estado en Ordenes_Transferencia)
   - `Bot_Transferencia_Items_Preparados` (trigger: Items_Transferencia, todos preparados)
   - `Bot_Transferencia_Vencida_Sin_Accion` (schedule: daily 9:00, estancadas >24h)
   - `Bot_Recepcion_Diferencias_Criticas` (trigger: Recepciones, Con_Diferencias > umbral crítico)
4. **Enable = ON** en todos

---

## PASO 7: IMPORTAR VISTAS (UX → Views → Import) (10 min)

`07_Views_Transferencias.json` → 9 vistas:
- Encargado Origen: Mis transferencias salientes, Preparar items, Despachar
- Encargado Destino: Mis transferencias entrantes, Recepcionar, Revisar recepciones
- Operador: Preparar items (origen), Recepcionar (destino)
- Admin: Dashboard global con KPIs y charts

---

## PASO 8: CONFIG_GLOBAL NUEVAS CLAVES (5 min)

En hoja `Config_Global` agrega:

| Config_ID | Clave | Valor | Tipo | Descripcion | Editable_Por_Rol |
|-----------|-------|-------|------|-------------|------------------|
| CFG_013 | `UMBRAL_DIFERENCIA_TRANSFERENCIA_CRITICA` | `5` | Number | % diferencia en recepción para alertar Admin | Administrador |
| CFG_014 | `HORAS_ALERTA_TRANSFERENCIA_ESTANCADA` | `24` | Number | Horas sin avance antes de alerta estancada | Administrador |

---

## PASO 9: REGENERATE + DEPLOY STAGING (5 min)

1. **Data → Tables → Regenerate Structure**
2. **App → Settings → Deployment → Deploy → Staging**
3. Abre Staging → Login 3 roles

---

## TESTS DE VALIDACIÓN FASE 4 (Mínimo 60 min con 4 usuarios: Admin, Encargado1, Encargado2, Operador1, Operador2)

### 🔴 TEST A: FLUJO COMPLETO ORIGEN → DESTINO (Sucursal 1 → Sucursal 2)
| # | Acción | Usuario | Resultado Esperado |
|---|--------|---------|-------------------|
| A1 | Encargado 1 → "Nueva Transferencia" → Destino: Sucursal 2 → Agrega 2 items → "Solicitar" | Encargado 1 | Orden creada, Estado="Solicitada", **Push a Encargado 2** |
| A2 | Encargado 2 → Ve transferencia entrante → "Aprobar Destino" | Encargado 2 | Estado="Aprobada_Destino", **Push a Encargado 1** |
| A3 | Encargado 1 → "Iniciar Preparación" | Encargado 1 | Estado="En_Preparacion", **Push a Encargado 2** |
| A4 | Operador 1A (Sucursal 1) → Prepara items → Cantidad_Preparada | Operador 1A | Items Estado="Preparado", **Cuando todos preparados → Push a Encargado 1 "Listo para despachar"** |
| A5 | Encargado 1 → "Despachar" | Encargado 1 | Estado="Despachada", **Stock origen descuenta Cantidad_Despachada**, **Push a Encargado 2 "Despachada en camino"** |
| A6 | Operador 2A (Sucursal 2) → Recibe items → Cantidad_Recibida (uno completo, uno con diferencia) | Operador 2A | Recepciones creadas, Estado_Recepcion="Completa"/"Con_Diferencias" |
| A7 | Encargado 2 → "Completar Recepción" | Encargado 2 | Estado final="Recibida_Con_Diferencias", **Stock destino suma Cantidad_Recibida**, **Push a Encargado 1 "Recepción con diferencias"**, **Push a Admin si diferencia > umbral crítico** |

### 🟡 TEST B: CASOS EDGE
| # | Escenario | Resultado Esperado |
|---|-----------|-------------------|
| B1 | Encargado 1 intenta `Sucursal_Destino_ID = Sucursal_Origen_ID` | **Valid_If rechaza** (no puede transferir a sí misma) |
| B2 | Operador 1A intenta "Aprobar Destino" | **Botón invisible** (Show_If false) |
| B3 | Encargado 2 ve transferencia que no es de su sucursal | **No ve** (Security Filter) |
| B4 | Encargado 1 cancela transferencia en "Aprobada_Destino" | Estado="Cancelada", **NO descuenta stock** |
| B5 | Recepción con diferencia > umbral crítico (ej. 10%) | **Push inmediato a Admin** con alerta crítica |
| B6 | Transferencia en "Solicitada" > 24h sin acción | **Push diario a ambos Encargados** "Estancada +24h" |

### 🟢 TEST C: OFFLINE + SYNC
| # | Escenario | Resultado |
|---|-----------|-----------|
| C1 | Operador 1A prepara items offline (modo avión) | Guarda local, Sync_Pending=TRUE |
| C2 | Operador 2A recibe items offline | Guarda recepción local |
| C3 | WiFi ON → Sync manual | Stock origen/destino actualizados, notificaciones se envían |

### 🔴 TEST D: INTEGRACIÓN FASE 3 (AJUSTES INVENTARIO)
| # | Acción | Resultado |
|---|--------|-----------|
| D1 | Recepción con diferencias → Encargado 2 ve botón "Generar Ajuste" | Crea registros en `Ajustes_Inventario` (Fase 3) en destino |
| D2 | Ajuste aplicado → Stock destino actualizado + Merma auto si negativo | Integración Fase 3 + Fase 2 funciona |

---

## CRITERIOS ACEPTACIÓN FASE 4

| Criterio | Obligatorio |
|----------|-------------|
| Flujo completo: Solicitada → Aprobada_Origen → Aprobada_Destino → En_Preparacion → Despachada → Recibida | ✅ |
| Stock origen descuenta **solo al Despachar** (no antes) | ✅ |
| Stock destino suma **solo al Completar Recepción** | ✅ |
| Notificaciones Push en cada transición crítica (6+ notificaciones) | ✅ |
| Alerta estancada > 24h a ambos Encargados | ✅ |
| Alerta diferencia crítica > umbral a Admin | ✅ |
| Seguridad: Origen ve sus salientes, Destino ve sus entrantes, Admin ve todo | ✅ |
| Valid_If máquina de estados respeta orden de fases | ✅ |
| Integración Fase 3: Genera Ajustes_Inventario desde diferencias | ✅ |
| Offline: Preparar/Recibir offline → Sync posterior OK | ✅ |
| Regenerate Structure sin errores + Deploy Staging OK | ✅ |

---

## REGISTRO EJECUCIÓN FASE 4

| Fecha | Ejecutado Por | Tests A/B/C/D Pasados | Bloqueadores | Firmado |
|-------|---------------|------------------------|--------------|---------|
| | | A: / 7 | | |
| | | B: / 6 | | |
| | | C: / 3 | | |
| | | D: / 2 | | |

---

## PRÓXIMO: FASE 5 - RECETAS + COSTOS + PRODUCCIÓN