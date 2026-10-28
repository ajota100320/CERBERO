# Diccionario de Datos - Fundaciones ERP Templo del Smash

## CONVENCIONES DE NOMBRE

| Convención | Ejemplo | Regla |
|------------|---------|-------|
| **Tablas** | `PascalCase_SnakeCase` | `Ingredientes_y_Stock`, `Registro_de_Mermas_y_Vencimientos` |
| **Columnas (Claves)** | `Tabla_ID` | `Ingrediente_ID`, `Merma_ID`, `Usuario_ID` |
| **Columnas (Refs)** | `Tabla_Ref_ID` | `Sucursal_ID`, `Proveedor_ID`, `Ingrediente_ID` |
| **Columnas (Datos)** | `Nombre_Campo` | `Stock_Actual`, `Costo_Unitario`, `Fecha_Captura` |
| **Columnas (Sistema)** | `Prefijo_Campo` | `Created_At`, `Updated_By`, `Deleted?`, `Sync_Pending?` |
| **Enums** | `SCREAMING_SNAKE` | `ESTADO_MERMA: BORRADOR, PENDIENTE, APROBADA` |
| **Keys primarias** | `UNIQUEID()` | Nunca `ROWNUMBER` ni secuenciales |

---

## TABLAS NUEVAS (FUNDACIONES)

### 1. Usuarios
| Columna | Tipo | Key? | Ref? | Required? | Initial Value | App Formula | Descripción |
|---------|------|------|------|-----------|---------------|-------------|-------------|
| `ID` | Text | ✅ | ❌ | ✅ | `UNIQUEID()` | | Clave única |
| `Email` | Text | ❌ | ❌ | ✅ | | | **Login único** (case-sensitive) |
| `Nombre_Completo` | Text | ❌ | ❌ | ✅ | | | Nombre visible en app |
| `Rol_Principal` | Enum | ❌ | ❌ | ✅ | `"Operador"` | | `Administrador`, `Encargado`, `Operador` |
| `Activo?` | Yes/No | ❌ | ❌ | ✅ | `TRUE` | | Desactivar = no puede loguear |
| `Fecha_Creacion` | DateTime | ❌ | ❌ | ❌ | `NOW()` | | Auditoría |
| `Creado_Por` | Text | ❌ | ❌ | ❌ | `USEREMAIL()` | | Auditoría |
| `Sucursal_Default_ID` | Ref | ❌ | ✅ Sucursales | ❌ | | | Sucursal por defecto al crear registros |
| `Telefono` | Text | ❌ | ❌ | ❌ | | | Contacto |
| `Notas` | LongText | ❌ | ❌ | ❌ | | | Internas |

---

### 2. Sucursales
| Columna | Tipo | Key? | Ref? | Required? | Initial Value | App Formula | Descripción |
|---------|------|------|------|-----------|---------------|-------------|-------------|
| `Sucursal_ID` | Text | ✅ | ❌ | ✅ | `UNIQUEID()` | | Clave única |
| `Nombre` | Text | ❌ | ❌ | ✅ | | | "Sucursal 1", "Sucursal 2" |
| `Codigo` | Text | ❌ | ❌ | ✅ | | | Corto: "SUC001", "SUC002" |
| `Direccion` | LongText | ❌ | ❌ | ❌ | | | Dirección completa |
| `Telefono` | Text | ❌ | ❌ | ❌ | | | Teléfono local |
| `Encargado_Email` | Text | ❌ | ❌ | ❌ | | | Email del encargado principal |
| `Horario_Apertura` | Time | ❌ | ❌ | ❌ | `"08:00"` | | Para turnos/alertas |
| `Horario_Cierre` | Time | ❌ | ❌ | ❌ | `"23:00"` | | |
| `Zona_Horaria` | Text | ❌ | ❌ | ✅ | `"America/Mexico_City"` | | IANA timezone |
| `Activa?` | Yes/No | ❌ | ❌ | ✅ | `TRUE` | | Soft delete sucursal |
| `Fecha_Creacion` | DateTime | ❌ | ❌ | ❌ | `NOW()` | | |
| `Creado_Por` | Text | ❌ | ❌ | ❌ | `USEREMAIL()` | | |

---

