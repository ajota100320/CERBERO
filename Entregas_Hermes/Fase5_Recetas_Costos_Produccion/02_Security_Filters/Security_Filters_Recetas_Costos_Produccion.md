# Security Filters - Recetas + Costos + Producción (Fase 5)

## INSTRUCCIÓN DE USO
Para **CADA TABLA NUEVA** de Fase 5:
1. Abre AppSheet Editor → **Data → Tables**
2. Click en el nombre de la tabla → pestaña **Security Filter**
3. Copia y pega **EXACTAMENTE** la expresión correspondiente
4. Click **Save** → **Regenerate Structure** si te lo pide

---

## 1. Recetas (CATÁLOGO POR SUCURSAL - Admin ve todo, Encargado/Operador ven su sucursal si Activa)
```appsheet
OR(
  USERROLE("Administrador"),
  AND([Es_Activa?] = TRUE, IN([Sucursal_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL())))
)
```

## 2. Receta_Ingredientes (HEREDA DE RECETA)
```appsheet
OR(
  USERROLE("Administrador"),
  IN([Receta_ID].[Sucursal_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL()))
)
```

## 3. Produccion (HEREDA DE RECETA → SUCURSAL)
```appsheet
OR(
  USERROLE("Administrador"),
  IN([Sucursal_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL()))
)
```

## 4. Produccion_Detalle (HEREDA DE PRODUCCION → SUCURSAL)
```appsheet
OR(
  USERROLE("Administrador"),
  IN([Produccion_ID].[Sucursal_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL()))
)
```

## 5. Costos_Historicos (CATÁLOGO COMPARTIDO - Admin ve todo, Encargado ve su sucursal)
```appsheet
OR(
  USERROLE("Administrador"),
  IN([Sucursal_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL()))
)
```

---

## ⚠️ REGLAS CRÍTICAS ESPECÍFICAS FASE 5

| Regla | Por qué |
|-------|---------|
| `Recetas`: `Sucursal_ID` **Required** + `Initial Value` = `LOOKUP(USEREMAIL(), ...)` | Encargado crea receta → auto-asigna su sucursal |
| `Recetas`: `Estado` = "Aprobada" → **Solo Admin puede aprobar** (Show_If en acción) | Control de costos centralizado |
| `Recetas`: `Costo_Total_Receta` y `Costo_Por_Porciona` son **App Formula** (solo lectura) | Se calculan desde `Receta_Ingredientes` |
| `Receta_Ingredientes`: `Costo_Unitario_Snapshot` = `LOOKUP([Ingrediente_ID], "Ingredientes_y_Stock", "Ingrediente_ID", "Costo_Actual")` | Congela costo al momento de crear línea |
| `Produccion`: `Sucursal_ID` **App Formula** = `LOOKUP([Receta_ID], "Recetas", "Receta_ID", "Sucursal_ID")` | Hereda sucursal de la receta |
| `Produccion_Detalle`: `Cantidad_Teorica` = fórmula proporcional a `Cantidad_Producida` | Escala automática según cuánto se produce |
| `Produccion_Detalle`: `Costo_Real_Linea` = `Cantidad_Real` * `Costo_Actual` (vivo) | Compara real vs teórico con costo actual |
| `Costos_Historicos`: Se alimenta **automáticamente** via Bot cuando cambia costo en Ingredientes/Recetas | Auditoría completa de variaciones |

---

## VALID_IF ADICIONALES

### En `Recetas` → Columna `Estado` → Valid_If:
```appsheet
SWITCH([_THISROW_BEFORE].[Estado],
  "Borrador", LIST("En_Revision", "Obsoleta"),
  "En_Revision", LIST("Aprobada", "Borrador", "Obsoleta"),
  "Aprobada", LIST("Obsoleta"),
  "Obsoleta", LIST(),
  LIST()
)
```

### En `Produccion` → Columna `Estado` → Valid_If:
```appsheet
SWITCH([_THISROW_BEFORE].[Estado],
  "En_Proceso", LIST("Completada", "Cancelada", "Con_Diferencias"),
  "Completada", LIST(),
  "Cancelada", LIST(),
  "Con_Diferencias", LIST(),
  LIST()
)
```

---

## VERIFICACIÓN RÁPIDA POST-PEGADO

1. **Login Admin** → Ve TODAS las recetas, producciones, costos de AMBAS sucursales ✅
2. **Login Encargado Sucursal 1** → Ve SOLO recetas/producciones/costos con `Sucursal_ID = Sucursal 1` ✅
3. **Login Operador Sucursal 1** → Ve recetas **Activas** de su sucursal + puede registrar producción ✅
4. **Crear Receta** como Encargado 1 → `Sucursal_ID` auto = Sucursal 1, `Estado` = Borrador ✅
5. **Aprobar Receta** como Admin → `Estado` = Aprobada, `Aprobada_Por` = Admin, `Fecha_Aprobacion` = NOW() ✅
6. **Producir** como Operador → Crea `Produccion` + `Produccion_Detalle` con consumos reales ✅