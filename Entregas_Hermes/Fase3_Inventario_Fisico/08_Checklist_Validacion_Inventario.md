# Checklist de Validación - Fase 3: Inventario Físico

## PRE-REQUISITOS (Fase 1 + 2 completadas y validadas)
- [ ] Fase 1: Fundaciones (Multisucursal, Roles, Auditoría, Offline) → Deploy Staging OK
- [ ] Fase 2: Mermas 2.0 (Flujo Borrador→Aprobada, Stock descuenta, Notificaciones, Dashboard) → Deploy Staging OK
- [ ] 6 usuarios de prueba funcionando en Staging
- [ ] Security Filters + User Roles + Offline Sync operativos en todas las tablas existentes

---

## PASO 1: CREAR 4 TABLAS NUEVAS EN GOOGLE SHEETS (15 min)

### Hojas nuevas en `ERP_Fundaciones_Data` (o tu Spreadsheet de datos):

| Hoja | Columnas (copia cabeceras de CSVs) | Datos ejemplo |
|------|-----------------------------------|---------------|
| `Plantillas_Inventario` | `Plantilla_ID,Nombre,Descripcion,Sucursal_ID,Tipo_Frecuencia,Categoria_Filtro,Activa?,Fecha_Creacion,Creado_Por` | 8 filas del CSV |
| `Conteos_Inventario` | `Conteo_ID,Plantilla_ID,Sucursal_ID,Iniciado_Por,Fecha_Inicio,Fecha_Fin,Estado,Observaciones,Fecha_Creacion,Creado_Por,Sync_Pending?` | 2 filas del CSV |
| `Items_Conteo` | `Item_ID,Conteo_ID,Ingrediente_ID,Stock_Teorico,Stock_Contado,Unidad_Medida,Diferencia,Porcentaje_Diferencia,Esta_Fuera_Tolerancia?,Tolerancia_Aplicada,Observacion_Contador,Fecha_Conteo,Contado_Por,Sync_Pending?` | 4 filas del CSV |
| `Ajustes_Inventario` | `Ajuste_ID,Conteo_ID,Item_ID,Ingrediente_ID,Sucursal_ID,Stock_Anterior,Stock_Nuevo,Diferencia_Ajuste,Tipo_Ajuste,Aprobado_Por,Fecha_Aprobacion,Estado,Genero_Merma_Auto?,Merma_ID_Generada,Fecha_Creacion,Creado_Por,Sync_Pending?` | 2 filas del CSV |

> **Tip:** Agrega columnas de auditoría estándar (ID, Created_At, Created_By, Updated_At, Updated_By, Deleted?, Sucursal_ID, Sync_Pending?) según `03_Columnas_Auditoria_Por_Tabla/Columnas_Inventario_Fisico.csv`

---

## PASO 2: VINCULAR 4 TABLAS EN APP SHEET STAGING (10 min)

**Data → Tables → + Table** × 4:

| Tabla | Source | Worksheet | Key | Row ID | Is Part Of? |
|-------|--------|-----------|-----|--------|-------------|
| `Plantillas_Inventario` | `ERP_Fundaciones_Data` | `Plantillas_Inventario` | `Plantilla_ID` | `Plantilla_ID` | No |
| `Conteos_Inventario` | `ERP_Fundaciones_Data` | `Conteos_Inventario` | `Conteo_ID` | `Conteo_ID` | No |
| `Items_Conteo` | `ERP_Fundaciones_Data` | `Items_Conteo` | `Item_ID` | `Item_ID` | **SÍ** → `Conteos_Inventario` (Ref: `Conteo_ID`) |
| `Ajustes_Inventario` | `ERP_Fundaciones_Data` | `Ajustes_Inventario` | `Ajuste_ID` | `Ajuste_ID` | No |

> **Click "Regenerate Structure" después de las 4**

---

## PASO 3: CONFIGURAR COLUMNAS CRÍTICAS (15 min)

### En cada tabla, verifica/ajusta:

**Plantillas_Inventario:**
- `Sucursal_ID` → Type: Ref → Sucursales, **Initial Value**: `LOOKUP(USEREMAIL(), "Usuarios_Sucursales", "Email", "Sucursal_ID")`, Show_If: FALSE
- `Activa?` → Initial Value: TRUE
- `Tipo_Frecuencia` → Enum: Diario, Semanal, Mensual, Eventual
- `Categoria_Filtro` → Enum: Todos, Criticos, Alto_Valor, Perecederos, Bebidas, Secos

