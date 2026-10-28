# Checklist de Validación - Fundaciones (Fase 1)

## OBJETIVO
Verificar que la base multisucursal + roles + auditoría + offline funciona **antes** de construir módulos funcionales.

---

## PRE-REQUISITOS (Hecho antes de empezar)

- [ ] 6 CSVs subidos a Google Sheets (pestañas: Usuarios, Sucursales, Usuarios_Sucursales, Roles, Permisos, Config_Global)
- [ ] 6 tablas vinculadas en AppSheet Staging (`ERP_Gastronomico_PRUEBAS`) → **Data → Tables → Add Table**
- [ ] Columnas de auditoría agregadas a 8 tablas existentes (ver `Columnas_Auditoria_Tablas_Existentes.csv`)
- [ ] 12 Security Filters pegados (ver `Security_Filters_Todas_Tablas.md`)
- [ ] Config Offline & Sync aplicada (ver `Config_Offline_Sync.md`)
- [ ] **Regenerate Structure** ejecutado en **TODAS** las tablas
- [ ] **Security → Require Sign-In → User Roles** configurado con tabla `Usuarios` / `Usuarios_Sucursales`

---

## USUARIOS DE PRUEBA (Crear en hoja `Usuarios` + `Usuarios_Sucursales`)

| Email | Nombre | Rol_Principal | Sucursal | Rol_Sucursal | Activo? |
|-------|--------|---------------|----------|--------------|---------|
| `admin@test.com` | Admin Test | Administrador | Sucursal 1 | Administrador | TRUE |
| `encargado1@test.com` | Encargado Sucursal 1 | Encargado | Sucursal 1 | Encargado | TRUE |
| `encargado2@test.com` | Encargado Sucursal 2 | Encargado | Sucursal 2 | Encargado | TRUE |
| `operador1a@test.com` | Operador 1A | Operador | Sucursal 1 | Operador | TRUE |
| `operador1b@test.com` | Operador 1B | Operador | Sucursal 1 | Operador | TRUE |
| `operador2a@test.com` | Operador 2A | Operador | Sucursal 2 | Operador | TRUE |

> **Tip:** Usa cuentas reales de Google para probar login real. O modo "Test" en AppSheet con emails ficticios.

---

## TESTS POR ROL (Ejecutar en orden)

### 🔴 TEST A: ADMINISTRADOR (`admin@test.com`)

| # | Acción | Resultado Esperado | Pass/Fail | Notas |
|---|--------|-------------------|-----------|-------|
| A1 | Login → Abre app | Ve **Dashboard Admin** (vista custom) | | |
| A2 | Va a **Ingredientes_y_Stock** | Ve registros de **AMBAS** sucursales | | |
| A3 | Va a **Registro_de_Mermas** | Ve mermas de **AMBAS** sucursales | | |
| A4 | Crea nuevo ingrediente | `Sucursal_ID` = vacía (catálogo compartido) o permite elegir | | |
| A5 | Edita `Costo_Actual` de un ingrediente | Permite editar (Admin) | | |
| A6 | Va a **Usuarios_Sucursales** | Ve todas las filas, puede crear/editar | | |
| A7 | Va a **Config_Global** | Ve y puede editar todas las configs | | |
| A8 | Va a **Auditoria_Cambios** (si existe) | Ve todos los logs | | |
| A9 | Intenta ver vista "Dashboard_Encargado" | **NO la ve** (`Show_If = USERROLE("Encargado")`) | | |
| A10 | Intenta ver vista "Dashboard_Operador" | **NO la ve** | | |

---

### 🟡 TEST B: ENCARGADO SUCURSAL 1 (`encargado1@test.com`)

| # | Acción | Resultado Esperado | Pass/Fail | Notas |
|---|--------|-------------------|-----------|-------|
| B1 | Login → Abre app | Ve **Dashboard Encargado** (solo su sucursal) | | |
| B2 | Va a **Ingredientes_y_Stock** | Ve **SOLO** ingredientes con `Sucursal_ID = Sucursal 1` | | |
| B3 | Va a **Registro_de_Mermas** | Ve **SOLO** mermas de Sucursal 1 | | |
| B4 | Crea nueva merma → Estado "Borrador" | `Sucursal_ID` = Sucursal 1 (auto), `Created_By` = su email | | |
| B5 | Cambia merma propia a "Pendiente" | Botón visible, funciona | | |
| B6 | Ve merma de **otro operador** (Sucursal 1) | **SÍ la ve** (mismo sucursal) | | |
| B7 | Click botón "Aprobar" en merma ajena | **Botón visible** (Encargado aprueba cualquier merma de su sucursal) | | |
| B8 | Click botón "Aprobar" → merma pasa a "Aprobada" | Stock se descuenta (Bot existente) | | |
| B9 | Intenta ver mermas de **Sucursal 2** | **NO ve ninguna** (Security Filter) | | |
| B10 | Intenta editar `Costo_Actual` ingrediente | **NO permite** (`Valid_If` falla, solo Admin o propuesta aprobada) | | |
| B11 | Va a **Usuarios_Sucursales** | Ve **SOLO** filas de Sucursal 1 | | |
| B12 | Intenta crear usuario nuevo | **NO puede** (no tiene permiso Admin) | | |
| B13 | Va a **Conteos_Inventario** (cuando exista) | Ve solo conteos de Sucursal 1 | | |

