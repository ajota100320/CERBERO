# ──────────────────────────────────────────────
# MERMAS - CRUD + LÓGICA INVENTARIO
# ──────────────────────────────────────────────

@app.get("/mermas", response_class=HTMLResponse)
async def list_mermas(request: Request, db: Session = Depends(get_db),
                      tipo: str = "", estado: str = "", page: int = 1, per_page: int = 20):
    query = db.query(RegistroMerma).options(joinedload(RegistroMerma.ingrediente))
    
    if tipo:
        query = query.filter(RegistroMerma.tipo == TipoMerma(tipo))
    if estado:
        query = query.filter(RegistroMerma.estado == EstadoAprobacion(estado))
    
    total = query.count()
    mermas = query.order_by(desc(RegistroMerma.fecha_registro)).offset((page - 1) * per_page).limit(per_page).all()
    
    return templates.TemplateResponse("mermas/list.html", {
        "request": request,
        "mermas": mermas,
        "tipos": list(TipoMerma),
        "estados": list(EstadoAprobacion),
        "tipo_filter": tipo,
        "estado_filter": estado,
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": (total + per_page - 1) // per_page,
    })


@app.get("/mermas/nueva", response_class=HTMLResponse)
async def new_merma_form(request: Request, db: Session = Depends(get_db)):
    ingredientes = db.query(IngredienteStock).filter(IngredienteStock.activo == True).order_by(IngredienteStock.nombre).all()
    
    return templates.TemplateResponse("mermas/form.html", {
        "request": request,
        "merma": None,
        "ingredientes": ingredientes,
        "tipos": list(TipoMerma),
        "action": "/mermas/nueva",
        "title": "Registrar Merma",
        "today": date.today().isoformat(),
        "now": datetime.now().time().isoformat()[:5],
    })


@app.post("/mermas/nueva")
async def create_merma(
    request: Request,
    db: Session = Depends(get_db),
    ingrediente_id: int = Form(...),
    tipo: str = Form(...),
    cantidad: float = Form(...),
    fecha_merma: str = Form(...),
    responsable: str = Form(""),
    observaciones: str = Form(""),
):
    ingrediente = db.query(IngredienteStock).filter(IngredienteStock.id == ingrediente_id).first()
    if not ingrediente:
        raise HTTPException(status_code=404, detail="Ingrediente no encontrado")
    
    if ingrediente.stock_actual < cantidad:
        raise HTTPException(status_code=400, detail=f"Stock insuficiente. Disponible: {ingrediente.stock_actual}")
    
    valor_perdida = cantidad * ingrediente.costo_promedio
    
    merma = RegistroMerma(
        ingrediente_id=ingrediente_id,
        tipo=TipoMerma(tipo),
        cantidad=cantidad,
        valor_perdida=valor_perdida,
        fecha_merma=datetime.strptime(fecha_merma, "%Y-%m-%d").date(),
        responsable=responsable or None,
        observaciones=observaciones or None,
        estado=EstadoAprobacion.PENDIENTE,
    )
    db.add(merma)
    db.flush()
    
    # NO descontar stock hasta que se apruebe (igual que AppSheet bot)
    # El bot de descuento se ejecuta al aprobar
    
    db.commit()
    return RedirectResponse(url="/mermas", status_code=303)


@app.post("/mermas/{merma_id}/aprobar")
async def aprobar_merma(merma_id: int, db: Session = Depends(get_db),
                        aprobado_por: str = Form(...)):
    merma = db.query(RegistroMerma).options(joinedload(RegistroMerma.ingrediente)).filter(RegistroMerma.id == merma_id).first()
    if not merma:
        raise HTTPException(status_code=404, detail="Merma no encontrada")
    
    if merma.estado == EstadoAprobacion.APROBADO:
        raise HTTPException(status_code=400, detail="Ya está aprobada")
    
    # Aplicar descuento de stock (Bot de descuento de mermas)
    ing = merma.ingrediente
    ing.stock_actual -= merma.cantidad
    ing.updated_at = func.now()
    
    merma.estado = EstadoAprobacion.APROBADO
    merma.aprobado_por = aprobado_por
    merma.fecha_aprobacion = func.now()
    
    db.commit()
    return RedirectResponse(url="/mermas", status_code=303)


