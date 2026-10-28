# Checklist de Validación - Fase 2: Mermas 2.0

## PRE-REQUISITOS (Fase 1 completada y validada)
- [ ] Fase 1 deployada en Staging y pasando todos los tests (Admin, Encargado, Operador, Seguridad, Offline, Auditoría)
- [ ] 6 usuarios de prueba creados y funcionales
- [ ] Security Filters + User Roles + Offline Sync operativos

---

## PASO 1: EXTENDER TABLA `Registro_de_Mermas_y_Vencimientos` (15 min)

### En Google Sheets (hoja existente)
1. Abre la hoja `Registro_de_Mermas_y_Vencimientos`
2. Inserta **14 columnas nuevas** a la derecha de las existentes
3. Cabeceras (fila 1) + fórmulas fila 2 (arrastra hacia abajo 100+ filas):

| Columna | Cabecera | Tipo Sheets | Fórmula fila 2 | Notas |
|---------|----------|-------------|----------------|-------|
| A | `Estado_Merma` | Texto | `="Borrador"` | Enum en AppSheet |
| B | `Tipo_Merma` | Texto | `="Merma"` | Enum |
| C | `Cantidad` | Número | | Requerido >0 |
| D | `Unidad_Medida` | Texto | `=SI(A2="";"";BUSCARV(A2;Ingredientes_y_Stock!A:Z;COLUMNA(Unidad_Base);FALSO))` | Ref a ingrediente |
| E | `Costo_Unitario_Estimado` | Número | `=SI(A2="";"";BUSCARV(A2;Ingredientes_y_Stock!A:Z;COLUMNA(Costo_Actual);FALSO))` | Snapshot al crear |
| F | `Costo_Total_Estimado` | Número | `=SI(O(C2="";E2="");"";C2*E2)` | App Formula en AppSheet |
| G | `Motivo` | Texto largo | | Mín 10 chars |
| H | `Evidencia_Foto` | Texto (URL) | | AppSheet maneja imágenes |
| I | `Ubicacion_Especifica` | Texto | | Almacén/Nevera/Estación |
| J | `Turno` | Texto | `="Apertura"` | Enum |
| K | `Reportado_Por` | Texto | `=""` | AppSheet: USEREMAIL() |
| L | `Fecha_Hora_Evento` | FechaHora | `=AHORA()` | Cuándo ocurrió |
| M | `Enviado_A_Revision_En` | FechaHora | `=""` | Auto al cambiar a Pendiente |
| N | `Enviado_A_Revision_Por` | Texto | `=""` | Auto |
| O | `Aprobado_Por` | Texto | `=""` | Solo Encargado/Admin |
| P | `Fecha_Aprobacion` | FechaHora | `=""` | Auto al aprobar |
| Q | `Rechazado_Por` | Texto | `=""` | Solo Encargado/Admin |
| R | `Fecha_Rechazo` | FechaHora | `=""` | Auto |
| S | `Motivo_Rechazo` | Texto largo | `=""` | Requerido si Rechazada |
| T | `Correccion_Solicitada_Por` | Texto | `=""` | Solo Encargado/Admin |
| U | `Fecha_Correccion_Solicitada` | FechaHora | `=""` | Auto |
| V | `Anulada_Por` | Texto | `=""` | Solo Admin |
| W | `Fecha_Anulacion` | FechaHora | `=""` | Auto |
| X | `Motivo_Anulacion` | Texto largo | `=""` | Requerido si Anulada |

> **Nota:** En AppSheet configura cada columna con su `Initial Value` / `App Formula` / `Show_If` / `Valid_If` según `01_Columnas_Mermas_Extendidas.csv`

### En AppSheet
1. **Data → Tables → Registro_de_Mermas_y_Vencimientos** → **Regenerate Structure**
2. Verifica 14 columnas nuevas aparecen
3. Configura cada columna (tipo, Initial Value, App Formula, Show_If=FALSE para campos auto, Valid_If, Editable_If)