---

### 🟢 TEST C: OPERADOR SUCURSAL 1 (`operador1a@test.com`)

| # | Acción | Resultado Esperado | Pass/Fail | Notas |
|---|--------|-------------------|-----------|-------|
| C1 | Login → Abre app | Ve **Dashboard Operador** ("Qué debo hacer ahora") | | |
| C2 | Va a **Registro_de_Mermas** | Ve **SOLO** sus propias mermas (`Created_By = USEREMAIL()`) | | |
| C3 | Crea nueva merma → "Borrador" → "Pendiente" | Funciona, `Sucursal_ID` auto = Sucursal 1 | | |
| C4 | Intenta editar merma **ya en "Pendiente"** | **NO permite** (solo Borrador editable por creador) | | |
| C5 | Intenta ver merma de `operador1b@test.com` | **NO la ve** (Security Filter + `Created_By`) | | |
| C6 | Va a **Lista_de_Verificacion_Diario** | Ve formulario, completa, firma | | |
| C7 | Completa checklist → Guardar | `ID=UNIQUEID()`, `Created_At=NOW()`, `Sync_Pending?=TRUE` | | |
| C8 | Modo avión → Completa otro checklist | Guarda offline, muestra "⏳ Pendiente" | | |
| C9 | Desactiva modo avión → Sync manual | "✅ Sincronizado", `Sync_Pending?=FALSE` | | |
| C10 | Va a **Ingredientes_y_Stock** | Ve stock (lectura) de Sucursal 1 | | |
| C11 | Intenta editar stock directo | **NO permite** (columna no editable / no hay acción) | | |
| C12 | Intenta acceder a vista "Config_Global" | **NO la ve** (`Show_If = USERROLE("Administrador")`) | | |
| C13 | Intenta acceder a "Usuarios_Sucursales" | **NO la ve** | | |

---

### 🔵 TEST D: OPERADOR SUCURSAL 2 (`operador2a@test.com`)

| # | Acción | Resultado Esperado | Pass/Fail | Notas |
|---|--------|-------------------|-----------|-------|
| D1 | Login → Abre app | Ve Dashboard Operador (Sucursal 2) | | |
| D2 | Va a **Ingredientes_y_Stock** | Ve **SOLO** stock de Sucursal 2 | | |
| D3 | Crea merma | `Sucursal_ID` = Sucursal 2 (auto) | | |
| D4 | **NO ve** nada de Sucursal 1 | Security Filter aisla completamente | | |

---

### 🟣 TEST E: PRUEBAS DE SEGURIDAD NEGATIVAS (Críticas)

| # | Ataque | Cómo Probar | Debe Fallar (Pass = Falló el ataque) | Pass/Fail |
|---|--------|-------------|--------------------------------------|-----------|
| E1 | Operador ve datos otra sucursal | Login Operador 1A → URL directa a registro Sucursal 2 | 404 / Sin datos / Error permisos | |
| E2 | Encargado A aprueba merma Sucursal B | Login Encargado 1 → Botón Aprobar en merma Sucursal 2 | Botón invisible / Error | |
| E3 | Operador edita `Costo_Actual` | Login Operador → Formulario Ingrediente → Cambia costo | `Valid_If` rechaza / Columna no editable | |
| E4 | Usuario sin `Usuarios_Sucursales` accede | Login `intruso@test.com` (sin fila en tabla) → Abre app | **No ve ningún registro** en ninguna tabla | |
| E5 | Operador cambia `Sucursal_ID` en formulario | Login Operador → Nuevo registro → Intenta cambiar campo oculto | Campo `Show_If=FALSE` + `Initial Value` auto + `Editable_If=FALSE` | |
| E6 | Hard delete (borrado físico) | Cualquier rol → Intenta borrar fila de Sheets directamente | AppSheet ignora / Soft delete (`Deleted?=TRUE`) es la única vía | |
| E7 | Escalada de rol vía URL | Operador → URL de vista Admin (`/view/Dashboard_Admin`) | Vista oculta (`Show_If` false) → Redirige a su dashboard | |
| E8 | Auto-asignación Encargado | Operador → Edita su fila en `Usuarios_Sucursales` → Cambia `Rol_Sucursal` a "Encargado" | `Valid_If` / `Editable_If` / Security Filter impide | |

