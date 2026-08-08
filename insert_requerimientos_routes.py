import re

file_path = r'C:\Users\hola\Documents\Mi segundo Cerebro\Nuevo proyecto ERP\app\main.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# We want to insert the new routes just before the HEALTH CHECK comment block.
pattern = r'(\n# ──────────────────────────────────────────────\n# HEALTH CHECK\n)'

new_routes = '''
# ──────────────────────────────────────────────
# REQUERIMIENTOS - CRUD COMPLETO (Fase 2)
# ──────────────────────────────────────────────

@app.get("/requerimientos", response_class=HTMLResponse)
async def list_requerimientos(request: Request, db: Session = Depends(get_db), user: Usuario = Depends(require_encargado_or_admin)):
    """
    Lista todos los requerimientos y calcula el total proyectado.
    Solo accesible para ENCARGADO y ADMINISTRADOR.
    """
    requerimientos = db.query(Requerimientos).order_by(Requerimientos.fecha_registro.desc()).all()
    total_proyectado = sum(r.cantidad * r.precio_estimado for r in requerimientos)
    # Obtener lista de sucursales para el formulario (solo activas)
    sucursales = db.query(Sucursal).filter(Sucursal.activa == True).order_by(Sucursal.nombre).all()
    return templates.TemplateResponse(request=request, name="requerimientos.html", context={
        "request": request,
        "user": user,
        "requerimientos": requerimientos,
        "total_proyectado": total_proyectado,
        "sucursales": sucursales
    })

@app.post("/requerimientos")
async def create_requerimiento(
    request: Request,
    db: Session = Depends(get_db),
    user: Usuario = Depends(require_encargado_or_admin),
    producto: str = Form(...),
    cantidad: float = Form(...),
    precio_estimado: float = Form(...),
    prioridad: str = Form(...),
    sucursal_id: int = Form(...)
):
    """
    Crea un nuevo requerimiento y envía notificación de Telegram.
    """
    # Validar que la sucursal existe y está activa
    sucursal = db.query(Sucursal).filter(Sucursal.id == sucursal_id, Sucursal.activa == True).first()
    if not sucursal:
        raise HTTPException(status_code=404, detail="Sucursal no encontrada o inactiva")
    # Validar prioridad
    try:
        prioridad_enum = Prioridad(prioridad)
    except ValueError:
        raise HTTPException(status_code=400, detail="Prioridad inválida")
    # Crear el objeto requerimiento
    requerimiento = Requerimientos(
        producto=producto,
        cantidad=cantidad,
        precio_estimado=precio_estimado,
        prioridad=prioridad_enum,
        sucursal_id=sucursal_id
    )
    db.add(requerimiento)
    db.commit()
    db.refresh(requerimiento)
    # Preparar mensaje de Telegram
    total = cantidad * precio_estimado
    mensaje = f"🚨 NUEVO REQUERIMIENTO ({prioridad}): {cantidad}x {producto} - Total: ${total:.2f}"
    # Enviar notificación (no bloqueante, pero esperamos por si falla)
    try:
        await enviar_alerta_telegram(mensaje)
    except Exception:
        # No fallamos la creación si falla Telegram
        pass
    # Redirigir de vuelta a la lista con mensaje de éxito
    return RedirectResponse(url="/requerimientos?ok=1", status_code=status.HTTP_303_SEE_OTHER)

'''

# Insert the new_routes before the health comment
new_content = re.sub(pattern, new_routes + r'\1', content)

# Write back
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print('Added GET and POST routes for /requerimientos in main.py')