**Conteos_Inventario:**
- `Plantilla_ID` → Ref → Plantillas_Inventario
- `Sucursal_ID` → Ref → Sucursales, **App Formula**: `LOOKUP([Plantilla_ID], "Plantillas_Inventario", "Plantilla_ID", "Sucursal_ID")`, Show_If: FALSE
- `Iniciado_Por` → Initial Value: `USEREMAIL()`
- `Fecha_Inicio` → Initial Value: `NOW()`
- `Estado` → Enum: Borrador, En_Progreso, Completado, Aprobado, Rechazado, Con_Diferencias, Anulado
- `Sync_Pending?` → Initial Value: TRUE

**Items_Conteo:**
- `Conteo_ID` → Ref → Conteos_Inventario (Is Part Of = TRUE)
- `Ingrediente_ID` → Ref → Ingredientes_y_Stock
- `Stock_Teorico` → App Formula: `LOOKUP([Ingrediente_ID], "Ingredientes_y_Stock", "Ingrediente_ID", "Stock_Actual")`, Show_If: FALSE
- `Stock_Contado` → Editable: TRUE, Valid_If: `>=0`
- `Diferencia` → App Formula: `[Stock_Contado] - [Stock_Teorico]`, Show_If: FALSE
- `Porcentaje_Diferencia` → App Formula: `IF([Stock_Teorico]<>0, ([Diferencia]/[Stock_Teorico])*100, 0)`, Show_If: FALSE
- `Esta_Fuera_Tolerancia?` → App Formula: `ABS([Porcentaje_Diferencia]) > LOOKUP("TOLERANCIA_INVENTARIO_DEFAULT", "Config_Global", "Clave", "Valor")`, Show_If: FALSE
- `Tolerancia_Aplicada` → App Formula: `LOOKUP("TOLERANCIA_INVENTARIO_DEFAULT", "Config_Global", "Clave", "Valor")`, Show_If: FALSE
- `Contado_Por` → Initial Value: `USEREMAIL()`
- `Fecha_Conteo` → Initial Value: `NOW()`
- `Sucursal_ID` → App Formula: `LOOKUP([Conteo_ID], "Conteos_Inventario", "Conteo_ID", "Sucursal_ID")`, Show_If: FALSE

**Ajustes_Inventario:**
- `Conteo_ID` → Ref → Conteos_Inventario
- `Item_ID` → Ref → Items_Conteo
- `Ingrediente_ID` → Ref → Ingredientes_y_Stock
- `Sucursal_ID` → App Formula: `LOOKUP([Conteo_ID], "Conteos_Inventario", "Conteo_ID", "Sucursal_ID")`, Show_If: FALSE
- `Stock_Anterior` → App Formula: `LOOKUP([Ingrediente_ID], "Ingredientes_y_Stock", "Ingrediente_ID", "Stock_Actual")`, Show_If: FALSE
- `Diferencia_Ajuste` → App Formula: `[Stock_Nuevo] - [Stock_Anterior]`, Show_If: FALSE
- `Tipo_Ajuste` → Enum: Merma_Automatica, Ajuste_Positivo, Ajuste_Negativo, Correccion_Manual
- `Estado` → Enum: Pendiente, Aprobado, Rechazado, Aplicado, Anulado
- `Genero_Merma_Auto?` → Initial Value: FALSE

---

## PASO 4: PEGAR 4 SECURITY FILTERS (5 min)

Desde `02_Security_Filters/Security_Filters_Inventario_Fisico.md`:

| Tabla | Expresión |
|-------|-----------|
| `Plantillas_Inventario` | `OR(USERROLE("Administrador"), IN([Sucursal_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL())))` |
| `Conteos_Inventario` | `IN([Sucursal_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL())))` |
| `Items_Conteo` | `IN([Conteo_ID].[Sucursal_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL())))` |
| `Ajustes_Inventario` | `IN([Conteo_ID].[Sucursal_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL())))` |

---

## PASO 5: CREAR ACCIONES CLAVE (Behavior → Actions) (20 min)

