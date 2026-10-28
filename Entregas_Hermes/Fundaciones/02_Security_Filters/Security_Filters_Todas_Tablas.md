# Security Filters - Multisucursal por Usuario/Email

## INSTRUCCIÓN DE USO
Para **CADA TABLA TRANSACCIONAL** listada abajo:
1. Abre AppSheet Editor → **Data → Tables**
2. Click en el nombre de la tabla → pestaña **Security Filter** (filtro de seguridad)
3. Copia y pega **EXACTAMENTE** la expresión correspondiente
4. Click **Save** → **Regenerate Structure** si te lo pide

---

## 1. Ingredientes_y_Stock
```appsheet
IN([Sucursal_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL()))
```

## 2. Registro_de_Compras
```appsheet
IN([Sucursal_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL()))
```

## 3. Detalle_de_Compras
```appsheet
IN([Sucursal_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL()))
```

## 4. Registro_de_Mermas_y_Vencimientos
```appsheet
IN([Sucursal_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL()))
```

## 5. Control_de_Gastos
```appsheet
IN([Sucursal_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL()))
```

## 6. Lista_de_Verificacion_Diario
```appsheet
IN([Sucursal_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL()))
```

## 7. Higiene_del_Personal
```appsheet
IN([Sucursal_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL()))
```

## 8. Registro_Temperaturas
```appsheet
IN([Sucursal_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL()))
```

## 9. Proveedores (CATÁLOGO COMPARTIDO - Admin ve todo, Encargado/Operador solo su sucursal)
```appsheet
OR(
  USERROLE("Administrador"),
  IN([Sucursal_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL()))
)
```

## 10. Tareas (TABLA NUEVA - cuando la crees)
```appsheet
IN([Sucursal_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL()))
```

## 11. Conteos_Inventario (TABLA NUEVA - cuando la crees)
```appsheet
IN([Sucursal_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL()))
```

## 12. Items_Conteo (TABLA NUEVA - hija de Conteos, hereda por Ref)
```appsheet
IN([Conteo_ID].[Sucursal_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL()))
```

---

## 13. Órdenes_Transferencia (TABLA NUEVA - origen O destino)
```appsheet
OR(
  IN([Sucursal_Origen_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL())),
  IN([Sucursal_Destino_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL()))
)
```

## 14. Recetas (CATÁLOGO COMPARTIDO - todos leen, solo Admin/Encargado escriben)
```appsheet
OR(
  USERROLE("Administrador"),
  USERROLE("Encargado"),
  AND(USERROLE("Operador"), [Aprobada?] = TRUE)
)
```

---

## ⚠️ REGLAS CRÍTICAS

| Regla | Por qué |
|-------|---------|
| **TODAS** las tablas transaccionales deben tener columna `Sucursal_ID` (Ref → Sucursales) | El Security Filter filtra por esta columna |
| `Usuarios_Sucursales` debe tener filas para **cada usuario activo** con su `Sucursal_ID` y `Rol` | Sin filas = usuario no ve nada |
| `USEREMAIL()` debe coincidir **exactamente** con `Usuarios_Sucursales[Email]` (case-sensitive en Sheets) | Email "Juan@dominio.com" ≠ "juan@dominio.com" |
| Tablas **catálogo compartido** (Proveedores, Recetas, Categorias, Unidades) usan `OR(USERROLE("Administrador"), ...)` | Admin ve todo; Encargado/Operador solo su sucursal |
| Tablas **hijas (Is Part Of)** heredan seguridad del padre si no tienen `Sucursal_ID` propia | Ej: `Items_Conteo` filtra por `Conteo_ID.[Sucursal_ID]` |
| **Regenera estructura** (Regenerate Structure) después de pegar cada Security Filter | AppSheet actualiza columnas virtuales y slices |

---

## VERIFICACIÓN RÁPIDA (Haz esto DESPUÉS de pegar todos)

1. **Login como Admin** → Debes ver **TODOS** los registros de ambas sucursales en cada tabla
2. **Login como Encargado Sucursal A** → Debes ver **SOLO** registros con `Sucursal_ID = "SUC_A"`
3. **Login como Operador Sucursal B** → Debes ver **SOLO** tus propios registros (`Created_By = USEREMAIL()`) + los de tu sucursal según reglas
4. **Intenta crear registro** como Encargado A → `Sucursal_ID` debe autollenarse con `LOOKUP(USEREMAIL(), ...)` y no dejarse editar a otra sucursal

---

## SI ALGO FALLA: Debugging

| Síntoma | Causa probable | Solución |
|---------|----------------|----------|
| Usuario no ve **ningún** registro | No tiene fila en `Usuarios_Sucursales` o email no coincide | Agregar fila en `Usuarios_Sucursales` con email exacto |
| Usuario ve registros de **otra** sucursal | `Sucursal_ID` vacío o mal asignado en datos | Revisar `Initial Value` de `Sucursal_ID` = `LOOKUP(...)` |
| Error "Column not found: Sucursal_ID" | Tabla no tiene la columna | Agregar columna `Sucursal_ID` (Ref → Sucursales) + `Initial Value` |
| Admin no ve todo | Security Filter mal escrito (falta `USERROLE("Administrador")`) | En catálogos compartidos, agregar `OR(USERROLE("Administrador"), ...)` |