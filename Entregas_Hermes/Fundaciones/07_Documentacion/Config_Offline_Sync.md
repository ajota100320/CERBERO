# Configuración Offline & Sync - AppSheet

## DÓNDE PEGAR
**AppSheet Editor → App → Settings → Offline & Sync**

---

## CONFIGURACIÓN RECOMENDADA (Copiar valores exactos)

| Campo | Valor | Tipo | Por qué |
|-------|-------|------|---------|
| **Offline Caching** | `All rows` | Dropdown | Descarga TODOS los datos permitidos por Security Filter al dispositivo. Permite trabajo 100% offline. |
| **Auto Sync** | `ON` | Toggle | Sincroniza automáticamente cuando hay conexión. |
| **Auto Sync Interval (minutes)** | `30` | Number | Cada 30 min intenta sync. Balance entre batería y frescura de datos. |
| **Sync on Edit** | `ON` | Toggle | Intenta sync inmediato al crear/editar registro. |
| **Delay Sync on Edit (seconds)** | `30` | Number | Evita spam de syncs si el usuario edita varios campos rápido. |
| **Manual Sync Button** | `Visible` | Toggle | Usuario ve botón "Sync" en menú para forzar sincronización. |
| **Show Sync Status** | `Visible` | Toggle | Usuario ve indicador "Synced / Pending / Error" en header. |
| **Background Sync** | `ON` | Toggle | Sync en segundo plano sin bloquear UI. |
| **Max Offline Days** | `30` | Number | Coincide con `Config_Global[DIAS_HISTORIAL_OFFLINE]`. Limpia datos >30 días. |

---

## CONFIGURACIÓN POR TABLA (Data → Tables → [Tabla] → Table Settings)

| Tabla | Reset on Sync | Read Only | Por qué |
|-------|---------------|-----------|---------|
| **Todas las transaccionales** (Ingredientes, Compras, Mermas, Gastos, Checklists, Higiene, Temperaturas, Tareas, Conteos, Transferencias) | `OFF` | `FALSE` | **NUNCA** borrar datos locales al sincronizar. El usuario puede haber trabajado offline días. |
| **Catálogos maestros** (Sucursales, Usuarios, Roles, Permisos, Config_Global, Proveedores, Categorias, Unidades, Recetas) | `OFF` | `TRUE` (solo Admin/Encargado editan) | Catálogos cambian poco. `Read Only` evita ediciones accidentales. |
| **Tablas de sistema/historial** (Auditoria_Cambios, Historial_Costos, Logs) | `OFF` | `TRUE` | Solo lectura para todos. |

---

## COLUMNAS REQUERIDAS PARA OFFLINE-FIRST (Ya incluidas en Columnas_Auditoria.csv)

| Columna | Propósito | Fórmula clave |
|---------|-----------|---------------|
| `ID` (Key) | `UNIQUEID()` en **Initial Value** | Genera ID único **en el dispositivo** sin conexión. Nunca uses Row Number. |
| `Created_At` | `NOW()` en **Initial Value** | Timestamp de captura en dispositivo (≠ fecha sync). |
| `Sync_Pending?` | `TRUE` Initial / App Formula | Bandera visual: "⏳ Pendiente" / "✅ Sincronizado". |
| `Deleted?` | Soft delete | Nunca borras filas físicas; marcas `TRUE` y Security Filter las oculta. |

---

## FLUJO OFFLINE QUE ESTO HABILITA

```
1. Usuario abre app en celular (con WiFi) → Descarga TODOS sus datos (Security Filter)
2. Usuario va a cocina/cámara fría (SIN señal) → App funciona 100%:
   - Crea merma → ID=UNIQUEID(), Created_At=NOW(), Sync_Pending?=TRUE
   - Completa checklist → ID=UNIQUEID(), Created_At=NOW(), Sync_Pending?=TRUE
   - Hace conteo inventario → ID=UNIQUEID(), Created_At=NOW(), Sync_Pending?=TRUE
3. Usuario vuelve a zona con WiFi → Auto Sync (30s) O Botón Manual Sync
4. Server recibe registros → Bots procesan (stock, alertas, auditoría)
5. Sync_Pending? → FALSE → Usuario ve "✅ Sincronizado"
6. Conflictos (raro): AppSheet detecta same-key-different-data → Pide resolución manual
```

---

## TESTING OFFLINE (Checklist obligatorio antes de deploy)

| Test | Cómo hacerlo | Qué debe pasar |
|------|--------------|----------------|
| **1. Carga inicial** | Abrir app en WiFi → ir a cada vista → verificar datos cargan | Todos los registros permitidos por Security Filter visibles |
| **2. Modo avión** | Activar modo avión → abrir app → crear 1 merma, 1 checklist, 1 conteo | Formularios abren, guardan sin error, muestran "⏳ Pendiente" |
| **3. Edición offline** | En modo avión → editar registro existente → guardar | Guarda, `Updated_At=NOW()`, `Sync_Pending?=TRUE` |
| **4. Sync manual** | Desactivar modo avión → click botón Sync → esperar | "✅ Sincronizado" en todos los registros creados/editados offline |
| **5. Auto-sync** | Hacer cambio → esperar 30 min sin tocar → verificar | Sync automático ocurrió, `Sync_Pending?=FALSE` |
| **6. Conflicto** (opcional) | Mismo registro editado en 2 dispositivos offline → sync ambos | AppSheet muestra diálogo "Conflict detected - choose version" |
| **7. Limpieza 30 días** | Cambiar fecha dispositivo a +31 días → abrir app | Datos >30 días se purgan de cache local (no de servidor) |

---

## NOTAS IMPORTANTES

| Tema | Detalle |
|------|---------|
| **Fotos/Archivos offline** | Se guardan en cola local. Al sync, suben a Google Drive. Configura `Max Offline Days` según espacio en celular. |
| **Licencia** | `Offline Caching = All rows` requiere **AppSheet Core** o **Enterprise**. Plan "Starter" solo permite "Recent rows". |
| **Espacio en dispositivo** | ~50-200 MB por usuario típico (datos + fotos). Advertir a usuarios con celulares antiguos. |
| **Sync_Pendng? como columna virtual** | Si no quieres almacenarla, hazla **Virtual Column** con App Formula: `NOT(ISNOTBLANK([_SYNC_TIME]))` (AppSheet interno). Pero columna real es más controlable. |
| **Regenerate Structure** | Después de activar Offline Caching, **siempre** haz Regenerate Structure en Data → Tables. |