| Acción | Tabla | Tipo | Qué hace | Show_If |
|--------|-------|------|----------|---------|
| `Inventario_Iniciar_Conteo` | Plantillas_Inventario | App: go to another view | Abre formulario nuevo Conteo con Plantilla_ID prellenado | `OR(USERROLE("Administrador"), USERROLE("Encargado"))` |
| `Conteo_Comenzar` | Conteos_Inventario | Data: set values | Estado="En_Progreso", Fecha_Inicio=NOW(), Iniciado_Por=USEREMAIL() | `AND([Estado]="Borrador", OR(USERROLE("Administrador"), USERROLE("Encargado")))` |
| `Conteo_Completar` | Conteos_Inventario | Data: set values | Estado="Completado", Fecha_Fin=NOW() | `AND([Estado]="En_Progreso", OR(USERROLE("Administrador"), USERROLE("Encargado")))` |
| `Conteo_Aprobar` | Conteos_Inventario | Data: execute action on set of rows | Llama `Action_Generar_Ajustes_Aprobados` + Estado="Aprobado", Aprobado_Por=USEREMAIL(), Fecha_Aprobacion=NOW() | `AND(IN([Estado],LIST("Completado","Con_Diferencias")), OR(USERROLE("Administrador"), USERROLE("Encargado")))` |
| `Conteo_Rechazar` | Conteos_Inventario | Data: set values | Estado="Rechazado" | Same as Aprobar |
| `Conteo_Anular` | Conteos_Inventario | Data: set values | Estado="Anulado" | `USERROLE("Administrador")` |
| `Conteo_Registrar_Item` | Items_Conteo | Data: set values | Stock_Contado=valor, Fecha_Conteo=NOW(), Contado_Por=USEREMAIL(), Sync_Pending=TRUE | `AND([Conteo_ID].[Estado]="En_Progreso", USERROLE("Operador"))` |
| `Action_Generar_Ajustes_Aprobados` | Conteos_Inventario | Data: execute action on set of rows | Para cada Item con `Esta_Fuera_Tolerancia?=TRUE` → crea fila en Ajustes_Inventario | `USERROLE("Administrador")` (system action) |
| `Ajuste_Aplicar_Stock` | Ajustes_Inventario | Data: execute action on set of rows | Ejecuta `Action_Actualizar_Stock_Ingrediente` + Estado="Aplicado", Aprobado_Por=USEREMAIL(), Fecha_Aprobacion=NOW() + si `Genero_Merma_Auto?` llama `Merma_Auto_Desde_Ajuste` | `AND([Estado]="Aprobado", OR(USERROLE("Administrador"), USERROLE("Encargado")))` |
| `Action_Actualizar_Stock_Ingrediente` | Ingredientes_y_Stock | Data: set values | Stock_Actual = [Stock_Nuevo] (referenced from Ajuste) | `USERROLE("Administrador")` (system action) |
| `Merma_Auto_Desde_Ajuste` | Registro_de_Mermas_y_Vencimientos | Data: add row | Crea merma automática con datos del ajuste | `USERROLE("Administrador")` (system action) |

---

## PASO 6: IMPORTAR BOTS + TASKS (Automation → Import) (10 min)

1. **Automation → Bots → Import** → `05_Bots_Inventario.json`
2. **Automation → Tasks → Import** → `06_Tasks_Bots_Inventario.json`
3. Verifica bots creados:
   - `Bot_Inventario_Flujo_Conteo` (triggers: Conteo_Comenzar, Conteo_Completar, Conteo_Aprobar)
   - `Bot_Inventario_Alertas_Vencidos` (schedule: daily 8:00, Row Filter: Estado=Borrador, Fecha_Programada < TODAY())
   - `Bot_Item_Fuera_Tolerancia` (trigger: Items_Conteo, condition: Esta_Fuera_Tolerancia? TRUE y antes FALSE)
4. **Enable = ON** en todos

---

## PASO 7: IMPORTAR VISTAS (UX → Views → Import) (10 min)

`07_Views_Inventario.json` → 9 vistas:
- Encargado: Plantillas, Gestion Conteos, Items Revisión, Ajustes, Dashboard KPIs
- Operador: Conteos Asignados, Contar Items
- Admin: Plantillas Todas, Conteos Todas

---

## PASO 8: CONFIG_GLOBAL NUEVAS CLAVES (5 min)

En hoja `Config_Global` agrega:

| Config_ID | Clave | Valor | Tipo | Descripcion | Editable_Por_Rol |
|-----------|-------|-------|------|-------------|------------------|
| CFG_010 | `TOLERANCIA_INVENTARIO_DEFAULT` | `5` | Number | % tolerancia default para diferencias de inventario | Administrador |
| CFG_011 | `TOLERANCIA_INVENTARIO_CRITICOS` | `2` | Number | % tolerancia para ingredientes críticos | Administrador |
| CFG_012 | `TOLERANCIA_INVENTARIO_ALTO_VALOR` | `1` | Number | % tolerancia para ingredientes alto valor | Administrador |

---

## PASO 9: REGENERATE + DEPLOY STAGING (5 min)

1. **Data → Tables → Regenerate Structure**
2. **App → Settings → Deployment → Deploy → Staging**
3. Abre Staging → Login 3 roles

---

## TESTS DE VALIDACIÓN FASE 3 (Mínimo 45 min con 3 usuarios)

