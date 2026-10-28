# Matriz de Permisos - ERP Templo del Smash v1.0

## RESUMEN DE ROLES

| Rol | Nivel | Descripción | Usuarios Típicos |
|-----|-------|-------------|------------------|
| **Administrador** | 100 | Control total: usuarios, config global, costos, auditoría, todas las sucursales | Dueño, Gerente General, Admin TI |
| **Encargado** | 50 | Supervisión operativa de **SU** sucursal: aprueba mermas/inventarios, asigna tareas, gestiona turnos | Encargado de Sucursal 1, Encargado de Sucursal 2 |
| **Operador** | 10 | Ejecución: checklists, mermas, temperaturas, higiene, tareas asignadas, conteos | Cocineros, Ayudantes, Personal de limpieza, Recepcionistas |

---

## MATRIZ DETALLADA POR MÓDULO Y ACCIÓN

| Módulo / Tabla | Acción | Administrador | Encargado (su sucursal) | Operador (sus registros) | Notas |
|----------------|--------|---------------|-------------------------|--------------------------|-------|
| **Usuarios** | Crear/Editar/Desactivar | ✅ Total | ❌ | ❌ | Solo Admin |
| **Usuarios** | Ver lista | ✅ Todas | ✅ Solo su sucursal | ❌ | Encargado ve su equipo |
| **Sucursales** | Crear/Editar | ✅ | ❌ | ❌ | |
| **Roles / Permisos** | Gestionar | ✅ | ❌ | ❌ | |
| **Config_Global** | Editar | ✅ | ❌ | ❌ | |
| **Ingredientes_y_Stock** | Ver stock | ✅ Todas | ✅ Su sucursal | ✅ Su sucursal | Security Filter |
| **Ingredientes_y_Stock** | Editar stock manual | ✅ | ⚠️ Solo ajuste con auditoría | ❌ | Operador NO toca stock directo |
| **Ingredientes_y_Stock** | Editar costo | ✅ | ⚠️ Propone → Admin aprueba | ❌ | Flujo propuesta/aprobación |
| **Registro_de_Compras** | Crear (cabecera) | ✅ | ✅ Su sucursal | ❌ | Solo Encargado/Admin reciben mercancía |
| **Detalle_de_Compras** | Agregar ítems | ✅ | ✅ Su sucursal | ❌ | |
| **Registro_de_Mermas** | Crear reporte (Borrador) | ✅ | ✅ | ✅ Su sucursal | Operador reporta |
| **Registro_de_Mermas** | Enviar a revisión | ✅ | ✅ | ✅ Solo sus borradores | |
| **Registro_de_Mermas** | Aprobar/Rechazar/Corrección | ✅ Todas | ✅ Su sucursal | ❌ | Encargado decide |
| **Registro_de_Mermas** | Anular | ✅ | ❌ | ❌ | Solo Admin |
| **Control_de_Gastos** | Crear/Ver | ✅ Todas | ✅ Su sucursal | ❌ | Solo Admin/Encargado |
| **Lista_de_Verificacion_Diario** | Completar (Apertura/Cierre) | ✅ | ✅ | ✅ Su turno | Operador firma |
| **Lista_de_Verificacion_Diario** | Ver histórico | ✅ Todas | ✅ Su sucursal | ✅ Solo sus firmas | |
| **Higiene_del_Personal** | Registrar auditoría | ✅ | ✅ | ✅ Su propio registro | Auto-auditoría |
| **Higiene_del_Personal** | Ver todas | ✅ Todas | ✅ Su sucursal | ❌ | |
| **Registro_Temperaturas** | Registrar | ✅ | ✅ | ✅ Su turno | |
| **Registro_Temperaturas** | Ver alertas/histórico | ✅ Todas | ✅ Su sucursal | ✅ Solo sus registros | |
| **Proveedores** | CRUD | ✅ | ⚠️ Ver/Crear su sucursal | ❌ | Catálogo compartido |
| **Tareas** | Crear/Asignar | ✅ Todas | ✅ Su sucursal | ❌ | |
| **Tareas** | Completar/Ver asignadas | ✅ | ✅ | ✅ Solo asignadas a él | |
| **Plantillas_Planilla** | CRUD | ✅ | ✅ Su sucursal | ❌ | |
| **Ejecuciones_Planilla** | Completar asignadas | ✅ | ✅ | ✅ Solo asignadas | |
| **Plantillas_Inventario** | CRUD | ✅ | ✅ Su sucursal | ❌ | |
| **Conteos_Inventario** | Iniciar/Asignar | ✅ | ✅ Su sucursal | ❌ | |
| **Conteos_Inventario** | Completar (conteo físico) | ✅ | ✅ | ✅ Solo asignados | |
| **Conteos_Inventario** | Aprobar/Rechazar | ✅ | ✅ Su sucursal | ❌ | Encargado valida tolerancias |
| **Incidencias** | Crear/Ver | ✅ Todas | ✅ Su sucursal | ✅ Crea/Ve asignadas | |
| **Incidencias** | Asignar/Escalar/Cerrar | ✅ | ✅ Su sucursal | ❌ | |
| **Horarios/Turnos** | Crear borrador/Publicar | ✅ | ✅ Su sucursal | ❌ | |
| **Horarios/Turnos** | Ver propio horario | ✅ | ✅ | ✅ | |
| **Horas_Extras** | Registrar/Solicitar | ✅ | ✅ | ✅ Su registro | |
| **Horas_Extras** | Aprobar | ✅ | ✅ Su sucursal | ❌ | |
| **KPI / Evaluaciones** | Configurar/Ver todas | ✅ | ✅ Su sucursal | ❌ | |
| **KPI / Evaluaciones** | Ver propia evaluación | ✅ | ✅ | ✅ Solo la suya | |
| **Capacitación** | Crear/Asignar contenido | ✅ | ✅ Su sucursal | ❌ | |
| **Capacitación** | Completar lecciones | ✅ | ✅ | ✅ Solo asignadas | |
| **Recetas** | Ver (aprobadas) | ✅ | ✅ | ✅ | Todas las sucursales |
| **Recetas** | Crear/Editar costos | ✅ | ⚠️ Propone → Admin aprueba | ❌ | |
| **Recetas** | Aprobar cambios costo | ✅ | ❌ | ❌ | Solo Admin |
| **Producción** | Planificar/Registrar | ✅ | ✅ Su sucursal | ✅ Su turno | |
| **Transferencias** | Crear/Solicitar | ✅ | ✅ Origen/Destino su sucursal | ❌ | |
| **Transferencias** | Preparar/Despachar/Recibir | ✅ | ✅ Su sucursal (origen/destino) | ✅ Si asignado | |
| **Transferencias** | Aprobar/Cancelar | ✅ | ✅ Su sucursal | ❌ | |
| **Auditoria_Cambios** | Ver | ✅ Todas | ✅ Su sucursal | ❌ | |
| **Reportes / Dashboards** | Ver consolidado | ✅ | ✅ Su sucursal | ❌ | Operador ve solo "Mi panel" |