### 3. Usuarios_Sucursales (Tabla de unión N:M + Rol por sucursal)
| Columna | Tipo | Key? | Ref? | Required? | Initial Value | App Formula | Descripción |
|---------|------|------|------|-----------|---------------|-------------|-------------|
| `ID` | Text | ✅ | ❌ | ✅ | `UNIQUEID()` | | Clave única |
| `Usuario_Email` | Text | ❌ | ✅ Usuarios[Email] | ✅ | | | Email exacto (case-sensitive) |
| `Sucursal_ID` | Ref | ❌ | ✅ Sucursales | ✅ | | | Sucursal asignada |
| `Rol_Sucursal` | Enum | ❌ | ❌ | ✅ | `"Operador"` | | `Administrador`, `Encargado`, `Operador` (puede variar por sucursal) |
| `Activo?` | Yes/No | ❌ | ❌ | ✅ | `TRUE` | | Desactivar asignación |
| `Fecha_Asignacion` | DateTime | ❌ | ❌ | ❌ | `NOW()` | | |
| `Asignado_Por` | Text | ❌ | ❌ | ❌ | `USEREMAIL()` | | Admin que asignó |
| `Notas` | LongText | ❌ | ❌ | ❌ | | | "Encargado turno noche", etc. |

> **CRÍTICO:** Esta tabla **alimenta los Security Filters**. Sin fila aquí → usuario no ve nada.

---

### 4. Roles (Catálogo de roles del sistema)
| Columna | Tipo | Key? | Ref? | Required? | Initial Value | Descripción |
|---------|------|------|------|-----------|---------------|-------------|
| `Rol_ID` | Text | ✅ | ❌ | ✅ | `ROL_ADMIN`, `ROL_ENCARGADO`, `ROL_OPERADOR` | Código fijo |
| `Nombre_Rol` | Text | ❌ | ❌ | ✅ | | "Administrador", "Encargado", "Operador" |
| `Descripcion` | LongText | ❌ | ❌ | ❌ | | Qué hace este rol |
| `Nivel_Jerarquia` | Number | ❌ | ❌ | ✅ | 100, 50, 10 | Para comparaciones `>` `<` |
| `Permite_Admin_Usuarios` | Yes/No | ❌ | ❌ | ✅ | TRUE/FALSE | Gestión de usuarios |
| `Permite_Config_Global` | Yes/No | ❌ | ❌ | ✅ | TRUE/FALSE | Editar Config_Global |
| `Permite_Aprobar_Mermas` | Yes/No | ❌ | ❌ | ✅ | TRUE/FALSE | Botón aprobar merma |
| `Permite_Aprobar_Costos` | Yes/No | ❌ | ❌ | ✅ | TRUE/FALSE | Aprobar cambios de costo |
| `Permite_Ver_Todas_Sucursales` | Yes/No | ❌ | ❌ | ✅ | TRUE/FALSE | Bypass Security Filter |
| `Activo?` | Yes/No | ❌ | ❌ | ✅ | `TRUE` | |

---

### 5. Permisos (Matriz granular tabla-acción-condición)
| Columna | Tipo | Key? | Ref? | Required? | Descripción |
|---------|------|------|------|-----------|-------------|
| `Permiso_ID` | Text | ✅ | ❌ | ✅ | `PERM_001`, `PERM_002`... |
| `Rol_ID` | Ref | ❌ | ✅ Roles | ✅ | Qué rol |
| `Tabla_Entidad` | Text | ❌ | ❌ | ✅ | Nombre tabla o `*` para todas |
| `Accion` | Enum | ❌ | ❌ | ✅ | `READ`, `WRITE`, `DELETE`, `APPROVE`, `*` |
| `Condicion_Expresion` | LongText | ❌ | ❌ | ✅ | Expresión AppSheet que evalúa a TRUE/FALSE |
| `Descripcion` | LongText | ❌ | ❌ | ❌ | Legible por humanos |
| `Activo?` | Yes/No | ❌ | ❌ | ✅ | `TRUE` |

> **Uso:** Referencia para documentar. AppSheet no lee esta tabla en runtime (usa Security Filter + USERROLE). Sirve para auditoría y `Show_If` dinámicos futuros.

---

