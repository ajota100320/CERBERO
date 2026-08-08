# ──────────────────────────────────────────────
# COMPRAS - PADRE (Cabecera) + HIJO (Detalle)
# ──────────────────────────────────────────────

@app.get("/compras", response_class=HTMLResponse)
async def list_compras(request: Request, db: Session = Depends(get_db),
                       estado: str = "", page: int = 1, per_page: int = 20):
    query = db.query(RegistroCompra).options(joinedload(RegistroCompra.proveedor))
    
    if estado:
        query = query.filter(RegistroCompra.estado == EstadoAprobacion(estado))
    
    total = query.count()
    compras = query.order_by(desc(RegistroCompra.fecha_registro)).offset((page - 1) * per_page).limit(per_page).all()
    
    return templates.TemplateResponse("compras/list.html", {
        "request": request,
        "compras": compras,
        "estados": list(EstadoAprobacion),
        "estado_filter": estado,
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": (total + per_page - 1) // per_page,
    })


@app.get("/compras/nueva", response_class=HTMLResponse)
async def new_compra_form(request: Request, db: Session = Depends(get_db)):
    proveedores = db.query(Proveedor).filter(Proveedor.activo == True).order_by(Proveedor.nombre).all()
    ingredientes = db.query(IngredienteStock).filter(IngredienteStock.activo == True).order_by(IngredienteStock.nombre).all()
    
    return templates.TemplateResponse("compras/form.html", {
        "request": request,
        "compra": None,
        "proveedores": proveedores,
        "ingredientes": ingredientes,
        "action": "/compras/nueva",
        "title": "Nueva Compra",
        "today": date.today().isoformat(),
    })


@app.post("/compras/nueva")
async def create_compra(
    request: Request,
    db: Session = Depends(get_db),
    numero_factura: str = Form(...),
    proveedor_id: int = Form(...),
    fecha_compra: str = Form(...),
    observaciones: str = Form(""),
    # Detalles - arrays
    ingrediente_id: List[int] = Form([]),
    cantidad: List[float] = Form([]),
    costo_unitario: List[float] = Form([]),
    fecha_vencimiento: List[str] = Form([]),
    lote: List[str] = Form([]),
):
    # Validar factura única
    existing = db.query(RegistroCompra).filter(RegistroCompra.numero_factura == numero_factura).first()
    if existing:
        raise HTTPException(status_code=400, detail="Número de factura ya existe")
    
    compra = RegistroCompra(
        numero_factura=numero_factura,
        proveedor_id=proveedor_id,
        fecha_compra=datetime.strptime(fecha_compra, "%Y-%m-%d").date(),
        observaciones=observaciones or None,
        estado=EstadoAprobacion.PENDIENTE,
    )
    db.add(compra)
    db.flush()  # Para obtener el ID
    
    # Procesar detalles
    subtotal = 0.0
    for i, ing_id in enumerate(ingrediente_id):
        if i < len(cantidad) and cantidad[i] > 0:
            ing = db.query(IngredienteStock).filter(IngredienteStock.id == ing_id).first()
            if not ing:
                continue
            
            cant = cantidad[i]
            cost_u = costo_unitario[i] if i < len(costo_unitario) else ing.costo_promedio
            cost_total = cant * cost_u
            
            f_venc = None
            if i < len(fecha_vencimiento) and fecha_vencimiento[i]:
                f_venc = datetime.strptime(fecha_vencimiento[i], "%Y-%m-%d").date()
            
            lote_val = lote[i] if i < len(lote) else None
            
            detalle = DetalleCompra(
                compra_id=compra.id,
                ingrediente_id=ing_id,
                cantidad=cant,
                costo_unitario=cost_u,
                costo_total=cost_total,
                fecha_vencimiento=f_venc,
                lote=lote_val,
            )
            db.add(detalle)
            
            # Actualizar stock y costo promedio (lógica de inventario autónomo)
            nuevo_stock = ing.stock_actual + cant
            if ing.stock_actual > 0:
                ing.costo_promedio = ((ing.stock_actual * ing.costo_promedio) + (cant * cost_u)) / nuevo_stock
            else:
                ing.costo_promedio = cost_u
            ing.stock_actual = nuevo_stock
            ing.updated_at = func.now()
            
            subtotal += cost_total
    
    iva = subtotal * 0.19
    compra.subtotal = subtotal
    compra.iva = iva
    compra.total = subtotal + iva
    
    db.commit()
    return RedirectResponse(url="/compras", status_code=303)


@app.get("/compras/{compra_id}", response_class=HTMLResponse)
async def view_compra(request: Request, compra_id: int, db: Session = Depends(get_db)):
    compra = db.query(RegistroCompra).options(
        joinedload(RegistroCompra.proveedor),
        joinedload(RegistroCompra.detalles).joinedload(DetalleCompra.ingrediente)
    ).filter(RegistroCompra.id == compra_id).first()
    
    if not compra:
        raise HTTPException(status_code=404, detail="Compra no encontrada")
    
    return templates.TemplateResponse("compras/detail.html", {
        "request": request,
        "compra": compra,
    })


@app.post("/compras/{compra_id}/aprobar")
async def aprobar_compra(compra_id: int, db: Session = Depends(get_db),
                         aprobado_por: str = Form(...)):
    compra = db.query(RegistroCompra).filter(RegistroCompra.id == compra_id).first()
    if not compra:
        raise HTTPException(status_code=404, detail="Compra no encontrada")
    
    compra.estado = EstadoAprobacion.APROBADO
    compra.aprobado_por = aprobado_por
    compra.fecha_aprobacion = func.now()
    
    db.commit()
    return RedirectResponse(url=f"/compras/{compra_id}", status_code=303)


@app.post("/compras/{compra_id}/rechazar")
async def rechazar_compra(compra_id: int, db: Session = Depends(get_db),
                          rechazado_por: str = Form(...)):
    compra = db.query(RegistroCompra).filter(RegistroCompra.id == compra_id).first()
    if not compra:
        raise HTTPException(status_code=404, detail="Compra no encontrada")
    
    # Revertir stock si ya fue aprobada
    if compra.estado == EstadoAprobacion.APROBADO:
        for detalle in compra.detalles:
            ing = detalle.ingrediente
            ing.stock_actual -= detalle.cantidad
            ing.updated_at = func.now()
    
    compra.estado = EstadoAprobacion.RECHAZADO
    compra.aprobado_por = rechazado_por
    compra.fecha_aprobacion = func.now()
    
    db.commit()
    return RedirectResponse(url=f"/compras/{compra_id}", status_code=303)