---

## PASO 2: CREAR ACCIONES (Behavior → Actions → + New Action) (20 min)

Importa o crea manualmente estas 6 acciones desde `02_Actions_Mermas.json`:

| Acción | Tipo | Tabla | Qué hace | Show_If |
|--------|------|-------|----------|---------|
| `Merma_Enviar_A_Revision` | Data: set column values | Mermas | Estado=Pendiente, Enviado_En=NOW(), Enviado_Por=USEREMAIL() | `AND([Estado_Merma]="Borrador", [Reportado_Por]=USEREMAIL())` |
| `Merma_Aprobar` | Data: execute action on set of rows | Mermas | Llama `Action_Descontar_Stock` + set Estado=Aprobada, Aprobado_Por, Fecha_Aprobacion | `OR(USERROLE("Administrador"), AND(USERROLE("Encargado"), [Sucursal_ID]=LOOKUP(USEREMAIL(),"Usuarios_Sucursales","Email","Sucursal_ID")))` |
| `Merma_Rechazar` | Data: set column values | Mermas | Estado=Rechazada, Rechazado_Por, Fecha_Rechazo, Motivo_Rechazo (requerido) | Same as Aprobar |
| `Merma_Solicitar_Correccion` | Data: set column values | Mermas | Estado=Correccion_Solicitada, Correccion_Por, Fecha_Correccion | Same as Aprobar |
| `Merma_Anular` | Data: set column values | Mermas | Estado=Anulada, Anulada_Por, Fecha_Anulacion, Motivo_Anulacion | `USERROLE("Administrador")` |
| `Action_Descontar_Stock_Ingrediente` | Data: set column values | Ingredientes_y_Stock | Stock_Actual = Stock_Actual - [Cantidad] (referenced from Merma) | `USERROLE("Administrador")` (system action) |

> **Tip:** En `Merma_Aprobar` → Referenced Action = `Action_Descontar_Stock_Ingrediente` con Row Filter: `FILTER("Ingredientes_y_Stock", AND([Ingrediente_ID]=[_THISROW].[Ingrediente_ID], [Sucursal_ID]=[_THISROW].[Sucursal_ID]))`

---

## PASO 3: IMPORTAR BOTS + TASKS (Automation → Bots → Import) (10 min)

1. **Automation → Bots → Import** → Selecciona `03_Bots_Mermas.json`
2. **Automation → Tasks → Import** → Selecciona `04_Tasks_Bots_Mermas.json`
3. Verifica que se crearon:
   - Bot: `Bot_Merma_Flujo_Aprobacion` (trigger: Merma_Aprobar, Merma_Rechazar, Merma_Solicitar_Correccion)
   - Bot: `Bot_Merma_Notificaciones_Pendientes` (schedule: cada 4h, Row Filter: Pendiente > 4h)
   - Bot: `Bot_Merma_Alerta_Stock_Critico` (trigger: Merma_Aprobar, condition: stock < punto reorden)
   - Bot: `Bot_Merma_Alerta_Monto_Alto` (trigger: Merma_Aprobar, condition: costo > umbral config)
4. En cada Bot → **Enable** = ON

---

## PASO 4: IMPORTAR VISTAS (UX → Views → Import) (10 min)

1. **UX → Views → Import** → Selecciona `05_Views_Mermas.json`
2. Verifica 6 vistas creadas:
   - `View_Mermas_Operador_Mis_Reportes` (Deck, solo Operador)
   - `View_Mermas_Operador_Nueva_Merma` (Form, solo Operador)
   - `View_Mermas_Encargado_Pendientes_Revision` (Table, solo Encargado, con botones Aprobar/Rechazar/Corrección)
   - `View_Mermas_Encargado_Todas_Su_Sucursal` (Deck, solo Encargado)
   - `View_Mermas_Admin_Todas_Sucursales` (Table, solo Admin, todos los botones)
   - `View_Mermas_Dashboard_KPIs_Encargado` (Dashboard, solo Encargado, 3 charts + 3 KPIs)