### 6. Config_Global (Configuración centralizada key-value)
| Columna | Tipo | Key? | Ref? | Required? | Descripción |
|---------|------|------|------|-----------|-------------|
| `Config_ID` | Text | ✅ | ❌ | ✅ | `CFG_001`, `CFG_002`... |
| `Clave` | Text | ❌ | ❌ | ✅ | Nombre técnico: `TOLERANCIA_INVENTARIO_DEFAULT` |
| `Valor` | Text | ❌ | ❌ | ✅ | Valor como string (se castea en fórmulas) |
| `Tipo` | Enum | ❌ | ❌ | ✅ | `Text`, `Number`, `Yes/No`, `JSON`, `DateTime` |
| `Descripcion` | LongText | ❌ | ❌ | ❌ | Qué controla |
| `Editable_Por_Rol` | Enum | ❌ | ❌ | ✅ | `Administrador`, `Encargado`, `Operador` |
| `Fecha_Actualizacion` | DateTime | ❌ | ❌ | ❌ | `NOW()` App Formula |
| `Actualizado_Por` | Text | ❌ | ❌ | ❌ | `USEREMAIL()` App Formula |

> **Patrón de uso en fórmulas:** `LOOKUP("TOLERANCIA_INVENTARIO_DEFAULT", "Config_Global", "Clave", "Valor")`

---

## COLUMNAS DE AUDITORÍA (Agregar a TODAS las tablas transaccionales)

| Columna | Tipo | Key? | Required? | Initial Value | App Formula | Show_If | Descripción |
|---------|------|------|-----------|---------------|-------------|---------|-------------|
| `ID` | Text | ✅ | ✅ | `UNIQUEID()` | | `FALSE` | Clave única offline-first |
| `Created_At` | DateTime | ❌ | ✅ | `NOW()` | | `FALSE` | Captura en dispositivo |
| `Created_By` | Text | ❌ | ✅ | `USEREMAIL()` | | `FALSE` | Quién creó |
| `Updated_At` | DateTime | ❌ | ❌ | | `NOW()` | `FALSE` | Última modificación (sync) |
| `Updated_By` | Text | ❌ | ❌ | | `USEREMAIL()` | `FALSE` | Quién modificó |
| `Deleted?` | Yes/No | ❌ | ✅ | `FALSE` | | `FALSE` | Soft delete |
| `Sucursal_ID` | Ref | ❌ | ✅ | `LOOKUP(USEREMAIL(), "Usuarios_Sucursales", "Email", "Sucursal_ID")` | | `FALSE` | Aislamiento multisucursal |
| `Sync_Pending?` | Yes/No | ❌ | ❌ | `TRUE` | | `FALSE` | Bandera visual sync |

---

## EXPRESIONES REUTILIZABLES (Catálogo para copiar/pegar)

| Nombre | Expresión | Uso típico |
|--------|-----------|------------|
| `ES_ADMIN` | `USERROLE("Administrador")` | `Show_If`, `Valid_If`, `Editable_If` |
| `ES_ENCARGADO` | `USERROLE("Encargado")` | `Show_If` vistas/botones Encargado |
| `ES_OPERADOR` | `USERROLE("Operador")` | `Show_If` formularios simples |
| `MI_SUCURSAL` | `LOOKUP(USEREMAIL(), "Usuarios_Sucursales", "Email", "Sucursal_ID")` | `Initial Value` `Sucursal_ID`, `Show_If` |
| `SOLO_MIS_REGISTROS` | `USEREMAIL() = [Created_By]` | `Security Filter` operador, `Valid_If` edición |
| `ENCARGADO_MI_SUCURSAL` | `AND(USERROLE("Encargado"), [Sucursal_ID] = LOOKUP(USEREMAIL(), "Usuarios_Sucursales", "Email", "Sucursal_ID"))` | Botones aprobar, vistas encargados |
| `ADMIN_O_ENCARGADO_MI_SUCURSAL` | `OR(USERROLE("Administrador"), AND(USERROLE("Encargado"), [Sucursal_ID] = LOOKUP(USEREMAIL(), "Usuarios_Sucursales", "Email", "Sucursal_ID")))` | Acciones sensibles compartidas |
| `ESTADO_MERMA_VALIDO` | `IN([Estado_Merma], LIST("Borrador", "Pendiente", "En_Revision", "Aprobada", "Rechazada", "Correccion_Solicitada", "Anulada"))` | `Valid_If` columna `Estado_Merma` |
| `ESTADO_TRANSFERENCIA_VALIDO` | `IN([Estado], LIST("Borrador", "Solicitada", "Aprobada", "En_Preparacion", "Despachada", "Recibida_Con_Diferencias", "Recibida_Completa", "Cancelada"))` | `Valid_If` columna `Estado` transferencia |
| `TRANSICION_MERMA_VALIDA` | `SWITCH([_THISROW_BEFORE].[Estado_Merma], "Borrador", LIST("Pendiente", "Cancelada"), "Pendiente", LIST("En_Revision", "Aprobada", "Rechazada", "Correccion_Solicitada", "Cancelada"), "En_Revision", LIST("Aprobada", "Rechazada", "Correccion_Solicitada"), "Correccion_Solicitada", LIST("Pendiente", "Cancelada"), "Aprobada", LIST(), "Rechazada", LIST(), "Anulada", LIST(), LIST())` | `Valid_If` máquina de estados merma |
| `CONFIG_VALOR` | `LOOKUP([_THIS], "Config_Global", "Clave", "Valor")` | Leer config dinámica (ej. tolerancia) |

