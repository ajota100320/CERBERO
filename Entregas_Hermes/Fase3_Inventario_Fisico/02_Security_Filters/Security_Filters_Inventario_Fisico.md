# Security Filters - Inventario Físico (Fase 3)

## INSTRUCCIÓN DE USO
Para **CADA TABLA NUEVA** de inventario físico:
1. Abre AppSheet Editor → **Data → Tables**
2. Click en el nombre de la tabla → pestaña **Security Filter**
3. Copia y pega **EXACTAMENTE** la expresión correspondiente
4. Click **Save** → **Regenerate Structure** si te lo pide

---

## 1. Plantillas_Inventario (CATÁLOGO POR SUCURSAL - Encargado/Admin crean, Operador ve solo su sucursal)
```appsheet
OR(
  USERROLE("Administrador"),
  IN([Sucursal_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL()))
)
```

## 2. Conteos_Inventario (CABECERA - Hereda seguridad por Sucursal_ID)
```appsheet
IN([Sucursal_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL()))
```

## 3. Items_Conteo (DETALLE - Hereda por Conteo_ID → Sucursal_ID)
```appsheet
IN([Conteo_ID].[Sucursal_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL()))
```

## 4. Ajustes_Inventario (Hereda por Conteo_ID → Sucursal_ID)
```appsheet
IN([Conteo_ID].[Sucursal_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL()))
```

---

## ⚠️ REGLAS CRÍTICAS ESPECÍFICAS INVENTARIO

| Regla | Por qué |
|-------|---------|
| **Todas** las 4 tablas nuevas tienen columna `Sucursal_ID` (Ref → Sucursales) | El Security Filter filtra por esta columna |
| `Plantillas_Inventario`: `Sucursal_ID` es **Required** + `Initial Value` = `LOOKUP(USEREMAIL(), ...)` | Encargado crea plantilla → auto-asigna su sucursal |
| `Conteos_Inventario`: `Sucursal_ID` **App Formula** = `LOOKUP([Plantilla_ID], "Plantillas_Inventario", "Plantilla_ID", "Sucursal_ID")` | Hereda sucursal de la plantilla (no editable) |
| `Items_Conteo`: `Sucursal_ID` **App Formula** = `LOOKUP([Conteo_ID], "Conteos_Inventario", "Conteo_ID", "Sucursal_ID")` | Hereda del conteo padre |
| `Ajustes_Inventario`: `Sucursal_ID` **App Formula** = `LOOKUP([Conteo_ID], "Conteos_Inventario", "Conteo_ID", "Sucursal_ID")` | Hereda del conteo padre |
| Tablas **hijas (Is Part Of)**: `Items_Conteo` y `Ajustes_Inventario` → Security Filter referencia **padre → Sucursal_ID** | AppSheet no hereda Security Filter automático en hijas |

---

## VERIFICACIÓN RÁPIDA POST-PEGADO

1. **Login Admin** → Ve TODAS las plantillas, conteos, items, ajustes de AMBAS sucursales ✅
2. **Login Encargado Sucursal 1** → Ve SOLO plantillas/conteos/items/ajustes con `Sucursal_ID = Sucursal 1` ✅
3. **Login Operador Sucursal 1** → Ve SOLO conteos/items de SU sucursal (no ve Plantillas) ✅
4. **Crear Plantilla** como Encargado 1 → `Sucursal_ID` se autollenna = Sucursal 1 ✅
5. **Crear Conteo** desde Plantilla → `Sucursal_ID` hereda de plantilla ✅
6. **Crear Item** en Conteo → `Sucursal_ID` hereda de conteo ✅

---

## SI ALGO FALLA: Debugging

| Síntoma | Causa probable | Solución |
|---------|----------------|----------|
| Usuario no ve **ningún** registro | No tiene fila en `Usuarios_Sucursales` | Agregar fila con email exacto + Sucursal_ID + Rol |
| Encargado ve plantillas de **otra** sucursal | Security Filter mal pegado / `Sucursal_ID` vacío en datos | Verificar expresión exacta + poblar `Sucursal_ID` en plantillas existentes |
| Error "Column not found: Sucursal_ID" | Tabla no tiene la columna | Agregar en Sheets → Sheets + Regenerate Structure |
| Operador ve **Plantillas** (no debería) | Falta `Show_If` en Vista | Vista Plantillas: `Show_If = OR(USERROLE("Administrador"), USERROLE("Encargado"))` |