---

## PASO 5: CONFIGURAR CONFIG_GLOBAL (Nuevas claves) (5 min)

En hoja `Config_Global` agrega:

| Config_ID | Clave | Valor | Tipo | Descripcion | Editable_Por_Rol |
|-----------|-------|-------|------|-------------|------------------|
| CFG_007 | `UMBRAL_ALERTA_MERMA_COSTO` | `500` | Number | Umbral costo merma para alertar Admin (pesos) | Administrador |
| CFG_008 | `UMBRAL_STOCK_CRITICO_PORCENTAJE` | `0.2` | Number | % del punto reorden para alerta crítica (0.2 = 20%) | Administrador |
| CFG_009 | `HORAS_ALERTA_MERMA_PENDIENTE` | `4` | Number | Horas sin acción antes de recordatorio a Encargado | Administrador |

---

## PASO 6: REGENERATE STRUCTURE + DEPLOY STAGING (5 min)

1. **Data → Tables → Regenerate Structure**
2. **App → Settings → Deployment → Deploy → Staging**
3. Abre app Staging → Login como los 3 roles

---

## TESTS DE VALIDACIÓN FASE 2 (Mínimo 30 min con 3 usuarios)

### 🔴 TEST A: OPERADOR CREA MERMA FLUJO COMPLETO
| # | Acción | Usuario | Resultado Esperado |
|---|--------|---------|-------------------|
| A1 | Login → "Nueva Merma" → Llena formulario (ingrediente, tipo, cantidad, motivo, foto, turno) → Guardar | Operador 1A | Merma creada con Estado="Borrador", Sucursal_ID auto, Reportado_Por=su email, Sync_Pending=TRUE |
| A2 | Abre su merma → Botón "Enviar a revisión" → Confirmar | Operador 1A | Estado="Pendiente", Enviado_A_Revision_En=NOW(), Enviado_A_Revision_Por=su email, **Push a Encargado sucursal** |
| A3 | Modo avión → Edita merma en Borrador → Guarda | Operador 1A | Guarda offline, Sync_Pending=TRUE |
| A4 | WiFi ON → Sync manual | Operador 1A | Sync_Pending=FALSE, "✅ Sincronizado" |

### 🟡 TEST B: ENCARGADO APRUEBA/RECHAZA
| # | Acción | Usuario | Resultado Esperado |
|---|--------|---------|-------------------|
| B1 | Login → Ve vista "Pendientes de revisión" → Ve merma de Operador 1A | Encargado 1 | Ve merma con datos completos, foto, costo estimado |
| B2 | Click "Aprobar" → Confirmar | Encargado 1 | Estado="Aprobada", Aprobado_Por=su email, Fecha_Aprobacion=NOW(), **Stock del ingrediente descuenta cantidad**, **Push a Operador "Aprobada"**, **Si stock < punto reorden → Push Admin "Stock Crítico"**, **Si costo > umbral → Push Admin "Merma Alto Impacto"** |
| B3 | Crea otra merma Operador 1B → Encargado Click "Rechazar" → Escribe motivo → Confirmar | Encargado 1 | Estado="Rechazada", Rechazado_Por, Fecha_Rechazo, Motivo_Rechazo, **Push a Operador "Rechazada" con motivo** |
| B4 | Crea otra merma Operador 1A → Encargado Click "Solicitar corrección" → Escribe qué corregir | Encargado 1 | Estado="Correccion_Solicitada", Correccion_Solicitada_Por, Fecha_Correccion, **Push a Operador "Devuelta para corrección"** |
| B5 | Operador corrige → "Enviar a revisión" → Encargado "Aprobar" | Operador 1A → Encargado 1 | Flujo completo funciona tras corrección |