@app.post("/mermas/{merma_id}/rechazar")
async def rechazar_merma(merma_id: int, db: Session = Depends(get_db),
                         rechazado_por: str = Form(...)):
    merma = db.query(RegistroMerma).filter(RegistroMerma.id == merma_id).first()
    if not merma:
        raise HTTPException(status_code=404, detail="Merma no encontrada")
    
    merma.estado = EstadoAprobacion.RECHAZADO
    merma.aprobado_por = rechazado_por
    merma.fecha_aprobacion = func.now()
    
    db.commit()
    return RedirectResponse(url="/mermas", status_code=303)


# ──────────────────────────────────────────────
# GASTOS - CRUD
# ──────────────────────────────────────────────

@app.get("/gastos", response_class=HTMLResponse)
async def list_gastos(request: Request, db: Session = Depends(get_db),
                      tipo: str = "", estado: str = "", page: int = 1, per_page: int = 20):
    query = db.query(ControlGasto)
    
    if tipo:
        query = query.filter(ControlGasto.tipo == TipoGasto(tipo))
    if estado:
        query = query.filter(ControlGasto.estado == EstadoAprobacion(estado))
    
    total = query.count()
    gastos = query.order_by(desc(ControlGasto.fecha_registro)).offset((page - 1) * per_page).limit(per_page).all()
    
    # Totales para el resumen
    total_mes = db.query(func.sum(ControlGasto.monto)).filter(
        ControlGasto.fecha_gasto >= date.today().replace(day=1)
    ).scalar() or 0
    
    return templates.TemplateResponse("gastos/list.html", {
        "request": request,
        "gastos": gastos,
        "tipos": list(TipoGasto),
        "estados": list(EstadoAprobacion),
        "tipo_filter": tipo,
        "estado_filter": estado,
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": (total + per_page - 1) // per_page,
        "total_mes": round(total_mes, 2),
    })


@app.get("/gastos/nuevo", response_class=HTMLResponse)
async def new_gasto_form(request: Request):
    return templates.TemplateResponse("gastos/form.html", {
        "request": request,
        "gasto": None,
        "tipos": list(TipoGasto),
        "action": "/gastos/nuevo",
        "title": "Nuevo Gasto",
        "today": date.today().isoformat(),
    })


@app.post("/gastos/nuevo")
async def create_gasto(
    request: Request,
    db: Session = Depends(get_db),
    tipo: str = Form(...),
    descripcion: str = Form(...),
    monto: float = Form(...),
    fecha_gasto: str = Form(...),
    proveedor: str = Form(""),
    numero_comprobante: str = Form(""),
    observaciones: str = Form(""),
):
    gasto = ControlGasto(
        tipo=TipoGasto(tipo),
        descripcion=descripcion,
        monto=monto,
        fecha_gasto=datetime.strptime(fecha_gasto, "%Y-%m-%d").date(),
        proveedor=proveedor or None,
        numero_comprobante=numero_comprobante or None,
        observaciones=observaciones or None,
        estado=EstadoAprobacion.PENDIENTE,
    )
    db.add(gasto)
    db.commit()
    return RedirectResponse(url="/gastos", status_code=303)


@app.post("/gastos/{gasto_id}/aprobar")
async def aprobar_gasto(gasto_id: int, db: Session = Depends(get_db),
                        aprobado_por: str = Form(...)):
    gasto = db.query(ControlGasto).filter(ControlGasto.id == gasto_id).first()
    if not gasto:
        raise HTTPException(status_code=404, detail="Gasto no encontrado")
    
    gasto.estado = EstadoAprobacion.APROBADO
    gasto.aprobado_por = aprobado_por
    gasto.fecha_aprobacion = func.now()
    
    db.commit()
    return RedirectResponse(url="/gastos", status_code=303)


