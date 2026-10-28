# Instrucciones Paso a Paso - Despliegue Fundaciones en Staging

## RESUMEN: Qué vas a hacer en ~60 minutos

| Paso | Qué haces | Tiempo | Archivos usados |
|------|-----------|--------|-----------------|
| 1 | Subir 6 CSVs a Google Sheets | 10 min | `01_CSVs_Google_Sheets/*.csv` |
| 2 | Vincular 6 tablas nuevas en AppSheet Staging | 10 min | — |
| 3 | Agregar 64 columnas de auditoría a 8 tablas existentes | 25 min | `03_Columnas_Auditoria_Por_Tabla/Columnas_Auditoria_Tablas_Existentes.csv` |
| 4 | Pegar 12 Security Filters | 10 min | `02_Security_Filters/Security_Filters_Todas_Tablas.md` |
| 5 | Configurar Offline & Sync | 5 min | `07_Documentacion/Config_Offline_Sync.md` |
| 6 | Configurar User Roles (Security) | 5 min | `07_Documentacion/Matriz_Permisos.md` |
| 7 | Regenerate Structure + Deploy Staging | 5 min | — |
| 8 | Crear 6 usuarios de prueba en Sheets | 5 min | `07_Documentacion/Checklist_Validacion_Fundaciones.md` |
| 9 | Probar con checklist (3 usuarios mínimos) | 30+ min | `07_Documentacion/Checklist_Validacion_Fundaciones.md` |

**Total estimado: ~60-90 min la primera vez. Luego ~15 min para iteraciones.**

---

## PASO 1: SUBIR 6 CSVs A GOOGLE SHEETS

### Opción A: Un solo archivo Sheets con 6 pestañas (RECOMENDADO)