---

## RELACIONES CLAVE (Refs)

| Tabla Hija | Columna Ref | Tabla Padre | Tipo | Notas |
|------------|-------------|-------------|------|-------|
| `Usuarios_Sucursales` | `Usuario_Email` | `Usuarios` | N:1 | Email exacto |
| `Usuarios_Sucursales` | `Sucursal_ID` | `Sucursales` | N:1 | |
| `Ingredientes_y_Stock` | `Sucursal_ID` | `Sucursales` | N:1 | Security Filter |
| `Registro_de_Compras` | `Sucursal_ID` | `Sucursales` | N:1 | |
| `Detalle_de_Compras` | `Compra_ID` | `Registro_de_Compras` | N:1 | `Is Part Of = TRUE` |
| `Detalle_de_Compras` | `Ingrediente_ID` | `Ingredientes_y_Stock` | N:1 | |
| `Registro_de_Mermas_y_Vencimientos` | `Sucursal_ID` | `Sucursales` | N:1 | |
| `Registro_de_Mermas_y_Vencimientos` | `Ingrediente_ID` | `Ingredientes_y_Stock` | N:1 | |
| `Control_de_Gastos` | `Sucursal_ID` | `Sucursales` | N:1 | |
| `Lista_de_Verificacion_Diario` | `Sucursal_ID` | `Sucursales` | N:1 | |
| `Higiene_del_Personal` | `Sucursal_ID` | `Sucursales` | N:1 | |
| `Registro_Temperaturas` | `Sucursal_ID` | `Sucursales` | N:1 | |
| `Proveedores` | `Sucursal_ID` | `Sucursales` | N:1 | Catálogo compartido |

---

## SLICES RECOMENDADOS (Para vistas y bots)

| Slice Name | Tabla Base | Row Filter | Uso |
|------------|------------|------------|-----|
| `Mermas_Pendientes_Aprobacion` | `Registro_de_Mermas_y_Vencimientos` | `[Estado_Merma] = "Pendiente"` | Bot notificación Encargado |
| `Mermas_Aprobadas_Hoy` | `Registro_de_Mermas_y_Vencimientos` | `AND([Estado_Merma]="Aprobada", DATE([Fecha_Aprobacion])=TODAY())` | Reporte diario, descuento stock |
| `Conteos_Pendientes` | `Conteos_Inventario` | `[Estado] IN LIST("Pendiente", "En_Progreso")` | Vista Encargado, Bot alerta |
| `Tareas_Vencidas` | `Tareas` | `AND([Estado]="Pendiente", [Fecha_Limite] < NOW())` | Bot alerta crítica |
| `Tareas_Por_Vencer_1h` | `Tareas` | `AND([Estado]="Pendiente", [Fecha_Limite] <= NOW()+"01:00:00", [Fecha_Limite] > NOW())` | Bot alerta 1h |
| `Transferencias_En_Transito` | `Ordenes_Transferencia` | `[Estado] IN LIST("Despachada", "Recibida_Con_Diferencias")` | Seguimiento |
| `Auditoria_Critica_Hoy` | `Auditoria_Cambios` | `AND(DATE([Timestamp])=TODAY(), IN([Tabla], LIST("Ingredientes_y_Stock", "Config_Global", "Usuarios")))` | Alerta Admin |

---

## VERSIONADO DE ESTE DICCIONARIO

| Versión | Fecha | Autor | Cambios |
|---------|-------|-------|---------|
| 1.0 | 2025-01-XX | Hermes (Arquitecto) | Creación inicial: Fundaciones (Usuarios, Sucursales, Roles, Permisos, Config, Auditoría) |