@app.post("/gastos/{gasto_id}/rechazar")
async def rechazar_gasto(gasto_id: int, db: Session = Depends(get_db),
                         rechazado_por: str = Form(...)):
    gasto = db.query(ControlGasto).filter(ControlGasto.id == gasto_id).first()
    if not gasto:
        raise HTTPException(status_code=404, detail="Gasto no encontrado")
    
    gasto.estado = EstadoAprobacion.RECHAZADO
    gasto.aprobado_por = rechazado_por
    gasto.fecha_aprobacion = func.now()
    
    db.commit()
    return RedirectResponse(url="/gastos", status_code=303)


# ──────────────────────────────────────────────
# CHECKLIST DIARIO - APERTURA/CIERRE
# ──────────────────────────────────────────────

@app.get("/checklist", response_class=HTMLResponse)
async def list_checklist(request: Request, db: Session = Depends(get_db),
                         tipo: str = "", page: int = 1, per_page: int = 20):
    query = db.query(ListaVerificacionDiario)
    
    if tipo:
        query = query.filter(ListaVerificacionDiario.tipo == TipoChecklist(tipo))
    
    total = query.count()
    checklists = query.order_by(desc(ListaVerificacionDiario.fecha_hora_completa)).offset((page - 1) * per_page).limit(per_page).all()
    
    # Verificar si ya hay apertura/cierre hoy
    hoy = date.today()
    apertura_hoy = db.query(ListaVerificacionDiario).filter(
        ListaVerificacionDiario.fecha == hoy,
        ListaVerificacionDiario.tipo == TipoChecklist.APERTURA
    ).first()
    
    cierre_hoy = db.query(ListaVerificacionDiario).filter(
        ListaVerificacionDiario.fecha == hoy,
        ListaVerificacionDiario.tipo == TipoChecklist.CIERRE
    ).first()
    
    return templates.TemplateResponse("checklist/list.html", {
        "request": request,
        "checklists": checklists,
        "tipos": list(TipoChecklist),
        "tipo_filter": tipo,
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": (total + per_page - 1) // per_page,
        "apertura_hoy": apertura_hoy,
        "cierre_hoy": cierre_hoy,
        "today": hoy,
    })


@app.get("/checklist/nuevo", response_class=HTMLResponse)
async def new_checklist_form(request: Request, tipo: str = "APERTURA", db: Session = Depends(get_db)):
    # Verificar si ya existe uno del mismo tipo hoy
    hoy = date.today()
    existing = db.query(ListaVerificacionDiario).filter(
        ListaVerificacionDiario.fecha == hoy,
        ListaVerificacionDiario.tipo == TipoChecklist(tipo)
    ).first()
    
    if existing:
        return RedirectResponse(url=f"/checklist/{existing.id}/editar", status_code=303)
    
    return templates.TemplateResponse("checklist/form.html", {
        "request": request,
        "checklist": None,
        "tipo": TipoChecklist(tipo),
        "action": "/checklist/nuevo",
        "title": f"Checklist de {tipo.capitalize()}",
        "today": hoy.isoformat(),
        "now": datetime.now().time().isoformat()[:5],
    })