1. Abre **Google Drive** → **New → Google Sheets** → Nombra: `ERP_Fundaciones_Data`
2. En la hoja, crea 6 pestañas (botón `+` abajo): `Usuarios`, `Sucursales`, `Usuarios_Sucursales`, `Roles`, `Permisos`, `Config_Global`
3. Para **CADA pestaña**:
   - Click en celda A1 → **File → Import → Upload** → Selecciona el CSV correspondiente de `C:\Users\hola\Documents\Mi segundo Cerebro\Entregas_Hermes\Fundaciones\01_CSVs_Google_Sheets\`
   - **Import location:** `Replace current sheet`
   - **Separator type:** `Detect automatically`
   - Click **Import data**
4. Verifica: Cada pestaña tiene cabeceras en fila 1, 1-2 filas de ejemplo en fila 2+

### Opción B: 6 archivos Sheets separados (si prefieres)

1. Sube cada CSV como archivo independiente: `New → File upload` → Selecciona CSV → Se abre en Sheets automático
2. Renombra cada archivo: `ERP_Usuarios`, `ERP_Sucursales`, etc.
3. **Importante:** En AppSheet luego vincularás cada uno como tabla separada.

> **Tip:** Opción A es más fácil de mantener. Todas las tablas en un solo Spreadsheet = un solo `Regenerate Structure` para todo.

---

## PASO 2: VINCULAR 6 TABLAS NUEVAS EN APP SHEET STAGING

1. Abre **AppSheet Editor** → Tu app de **Staging**: `ERP_Gastronomico_PRUEBAS`
2. Menu lateral: **Data → Tables** → Click **"+ Table"** (botón azul arriba a la derecha)
3. Para **CADA una de las 6 tablas**:

| Tabla | Source | Worksheet/Range | Key Column | Row ID |
|-------|--------|-----------------|------------|--------|
| `Usuarios` | `ERP_Fundaciones_Data` | `Usuarios` | `ID` | `ID` |
| `Sucursales` | `ERP_Fundaciones_Data` | `Sucursales` | `Sucursal_ID` | `Sucursal_ID` |
| `Usuarios_Sucursales` | `ERP_Fundaciones_Data` | `Usuarios_Sucursales` | `ID` | `ID` |
| `Roles` | `ERP_Fundaciones_Data` | `Roles` | `Rol_ID` | `Rol_ID` |
| `Permisos` | `ERP_Fundaciones_Data` | `Permisos` | `Permiso_ID` | `Permiso_ID` |
| `Config_Global` | `ERP_Fundaciones_Data` | `Config_Global` | `Config_ID` | `Config_ID` |

4. Click **Save** después de cada una.
5. **IMPORTANTE:** Después de agregar las 6, click ** "Regenerate Structure" ** (botón naranja arriba a la derecha en Data → Tables). Espera a que termine.

---

## PASO 3: AGREGAR 64 COLUMNAS DE AUDITORÍA A 8 TABLAS EXISTENTES

> **Método rápido:** Usar el CSV `Columnas_Auditoria_Tablas_Existentes.csv` como guía para agregar columnas en **Google Sheets primero**, luego `Regenerate Structure` en AppSheet.

### 3.1 En Google Sheets (hojas existentes de tu app actual)

Para **CADA una de estas 8 hojas** en tu Spreadsheet de datos actual:
- `Ingredientes_y_Stock`
- `Registro_de_Compras`
- `Detalle_de_Compras`
- `Registro_de_Mermas_y_Vencimientos`
- `Control_de_Gastos`
- `Lista_de_Verificacion_Diario`
- `Higiene_del_Personal`
- `Registro_Temperaturas`
- `Proveedores`

**Haz esto:**
1. Abre la hoja correspondiente
2. Ve a la **última columna** con datos → Insertar **8 columnas nuevas** a la derecha
3. Copia las **cabeceras exactas** (fila 1) del CSV `Columnas_Auditoria_Tablas_Existentes.csv` para esa tabla:
   - `ID` | `Created_At` | `Created_By` | `Updated_At` | `Updated_By` | `Deleted?` | `Sucursal_ID` | `Sync_Pending?`
4. En **fila 2** (primera fila de datos), pega las **fórmulas Initial Value / App Formula** correspondientes:
   - `ID` → `=UNIQUEID()` (o deja vacío, AppSheet lo pone en Initial Value)
   - `Created_At` → `=NOW()`
   - `Created_By` → deja vacío (AppSheet Initial Value = `USEREMAIL()`)
   - `Updated_At` → deja vacío (AppSheet App Formula = `NOW()`)
   - `Updated_By` → deja vacío (AppSheet App Formula = `USEREMAIL()`)
   - `Deleted?` → `=FALSE`
   - `Sucursal_ID` → deja vacío (AppSheet Initial Value = `LOOKUP(USEREMAIL(), "Usuarios_Sucursales", "Email", "Sucursal_ID")`)
   - `Sync_Pending?` → `=TRUE`
5. **Arrastra hacia abajo** para cubrir todas las filas existentes (o al menos 100 filas)
6. Repite para las 8 tablas.

> **Alternativa en AppSheet (más lento pero sin tocar Sheets):**
> Data → Tables → [Tabla] → Columns → **+ Add Column** × 8 por tabla → pega nombre, tipo, Initial Value, App Formula, Show_If=FALSE. **64 clicks por tabla**. Hazlo en Sheets, es 10x más rápido.

### 3.2 En AppSheet: Regenerate Structure

1. Data → Tables → Click en cada una de las 8 tablas → Verifica que aparecen las 8 columnas nuevas
2. Si NO aparecen: **Regenerate Structure** (botón naranja)
3. Para cada columna nueva, ve a su configuración (click lápiz) y verifica/ajusta:
   - `ID` → Type: `Text`, Key: ✅, Initial Value: `UNIQUEID()`, Show_If: `FALSE`
   - `Created_At` → Type: `DateTime`, Initial Value: `NOW()`, Show_If: `FALSE`
   - `Created_By` → Type: `Text`, Initial Value: `USEREMAIL()`, Show_If: `FALSE`
   - `Updated_At` → Type: `DateTime`, **App Formula**: `NOW()`, Show_If: `FALSE`
   - `Updated_By` → Type: `Text`, **App Formula**: `USEREMAIL()`, Show_If: `FALSE`
   - `Deleted?` → Type: `Yes/No`, Initial Value: `FALSE`, Show_If: `FALSE`
   - `Sucursal_ID` → Type: `Ref` → `Sucursales`, Initial Value: `LOOKUP(USEREMAIL(), "Usuarios_Sucursales", "Email", "Sucursal_ID")`, Show_If: `FALSE`
   - `Sync_Pending?` → Type: `Yes/No`, Initial Value: `TRUE`, Show_If: `FALSE`

---

## PASO 4: PEGAR 12 SECURITY FILTERS

1. Abre `C:\Users\hola\Documents\Mi segundo Cerebro\Entregas_Hermes\Fundaciones\02_Security_Filters\Security_Filters_Todas_Tablas.md`
2. En AppSheet: **Data → Tables** → Click en **cada tabla** de la lista abajo → Pestaña **Security Filter** (icono escudo) → **Pega la expresión exacta** → **Save**

### Tablas EXISTENTES (8) - Security Filter estándar:
| Tabla | Expresión (copia del .md) |
|-------|---------------------------|
| `Ingredientes_y_Stock` | `IN([Sucursal_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL()))` |
| `Registro_de_Compras` | `IN([Sucursal_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL()))` |
| `Detalle_de_Compras` | `IN([Sucursal_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL()))` |
| `Registro_de_Mermas_y_Vencimientos` | `IN([Sucursal_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL()))` |
| `Control_de_Gastos` | `IN([Sucursal_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL()))` |
| `Lista_de_Verificacion_Diario` | `IN([Sucursal_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL()))` |
| `Higiene_del_Personal` | `IN([Sucursal_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL()))` |
| `Registro_Temperaturas` | `IN([Sucursal_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL()))` |

### Tablas CATÁLOGO COMPARTIDO (1) - Security Filter con Admin:
| Tabla | Expresión |
|-------|-----------|
| `Proveedores` | `OR(USERROLE("Administrador"), IN([Sucursal_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL())))` |

### Tablas NUEVAS (cuando las crees en Fase 2+) - Ya preparadas en el .md:
- `Tareas`, `Conteos_Inventario`, `Items_Conteo`, `Ordenes_Transferencia`, `Recetas` — **aplégalas luego**

> **Después de CADA Security Filter:** Click **Save** → AppSheet puede pedir **Regenerate Structure**. Hazlo al final de todos.

---

## PASO 5: CONFIGURAR OFFLINE & SYNC

1. AppSheet Editor → **App → Settings → Offline & Sync** (scroll abajo)
2. Copia **EXACTAMENTE** estos valores desde `Config_Offline_Sync.md`:

| Setting | Valor |
|---------|-------|
| Offline Caching | `All rows` |
| Auto Sync | `ON` |
| Auto Sync Interval (minutes) | `30` |
| Sync on Edit | `ON` |
| Delay Sync on Edit (seconds) | `30` |
| Manual Sync Button | `Visible` |
| Show Sync Status | `Visible` |
| Background Sync | `ON` |
| Max Offline Days | `30` |

3. Click **Save** (arriba a la derecha)

### 5.1 Config por tabla (Table Settings)
Para **CADA tabla transaccional** (las 8 existentes + 6 nuevas = 14):
- Data → Tables → [Tabla] → **Table Settings** (icono engranaje) →
  - `Reset on Sync` = `OFF` (crítico!)
  - `Read Only` = `FALSE` (salvo catálogos: `Sucursales`, `Usuarios`, `Roles`, `Permisos`, `Config_Global`, `Proveedores` → `TRUE` para no-Admin)

---

## PASO 6: CONFIGURAR USER ROLES (SECURITY)

1. AppSheet Editor → **Security → Require Sign-In** → **User Roles** (sección abajo)
2. Configura:

| Campo | Valor |
|-------|-------|
| **User Role Table** | `Usuarios_Sucursales` (o `Usuarios` si pones columna `Rol` ahí) |
| **User Role Email Column** | `Email` |
| **User Role Column** | `Rol_Sucursal` (o `Rol_Principal` en `Usuarios`) |
| **Default Role** | `Operador` |
| **Role Values** | `Administrador`, `Encargado`, `Operador` (exacto como en CSV) |

> **OJO:** La tabla fuente debe tener una fila por **usuario-sucursal-rol**. Usa `Usuarios_Sucursales` porque un usuario puede tener roles distintos en sucursales distintas (aunque en tu caso es 1:1).
> Si usas `Usuarios` como tabla de roles, agrega columna `Rol` (Enum: Administrador/Encargado/Operador) y `Sucursal_ID` (Ref).

3. Click **Save** → **Regenerate Structure**

---

## PASO 7: REGENERATE STRUCTURE + DEPLOY STAGING

1. **Data → Tables** → Botón naranja **"Regenerate Structure"** (arriba a la derecha) → Espera 30-60 seg
2. Verifica: **No errors** en rojo en ninguna tabla
3. **App → Settings → App Info** → **Deployment** → **Deploy** → **Staging** (tu app `ERP_Gastronomico_PRUEBAS`)
4. Espera "Deployment successful"
5. Click **Open App** → Se abre en navegador → **Login con `admin@test.com`** (o tu cuenta real)

---

## PASO 8: CREAR 6 USUARIOS DE PRUEBA EN SHEETS

Ve a tu hoja `ERP_Fundaciones_Data` → Pestaña `Usuarios_Sucursales` → Agrega estas 6 filas (copia/pega):

| ID | Usuario_Email | Sucursal_ID | Rol_Sucursal | Activo? | Fecha_Asignacion | Asignado_Por | Notas |
|----|---------------|-------------|--------------|---------|------------------|--------------|-------|
| `=UNIQUEID()` | `admin@test.com` | [Sucursal_ID de "Sucursal 1"] | `Administrador` | `TRUE` | `=NOW()` | `admin@test.com` | `Admin global` |
| `=UNIQUEID()` | `encargado1@test.com` | [Sucursal_ID de "Sucursal 1"] | `Encargado` | `TRUE` | `=NOW()` | `admin@test.com` | `Encargado Suc 1` |
| `=UNIQUEID()` | `encargado2@test.com` | [Sucursal_ID de "Sucursal 2"] | `Encargado` | `TRUE` | `=NOW()` | `admin@test.com` | `Encargado Suc 2` |
| `=UNIQUEID()` | `operador1a@test.com` | [Sucursal_ID de "Sucursal 1"] | `Operador` | `TRUE` | `=NOW()` | `admin@test.com` | `Operador Suc 1 A` |
| `=UNIQUEID()` | `operador1b@test.com` | [Sucursal_ID de "Sucursal 1"] | `Operador` | `TRUE` | `=NOW()` | `admin@test.com` | `Operador Suc 1 B` |
| `=UNIQUEID()` | `operador2a@test.com` | [Sucursal_ID de "Sucursal 2"] | `Operador` | `TRUE` | `=NOW()` | `admin@test.com` | `Operador Suc 2 A` |

> **Para obtener `Sucursal_ID`:** Ve a pestaña `Sucursales` → Copia el `Sucursal_ID` de "Sucursal 1" y "Sucursal 2" (son `UNIQUEID()` generados al importar). Pégalos en la columna `Sucursal_ID` arriba.

**También agrega en pestaña `Usuarios`:**
| ID | Email | Nombre_Completo | Rol_Principal | Activo? | Fecha_Creacion | Creado_Por | Sucursal_Default_ID |
|----|-------|-----------------|---------------|---------|----------------|------------|---------------------|
| `=UNIQUEID()` | `admin@test.com` | Admin Test | `Administrador` | `TRUE` | `=NOW()` | `admin@test.com` | [Sucursal_ID Suc 1] |
| `=UNIQUEID()` | `encargado1@test.com` | Encargado Sucursal 1 | `Encargado` | `TRUE` | `=NOW()` | `admin@test.com` | [Sucursal_ID Suc 1] |
| ... | ... | ... | ... | ... | ... | ... | ... |

---

## PASO 9: EJECUTAR CHECKLIST DE VALIDACIÓN

1. Abre `C:\Users\hola\Documents\Mi segundo Cerebro\Entregas_Hermes\Fundaciones\07_Documentacion\Checklist_Validacion_Fundaciones.md`
2. **Mínimo viable:** Haz **Test A (Admin)**, **Test B (Encargado 1)**, **Test C (Operador 1A)**, **Test E (Seguridad Negativa E1-E8)**
3. Marca Pass/Fail en el documento
4. **Si algo falla:** Ven al chat, dime el Test # y qué pasó → Te doy fix exacto
5. **Si todo Pass:** ¡Fase 1 lista! → Pasamos a **Fase 2: Mermas 2.0 + Inventario Físico**

---

## SOLUCIÓN RÁPIDA A ERRORES COMUNES

| Error | Causa | Fix |
|-------|-------|-----|
| "Column 'Sucursal_ID' not found" | Tabla no tiene la columna | Agregar en Sheets + Regenerate Structure |
| Usuario no ve nada | No tiene fila en `Usuarios_Sucursales` | Agregar fila con email exacto |
| Encargado ve sucursal ajena | Security Filter mal pegado / `Sucursal_ID` vacío en datos | Verificar Security Filter + poblar `Sucursal_ID` en datos existentes |
| `LOOKUP` devuelve vacío | Email no coincide (mayúsculas/minúsculas / espacios) | `TRIM(LOWER(USEREMAIL()))` vs `TRIM(LOWER([Email]))` en Sheets |
| Offline no guarda | `Offline Caching` = `Recent rows` o plan Starter | Cambiar a `All rows` + verificar licencia Core/Enterprise |
| Botón "Aprobar" no sale | `Show_If` usa `USERROLE()` pero User Roles no configurado | Paso 6 completo + Regenerate |
| Sync falla "Conflict" | Mismo `ID` editado en 2 dispositivos offline | AppSheet muestra diálogo → Elegir versión correcta |

---

## COMANDOS ÚTILES PARA TI (Terminal local)

```bash
# Ver estructura de entrega creada
tree "C:\Users\hola\Documents\Mi segundo Cerebro\Entregas_Hermes\Fundaciones"

# Abrir carpeta en Explorer
explorer "C:\Users\hola\Documents\Mi segundo Cerebro\Entregas_Hermes\Fundaciones"

# Ver checklist
code "C:\Users\hola\Documents\Mi segundo Cerebro\Entregas_Hermes\Fundaciones\07_Documentacion\Checklist_Validacion_Fundaciones.md"
```

---

## PRÓXIMO PAQUETE (Fase 2) - Cuando digas "FASE 2"

Te generaré:
- `Mermas_2.0_Columnas_Extendido.csv` (agregar a tabla existente)
- `Plantillas_Inventario.csv`, `Conteos_Inventario.csv`, `Items_Conteo.csv` (3 tablas nuevas)
- `Actions_Mermas_Flujo.json` (6 actions importables)
- `Bots_Mermas_Aprobacion.json` (1 bot stock + 3 notificaciones)
- `Views_Conteos_Inventario.json` (vistas Encargado/Operador)
- `Checklist_Validacion_Mermas_Inventario.md`

---

**¿Listo para empezar? Empieza por PASO 1. Avísame cuando termines PASO 7 (Deploy Staging) y te ayudo con usuarios de prueba y tests.**