### 🔴 TEST C: ADMIN ANULA + VISIBILIDAD TOTAL
| # | Acción | Usuario | Resultado Esperado |
|---|--------|---------|-------------------|
| C1 | Login Admin → Ve TODAS las mermas de AMBAS sucursales | Admin | Ve mermas Sucursal 1 y 2, todos los estados |
| C2 | Click "Anular" en merma Aprobada → Escribe motivo | Admin | Estado="Anulada", Anulada_Por=Admin, Fecha_Anulacion, Motivo_Anulacion, **NO descuenta stock** (ya descontado al aprobar) |
| C3 | Ver Dashboard KPIs Encargado → Gráficas cargan | Encargado 1 | 3 charts + 3 KPIs muestran datos reales |

### 🟣 TEST D: SEGURIDAD NEGATIVA (CRÍTICO)
| # | Ataque | Usuario | Debe Fallar |
|---|--------|---------|-------------|
| D1 | Operador intenta "Aprobar" merma ajena | Operador 1A | Botón invisible (Show_If false) / Error permisos |
| D2 | Encargado Sucursal 1 intenta aprobar merma Sucursal 2 | Encargado 1 | No ve merma Sucursal 2 (Security Filter) |
| D3 | Operador edita merma ya "Aprobada" | Operador 1A | Valid_If / Editable_If false → No permite |
| D4 | Usuario sin fila en Usuarios_Sucursales abre app | intruso@test.com | No ve **ningún** registro en ninguna tabla |

### 🟠 TEST E: OFFLINE + SYNC MERMA
| # | Escenario | Resultado |
|---|-----------|-----------|
| E1 | Operador crea merma offline (modo avión) → Foto + datos → Guardar | Guarda local, ID=UNIQUEID(), Created_At=NOW(), Sync_Pending=TRUE |
| E2 | Operador edita merma propia Borrador offline → Guardar | Actualiza Updated_At, Sync_Pending=TRUE |
| E3 | WiFi ON → Sync manual → Ver en Encargado | Merma aparece en "Pendientes" del Encargado, Sync_Pending=FALSE |
| E4 | Encargado aprueba offline (modo avión) → Sync posterior | Al sync: stock descuenta, notificaciones se envían |

---

## CRITERIOS DE ACEPTACIÓN FASE 2 (Definition of Done)

| Criterio | Obligatorio |
|----------|-------------|
| Operador crea merma → Borrador → Pendiente → (Encargado) Aprobada/Rechazada/Corrección → Flujo completo | ✅ |
| Stock descuenta **solo al aprobar** (no al crear, no al rechazar) | ✅ |
| Notificaciones Push: Encargado (pendiente), Operador (rechazo/corrección), Admin (stock crítico, monto alto) | ✅ |
| Recordatorio 4h a Encargado de mermas pendientes | ✅ |
| Dashboard KPIs Encargado funcional (3 charts + 3 KPIs) | ✅ |
| Seguridad: Operador SOLO ve/sus mermas; Encargado SOLO su sucursal; Admin TODO | ✅ |
| Offline: Crear/Editar merma Borrador offline → Sync OK | ✅ |
| Auditoría: Created_At/By, Updated_At/By, Deleted?, Sync_Pending?, Sucursal_ID en cada merma | ✅ |
| Regenerate Structure sin errores + Deploy Staging exitoso | ✅ |

---

## REGISTRO DE EJECUCIÓN FASE 2

| Fecha | Ejecutado Por | Tests Pasados / Totales | Bloqueadores | Firmado |
|-------|---------------|-------------------------|--------------|---------|
| | | A: / 4 | | |
| | | B: / 5 | | |
| | | C: / 3 | | |
| | | D: / 4 | | |
| | | E: / 4 | | |

---

## PRÓXIMO: FASE 3 - INVENTARIO FÍSICO (Plantillas, Conteos, Items, Tolerancias, Aprobación)