---

## LEGENDA

| Símbolo | Significado |
|---------|-------------|
| ✅ | Acceso total (crear, leer, editar, borrar lógico según módulo) |
| ⚠️ | Acceso condicionado / flujo de aprobación / solo proponer |
| ❌ | Sin acceso (oculto por Security Filter + Show_If + Valid_If) |
| "Su sucursal" | Filtrado por `Security Filter: IN([Sucursal_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL()))` |
| "Sus registros" | Filtrado por `Created_By = USEREMAIL()` o `Asignado_A = USEREMAIL()` |

---

## IMPLEMENTACIÓN TÉCNICA (3 CAPAS)

### Capa 1: Security Filter (Nivel Fila - Data → Tables → Security Filter)
**Obligatoria en TODAS las tablas transaccionales.**
```appsheet
IN([Sucursal_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL()))
```
*Catálogos compartidos:* `OR(USERROLE("Administrador"), IN(...))`

### Capa 2: USERROLE() en Show_If / Valid_If / Editable_If (Nivel Columna/Acción/Vista)
Ejemplos:
- Botón "Aprobar Merma": `Show_If = OR(USERROLE("Administrador"), AND(USERROLE("Encargado"), [Sucursal_ID] = LOOKUP(...)))`
- Columna `Costo_Actual`: `Valid_If = OR(USERROLE("Administrador"), AND(USERROLE("Encargado"), [Propuesta_Aprobada?]=TRUE))`
- Vista "Dashboard_Admin": `Show_If = USERROLE("Administrador")`