---

### 🟠 TEST F: OFFLINE & SYNC

| # | Escenario | Pasos | Resultado Esperado | Pass/Fail |
|---|-----------|-------|-------------------|-----------|
| F1 | Carga inicial WiFi | Abrir app → Cada vista → Ver datos | Todos los registros permitidos cargan | |
| F2 | Crear offline | Modo avión → Nueva merma + checklist + conteo | Guardan sin error, `Sync_Pending?=TRUE` | |
| F3 | Editar offline | Modo avión → Editar merma propia (Borrador) | Guarda, `Updated_At=NOW()`, `Sync_Pending?=TRUE` | |
| F4 | Sync manual | WiFi ON → Botón Sync → Esperar | "✅ Sincronizado", `Sync_Pending?=FALSE` | |
| F5 | Auto-sync | Hacer cambio → Esperar 35 min (intervalo 30) | Sync automático ocurrió | |
| F6 | Fotos offline | Modo avión → Merma → Tomar foto → Guardar | Foto en cola local, sube al sync | |
| F7 | Limpieza 30 días | (Opcional) Cambiar fecha dispositivo +31 días → Abrir | Cache local purgado, servidor intacto | |

---

### 🟤 TEST G: AUDITORÍA & TRAZABILIDAD

| # | Verificación | Cómo | Resultado | Pass/Fail |
|---|--------------|------|-----------|-----------|
| G1 | `Created_At` = captura dispositivo | Crear registro offline → Ver valor | `NOW()` del momento creación (no sync) | |
| G2 | `Created_By` = usuario real | Crear registro → Ver valor | `USEREMAIL()` exacto | |
| G3 | `Updated_At` cambia en edición | Editar registro → Sync → Ver valor | `NOW()` del momento sync | |
| G4 | `Updated_By` = editor | Editar registro → Sync → Ver valor | `USEREMAIL()` de quien editó | |
| G5 | `Deleted?` oculta registro | Admin → Soft delete (`Deleted?=TRUE`) → Login Operador | Operador NO ve el registro | |
| G6 | Admin ve registro borrado | Admin → Filtro "Mostrar borrados" (vista custom) | Admin SÍ ve registro con `Deleted?=TRUE` | |
| G7 | `Sucursal_ID` auto-asignado | Cualquier rol → Crear registro → Ver `Sucursal_ID` | = `LOOKUP(USEREMAIL(), Usuarios_Sucursales...)` | |
| G8 | `ID` = UNIQUEID() único | Crear 10 registros rápido offline → Ver IDs | Todos distintos, formato `xxxxxxxx-xxxx-xxxx` | |

---

## CRITERIOS DE ACEPTACIÓN FASE 1 (Definition of Done)

| Criterio | Obligatorio? |
|----------|--------------|
| **A1-A10** (Admin ve todo, gestiona todo) | ✅ SÍ |
| **B1-B13** (Encargado ve/gestiona SOLO su sucursal) | ✅ SÍ |
| **C1-C13** (Operador ve/hace SOLO lo suyo) | ✅ SÍ |
| **D1-D4** (Aislamiento total entre sucursales) | ✅ SÍ |
| **E1-E8** (TODOS los ataques fallan) | ✅ **CRÍTICO** |
| **F1-F5** (Offline crea/edita + Sync manual/auto) | ✅ SÍ |
| **G1-G8** (Auditoría completa en cada registro) | ✅ SÍ |
| **Security Filter** en **TODAS** las 14+ tablas | ✅ SÍ |
| **User Roles** configurado en Security → Require Sign-In | ✅ SÍ |
| **Regenerate Structure** sin errores | ✅ SÍ |
| **Deploy a Staging** exitoso | ✅ SÍ |

---

## REGISTRO DE EJECUCIÓN

| Fecha | Ejecutado Por | Rol Probado | Tests Pasados / Totales | Bloqueadores | Firmado |
|-------|---------------|-------------|-------------------------|--------------|---------|
| | | Admin | / 10 | | |
| | | Encargado 1 | / 13 | | |
| | | Operador 1A | / 13 | | |
| | | Operador 2A | / 4 | | |
| | | Seguridad Negativa | / 8 | | |
| | | Offline/Sync | / 5 | | |
| | | Auditoría | / 8 | | |

---

## PRÓXIMO PASO (Si todo ✅)

> **Fase 2: Mermas 2.0 + Inventario Físico**
> - Extender `Registro_de_Mermas_y_Vencimientos` con columnas de flujo
> - Crear `Plantillas_Inventario`, `Conteos_Inventario`, `Items_Conteo`
> - Bots de aprobación merma + alertas tolerancia
> - Tests de flujo completo Borrador → Aprobada → Stock baja