### 🔴 TEST A: ENCARGADO INICIA CONTEO → OPERADOR CUENTA
| # | Acción | Usuario | Resultado Esperado |
|---|--------|---------|-------------------|
| A1 | Login Encargado 1 → "Plantillas" → Click "Iniciar Conteo" en "Conteo Diario Apertura" | Encargado 1 | Crea Conteo_ID, Estado="Borrador", Sucursal_ID=Sucursal 1, **Push a Operadores Suc 1** |
| A2 | Encargado → Conteo → "Comenzar" | Encargado 1 | Estado="En_Progreso", Fecha_Inicio=NOW() |
| A3 | Login Operador 1A → "Mis Conteos Asignados" → Ve conteo En_Progreso | Operador 1A | Ve solo conteos de SU sucursal En_Progreso |
| A4 | Operador → Click conteo → Lista Items → Llena Stock_Contado (algunos dentro tolerancia, 1 fuera) | Operador 1A | Stock_Contado guardado, Diferencia/Porcentaje calculados, **Esta_Fuera_Tolerancia?=TRUE para el fuera**, **Push inmediato a Encargado** |
| A5 | Operador completa todos → Encargado ve "Completar" | Encargado 1 | Estado="Completado", Fecha_Fin=NOW() |

### 🟡 TEST B: ENCARGADO APRUEBA → AJUSTES AUTOMÁTICOS
| # | Acción | Usuario | Resultado Esperado |
|---|--------|---------|-------------------|
| B1 | Encargado → Conteo Completado → "Aprobar" | Encargado 1 | Estado="Aprobado", Aprobado_Por, Fecha_Aprobacion, **Genera Ajustes para items fuera tolerancia**, **Si diff negativo → Merma automática (Fase 2)**, **Push a Admin si crítico** |
| B2 | Encargado → Ajustes → Ve ajustes Pendiente → "Aplicar Stock" | Encargado 1 | Stock_Actual en Ingredientes_y_Stock se actualiza, Estado="Aplicado", **Si Merma_Automatica → Crea merma en Fase 2** |
| B3 | Verifica stock en Ingredientes_y_Stock | Encargado 1 | Stock coincide con Stock_Nuevo del ajuste |

### 🟢 TEST C: OPERADOR VE SOLO LO SUYO + OFFLINE
| # | Acción | Usuario | Resultado |
|---|--------|---------|-----------|
| C1 | Login Operador 2A (Sucursal 2) → No ve conteos Sucursal 1 | Operador 2A | Security Filter aísla completamente |
| C2 | Modo avión → Operador 1A cuenta item → Guarda | Operador 1A | Guarda offline, Sync_Pending=TRUE, Diferencia calculada local |
| C3 | WiFi ON → Sync → Encargado ve item contado | Operador 1A → Encargado 1 | Sync_Pending=FALSE, Encargado ve dato actualizado |

### 🔴 TEST D: SEGURIDAD NEGATIVA
| # | Ataque | Debe Fallar |
|---|--------|-------------|
| D1 | Operador intenta "Aprobar" conteo | Botón invisible |
| D2 | Encargado 1 ve/edita conteo Sucursal 2 | No ve (Security Filter) |
| D3 | Operador edita item de conteo "Aprobado" | Valid_If/Editable_If false |
| D4 | Usuario sin Usuarios_Sucursales accede | No ve nada |

---

## CRITERIOS ACEPTACIÓN FASE 3

| Criterio | Obligatorio |
|----------|-------------|
| Encargado crea conteo desde plantilla → Push a operadores | ✅ |
| Operador cuenta items → Diferencia/Porcentaje/Fuera_Tolerancia auto-calculados | ✅ |
| Push inmediato a Encargado si item fuera tolerancia | ✅ |
| Encargado aprueba → Genera ajustes automáticos solo items fuera tolerancia | ✅ |
| Ajuste "Aplicar Stock" → Actualiza Stock_Actual en Ingredientes_y_Stock | ✅ |
| Ajuste Merma_Automatica → Crea merma en Fase 2 (Registro_de_Mermas) | ✅ |
| Dashboard KPIs Encargado muestra métricas reales | ✅ |
| Seguridad: aislamiento total por sucursal + roles | ✅ |
| Offline: operador cuenta sin señal → sync posterior OK | ✅ |
| Regenerate Structure sin errores + Deploy Staging OK | ✅ |

---

## REGISTRO EJECUCIÓN FASE 3

| Fecha | Ejecutado Por | Tests A/B/C/D Pasados | Bloqueadores | Firmado |
|-------|---------------|------------------------|--------------|---------|
| | | A: / 5 | | |
| | | B: / 3 | | |
| | | C: / 3 | | |
| | | D: / 4 | | |

---

## PRÓXIMO: FASE 4 - TRANSFERENCIAS ENTRE SUCURSALES