### Capa 3: Security → Require Sign-In → User Roles (Nivel App)
Configurar en **AppSheet Editor → Security → Require Sign-In → User Roles**:
- Tabla fuente: `Usuarios` (o `Usuarios_Sucursales` con columna `Role`)
- Columna Email: `Email`
- Columna Role: `Rol` (valores: "Administrador", "Encargado", "Operador")
- **Default Role:** `Operador` (denegación por defecto)

---

## FLUJOS DE APROBACIÓN CRÍTICOS

| Flujo | Inicia | Aprueba | Excepción | Trazabilidad |
|-------|--------|---------|-----------|--------------|
| **Merma** | Operador (Borrador) → Encargado (Aprobada/Rechazada/Corrección) | Encargado sucursal | Admin (anula, fuerza) | `Estado_Merma`, `Aprobado_Por`, `Fecha_Aprobacion`, `Motivo_Rechazo`, `Historial_Correcciones` |
| **Costo Insumo** | Encargado (Propone) → Admin (Aprueba/Rechaza) | Admin | - | `Propuesta_Costo`, `Propuesta_Por`, `Propuesta_Aprobada?`, `Historial_Costos` |
| **Transferencia** | Encargado Origen (Solicitada) → Encargado Destino (Aprobada) → Origen (Despachada) → Destino (Recibida) | Ambos Encargados | Admin (cancela) | `Estado`, responsables por etapa, `Diferencia_Recepcion` |
| **Conteo Inventario** | Operador (Completado) → Encargado (Aprobado/Con_Diferencias) | Encargado sucursal | Admin | `Estado`, `Fuera_Tolerancia?`, genera Merma automática si diff > tolerancia |
| **Horas Extra** | Operador (Registra) → Encargado (Aprueba) | Encargado | Admin | `Estado`, `Aprobado_Por`, `Fecha_Aprobacion` |

---

## PRUEBAS DE SEGURIDAD (Negativas - OBLIGATORIAS antes de deploy)

| Test | Cómo | Debe fallar |
|------|------|-------------|
| Operador ve mermas de otro operador | Login Operador A → Vista Mermas | Solo ve las suyas (`Created_By = USEREMAIL()`) |
| Encargado Sucursal A aprueba merma Sucursal B | Login Encargado A → Botón Aprobar en merma Sucursal B | Botón invisible (`Show_If` false) / Error Security Filter |
| Operador edita `Costo_Actual` ingrediente | Login Operador → Formulario Ingrediente → Cambia costo | `Valid_If` rechaza / Columna no editable (`Editable_If` false) |
| Usuario sin fila en `Usuarios_Sucursales` accede | Login email no registrado → Abre app | No ve **ningún** registro (Security Filter devuelve vacío) |
| Operador accede a vista "Config Global" | Login Operador → Menú lateral | Vista oculta (`Show_If = USERROLE("Administrador")`) |
| Encargado elimina registro (hard delete) | Login Encargado → Acción "Delete" | No existe acción Delete; solo Soft Delete (`Deleted?=TRUE`) y solo Admin ve botón "Restaurar" |
| Operador cambia `Sucursal_ID` en formulario | Login Operador → Nuevo registro → Intenta cambiar Sucursal | Campo `Sucursal_ID` `Show_If=FALSE` + `Initial Value` automático + `Editable_If=FALSE` |