@app.post("/checklist/nuevo")
async def create_checklist(
    request: Request,
    db: Session = Depends(get_db),
    tipo: str = Form(...),
    fecha: str = Form(...),
    hora_registro: str = Form(...),
    responsable_nombre: str = Form(...),
    responsable_firma: str = Form(""),
    # Checklist items
    cocina_limpia: bool = Form(False),
    cocina_ordenada: bool = Form(False),
    basureros_vacios: bool = Form(False),
    equipos_funcionando: bool = Form(False),
    temperaturas_ok: bool = Form(False),
    extintores_ok: bool = Form(False),
    uniformes_limpios: bool = Form(False),
    manos_lavadas: bool = Form(False),
    cabello_cubierto: bool = Form(False),
    almacen_ordenado: bool = Form(False),
    sin_plagas: bool = Form(False),
    fecha_vencimiento_revisada: bool = Form(False),
    observaciones: str = Form(""),
):
    checklist = ListaVerificacionDiario(
        tipo=TipoChecklist(tipo),
        fecha=datetime.strptime(fecha, "%Y-%m-%d").date(),
        hora_registro=datetime.strptime(hora_registro, "%H:%M").time(),
        responsable_nombre=responsable_nombre,
        responsable_firma=responsable_firma or None,
        cocina_limpia=cocina_limpia,
        cocina_ordenada=cocina_ordenada,
        basureros_vacios=basureros_vacios,
        equipos_funcionando=equipos_funcionando,
        temperaturas_ok=temperaturas_ok,
        extintores_ok=extintores_ok,
        uniformes_limpios=uniformes_limpios,
        manos_lavadas=manos_lavadas,
        cabello_cubierto=cabello_cubierto,
        almacen_ordenado=almacen_ordenado,
        sin_plagas=sin_plagas,
        fecha_vencimiento_revisada=fecha_vencimiento_revisada,
        observaciones=observaciones or None,
    )
    db.add(checklist)
    db.commit()
    return RedirectResponse(url="/checklist", status_code=303)


@app.get("/checklist/{checklist_id}/editar", response_class=HTMLResponse)
async def edit_checklist_form(request: Request, checklist_id: int, db: Session = Depends(get_db)):
    checklist = db.query(ListaVerificacionDiario).filter(ListaVerificacionDiario.id == checklist_id).first()
    if not checklist:
        raise HTTPException(status_code=404, detail="Checklist no encontrado")
    
    return templates.TemplateResponse("checklist/form.html", {
        "request": request,
        "checklist": checklist,
        "tipo": checklist.tipo,
        "action": f"/checklist/{checklist_id}/editar",
        "title": f"Editar Checklist de {checklist.tipo.value.capitalize()}",
    })


@app.post("/checklist/{checklist_id}/editar")
async def update_checklist(
    checklist_id: int,
    db: Session = Depends(get_db),
    tipo: str = Form(...),
    fecha: str = Form(...),
    hora_registro: str = Form(...),
    responsable_nombre: str = Form(...),
    responsable_firma: str = Form(""),
    cocina_limpia: bool = Form(False),
    cocina_ordenada: bool = Form(False),
    basureros_vacios: bool = Form(False),
    equipos_funcionando: bool = Form(False),
    temperaturas_ok: bool = Form(False),
    extintores_ok: bool = Form(False),
    uniformes_limpios: bool = Form(False),
    manos_lavadas: bool = Form(False),
    cabello_cubierto: bool = Form(False),
    almacen_ordenado: bool = Form(False),
    sin_plagas: bool = Form(False),
    fecha_vencimiento_revisada: bool = Form(False),
    observaciones: str = Form(""),
):
    checklist = db.query(ListaVerificacionDiario).filter(ListaVerificacionDiario.id == checklist_id).first()
    if not checklist:
        raise HTTPException(status_code=404, detail="Checklist no encontrado")
    
    checklist.tipo = TipoChecklist(tipo)
    checklist.fecha = datetime.strptime(fecha, "%Y-%m-%d").date()
    checklist.hora_registro = datetime.strptime(hora_registro, "%H:%M").time()
    checklist.responsable_nombre = responsable_nombre
    checklist.responsable_firma = responsable_firma or None
    checklist.cocina_limpia = cocina_limpia
    checklist.cocina_ordenada = cocina_ordenada
    checklist.basureros_vacios = basureros_vacios
    checklist.equipos_funcionando = equipos_funcionando
    checklist.temperaturas_ok = temperaturas_ok
    checklist.extintores_ok = extintores_ok
    checklist.uniformes_limpios = uniformes_limpios
    checklist.manos_lavadas = manos_lavadas
    checklist.cabello_cubierto = cabello_cubierto
    checklist.almacen_ordenado = almacen_ordenado
    checklist.sin_plagas = sin_plagas
    checklist.fecha_vencimiento_revisada = fecha_vencimiento_revisada
    checklist.observaciones = observaciones or None
    
    db.commit()
    return RedirectResponse(url="/checklist", status_code=303)