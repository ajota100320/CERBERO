# Security Filters - Fase 6: Tareas + KPIs + Capacitación + Incidencias

## INSTRUCCIÓN DE USO
Para **CADA TABLA NUEVA** de Fase 6:
1. Abre AppSheet Editor → **Data → Tables**
2. Click en el nombre de la tabla → pestaña **Security Filter**
3. Copia y pega **EXACTAMENTE** la expresión correspondiente
4. Click **Save** → **Regenerate Structure** si te lo pide

---

## 1. Tareas (CATÁLOGO POR SUCURSAL - Admin ve todo, Encargado/Operador ven su sucursal si Activa)
```appsheet
OR(
  USERROLE("Administrador"),
  AND([Es_Activa?] = TRUE, IN([Sucursal_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL())))
)
```

## 2. Tarea_Programaciones (HEREDA DE TAREA → SUCURSAL)
```appsheet
OR(
  USERROLE("Administrador"),
  IN([Sucursal_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL()))
)
```

## 3. Tarea_Ejecuciones (HEREDA DE PROGRAMACIÓN → SUCURSAL)
```appsheet
OR(
  USERROLE("Administrador"),
  IN([Sucursal_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL()))
)
```

## 4. KPI_Definiciones (CATÁLOGO - Admin ve todo, Encargado ve su sucursal + globales)
```appsheet
OR(
  USERROLE("Administrador"),
  AND([Es_Activa?] = TRUE, OR([Sucursal_ID] = "", IN([Sucursal_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL()))))
)
```

## 5. Registros_KPI (HEREDA DE KPI → SUCURSAL)
```appsheet
OR(
  USERROLE("Administrador"),
  IN([Sucursal_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL()))
)
```

## 6. Capacitaciones (CATÁLOGO POR SUCURSAL - similar a Tareas)
```appsheet
OR(
  USERROLE("Administrador"),
  AND([Es_Activa?] = TRUE, IN([Sucursal_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL())))
)
```

## 7. Capacitaciones_Usuarios (HEREDA DE CAPACITACIÓN → SUCURSAL + USUARIO VE SUS ASIGNACIONES)
```appsheet
OR(
  USERROLE("Administrador"),
  AND([Usuario_ID] = USEREMAIL()),
  IN([Sucursal_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL()))
)
```

## 8. Incidencias (POR SUCURSAL - Admin ve todo, Encargado/Operador ven su sucursal)
```appsheet
OR(
  USERROLE("Administrador"),
  IN([Sucursal_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL()))
)
```

---

## ⚠️ REGLAS CRÍTICAS ESPECÍFICAS FASE 6

| Regla | Por qué |
|-------|---------|
| `Tareas`: `Sucursal_ID` **Required** + `Initial Value` = `LOOKUP(USEREMAIL(), ...)` | Encargado crea tarea → auto-asigna su sucursal |
| `Tarea_Programaciones`: `Sucursal_ID` **App Formula** = `LOOKUP([Tarea_ID], "Tareas", "Tarea_ID", "Sucursal_ID")` | Hereda sucursal de la tarea |
| `Tarea_Ejecuciones`: `Tarea_ID` **App Formula** = `LOOKUP([Prog_ID], "Tarea_Programaciones", "Prog_ID", "Tarea_ID")` | Hereda de programación |
| `Tarea_Ejecuciones`: `Duracion_Real_Min` **App Formula** = `[Hora_Fin] - [Hora_Inicio]` | Auto-calcula duración |
| `Tarea_Ejecuciones`: `Incidencia_Generada?` + `Incidencia_ID` → **Bot genera Incidencia automática** si checklist falla | Integración tareas → incidencias |
| `KPI_Definiciones`: `Formula_AppSheet` almacena fórmula como texto → **Bot evalúa y escribe Registros_KPI** | Cálculo dinámico programado |
| `KPI_Definiciones`: `Estado_KPI` en Registros_KPI = semáforo según umbrales (Verde/Amarillo/Rojo) | Visualización inmediata |
| `Capacitaciones_Usuarios`: `Fecha_Vencimiento` = `Fecha_Asignacion + Frecuencia_Renovacion_Meses * 30` | Renovación automática |
| `Incidencias`: `SLA_Horas` según severidad (Crítica=1, Alta=4, Media=8, Baja=24) | Escalado automático |
| `Incidencias`: `Tiempo_Respuesta_Horas` = `Fecha_Asignacion - Fecha_Reporte` | KPI respuesta |
| `Incidencias`: `Tiempo_Resolucion_Horas` = `Fecha_Cierre - Fecha_Reporte` | KPI resolución |

---

## VALID_IF ADICIONALES

### En `Tarea_Ejecuciones` → Columna `Estado` → Valid_If:
```appsheet
SWITCH([_THISROW_BEFORE].[Estado],
  "Pendiente", LIST("En_Proceso", "Omitida"),
  "En_Proceso", LIST("Completada", "Con_Incidencia"),
  "Completada", LIST(),
  "Omitida", LIST(),
  "Con_Incidencia", LIST("Completada"),
  LIST()
)
```

### En `Incidencias` → Columna `Estado` → Valid_If:
```appsheet
SWITCH([_THISROW_BEFORE].[Estado],
  "Abierta", LIST("En_Proceso", "Escalada", "Cancelada"),
  "En_Proceso", LIST("Resuelta", "Escalada"),
  "Escalada", LIST("En_Proceso", "Resuelta"),
  "Resuelta", LIST("Cerrada", "En_Proceso"),
  "Cerrada", LIST(),
  "Cancelada", LIST(),
  LIST()
)
```

### En `Capacitaciones_Usuarios` → Columna `Estado` → Valid_If:
```appsheet
SWITCH([_THISROW_BEFORE].[Estado],
  "Pendiente", LIST("En_Progreso", "Vencida", "Eximida"),
  "En_Progreso", LIST("Completada", "Vencida"),
  "Completada", LIST("Pendiente"),  // Para renovación
  "Vencida", LIST("En_Progreso", "Eximida"),
  "Eximida", LIST("Pendiente"),
  LIST()
)
```

---

## VERIFICACIÓN RÁPIDA POST-PEGADO

1. **Login Admin** → Ve TODAS las tareas, programaciones, ejecuciones, KPIs, capacitaciones, incidencias de AMBAS sucursales ✅
2. **Login Encargado Sucursal 1** → Ve SOLO de su sucursal + KPIs globales ✅
3. **Login Operador Sucursal 1** → Ve sus tareas programadas hoy, puede ejecutar, ve sus capacitaciones asignadas, puede reportar incidencias ✅
4. **Crear Tarea** como Encargado 1 → `Sucursal_ID` auto = Sucursal 1 ✅
5. **Programar Tarea** → Hereda sucursal, asigna rol/usuario, ventana horaria ✅
6. **Ejecutar Tarea** como Operador → Checklist dinámico, fotos, genera incidencia si falla ✅
7. **Reportar Incidencia** → Auto-asigna sucursal, SLA según severidad ✅
8. **KPIs** → Job diario/semanal calcula y muestra semáforo en Dashboard ✅