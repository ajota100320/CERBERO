# Security Filters - Transferencias entre Sucursales (Fase 4)

## INSTRUCCIÓN DE USO
Para **CADA TABLA NUEVA** de transferencias:
1. Abre AppSheet Editor → **Data → Tables**
2. Click en el nombre de la tabla → pestaña **Security Filter**
3. Copia y pega **EXACTAMENTE** la expresión correspondiente
4. Click **Save** → **Regenerate Structure** si te lo pide

---

## 1. Ordenes_Transferencia (VISIBLE PARA ORIGEN Y DESTINO)
```appsheet
OR(
  IN([Sucursal_Origen_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL())),
  IN([Sucursal_Destino_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL())),
  USERROLE("Administrador")
)
```

## 2. Items_Transferencia (HEREDA DE ORDEN - ORIGEN)
```appsheet
OR(
  IN([Orden_ID].[Sucursal_Origen_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL())),
  IN([Orden_ID].[Sucursal_Destino_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL())),
  USERROLE("Administrador")
)
```

## 3. Recepciones_Transferencia (VISIBLE PARA DESTINO)
```appsheet
OR(
  IN([Orden_ID].[Sucursal_Destino_ID], SELECT(Usuarios_Sucursales[Sucursal_ID], [Email] = USEREMAIL())),
  USERROLE("Administrador")
)
```

---

## ⚠️ REGLAS CRÍTICAS ESPECÍFICAS TRANSFERENCIAS

| Regla | Por qué |
|-------|---------|
| `Ordenes_Transferencia` tiene **DOS** sucursales: `Sucursal_Origen_ID` y `Sucursal_Destino_ID` | Security Filter usa `OR` para mostrar a ambos lados |
| `Sucursal_ID` (columna auditoría) = `Sucursal_Origen_ID` por convenio | Security Filter hereda de origen; destino ve por `OR` en expresión |
| `Items_Transferencia` → Security Filter referencia `Orden_ID.[Sucursal_Origen_ID]` y `Orden_ID.[Sucursal_Destino_ID]` | Hereda visibilidad de la orden padre |
| `Recepciones_Transferencia` → Solo `Sucursal_Destino_ID` | Solo destino recibe; origen ve a través de Items/Orden |
| `Sucursal_Origen_ID` ≠ `Sucursal_Destino_ID` → **Valid_If obligatorio** | No transferir a la misma sucursal |

---

## VALID_IF ADICIONALES (Pegar en columnas correspondientes)

### En `Ordenes_Transferencia` → Columna `Sucursal_Destino_ID` → Valid_If:
```appsheet
AND(
  IN([_THIS], SELECT(Sucursales[Sucursal_ID], [Activa?] = TRUE)),
  [_THIS] <> [Sucursal_Origen_ID]
)
```

### En `Ordenes_Transferencia` → Columna `Estado` → Valid_If (Máquina de estados):
```appsheet
SWITCH([_THISROW_BEFORE].[Estado],
  "Borrador", LIST("Solicitada", "Cancelada"),
  "Solicitada", LIST("Aprobada_Origen", "Cancelada"),
  "Aprobada_Origen", LIST("Aprobada_Destino", "Cancelada"),
  "Aprobada_Destino", LIST("En_Preparacion", "Cancelada"),
  "En_Preparacion", LIST("Despachada", "Cancelada"),
  "Despachada", LIST("En_Transito", "Cancelada"),
  "En_Transito", LIST("Recibida_Completa", "Recibida_Con_Diferencias", "Cancelada"),
  "Recibida_Completa", LIST(),
  "Recibida_Con_Diferencias", LIST(),
  "Cancelada", LIST(),
  LIST()
)
```

---

## VERIFICACIÓN RÁPIDA POST-PEGADO

1. **Login Admin** → Ve TODAS las órdenes, items, recepciones de AMBAS sucursales ✅
2. **Login Encargado Sucursal 1** → Ve órdenes donde `Sucursal_Origen_ID = Sucursal 1` OR `Sucursal_Destino_ID = Sucursal 1` ✅
3. **Login Encargado Sucursal 2** → Ve órdenes donde `Sucursal_Origen_ID = Sucursal 2` OR `Sucursal_Destino_ID = Sucursal 2` ✅
4. **Login Operador Sucursal 1** → Ve items/recepciones de órdenes de SU sucursal (origen o destino) ✅
5. **Crear Orden** Encargado 1 → `Sucursal_Origen_ID` auto = Sucursal 1, elige Destino = Sucursal 2 ✅
6. **Valid_If** → No permite `Sucursal_Destino_ID = Sucursal_Origen_ID` ✅

---

## SI ALGO FALLA: Debugging

| Síntoma | Causa probable | Solución |
|---------|----------------|----------|
| Encargado 1 NO ve orden que él solicitó | Security Filter mal pegado / `Sucursal_Origen_ID` vacío | Verificar expresión `OR` exacta + poblar `Sucursal_Origen_ID` |
| Encargado 2 (destino) NO ve orden entrante | Security Filter falta `Sucursal_Destino_ID` en `OR` | Agregar `IN([Sucursal_Destino_ID], SELECT(...))` al filter |
| Operador ve items de orden ajena | `Items_Transferencia` filter mal referenciado | Usar `Orden_ID.[Sucursal_Origen_ID]` y `Orden_ID.[Sucursal_Destino_ID]` |
| Error "Circular reference" en `Sucursal_ID` | `Sucursal_ID` App Formula referencia a sí misma | `Sucursal_ID` = `LOOKUP([Sucursal_Origen_ID], "Sucursales", "Sucursal_ID", "Sucursal_ID")` (no autorreferencia) |