# ──────────────────────────────────────────────
# HIGIENE PERSONAL - CRUD
# ──────────────────────────────────────────────

@app.get("/higiene", response_class=HTMLResponse)
async def list_higiene(request: Request, db: Session = Depends(get_db),
                       page: int = 1, per_page: int = 20):
    query = db.query(HigienePersonal)
    
    total = query.count()
    auditorias = query.order_by(desc(HigienePersonal.fecha_registro)).offset((page - 1) * per_page).limit(per_page).all()
    
    # Estadísticas
    total_mes = db.query(HigienePersonal).filter(
        HigienePersonal.fecha_auditoria >= date.today().replace(day=1)
    ).count()
    
    aprobados_mes = db.query(HigienePersonal).filter(
        HigienePersonal.fecha_auditoria >= date.today().replace(day=1),
        HigienePersonal.aprobado == True
    ).count()
    
    return templates.TemplateResponse("higiene/list.html", {
        "request": request,
        "auditorias": auditorias,
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": (total + per_page - 1) // per_page,
        "total_mes": total_mes,
        "aprobados_mes": aprobados_mes,
        "porcentaje": round((aprobados_mes / total_mes * 100) if total_mes > 0 else 0, 1),
    })


@app.get("/higiene/nueva", response_class=HTMLResponse)
async def new_higiene_form(request: Request):
    return templates.TemplateResponse("higiene/form.html", {
        "request": request,
        "auditoria": None,
        "action": "/higiene/nueva",
        "title": "Nueva Auditoría de Higiene",
        "today": date.today().isoformat(),
        "now": datetime.now().time().isoformat()[:5],
    })


@app.post("/higiene/nueva")
async def create_higiene(
    request: Request,
    db: Session = Depends(get_db),
    empleado_nombre: str = Form(...),
    empleado_cargo: str = Form(""),
    fecha_auditoria: str = Form(...),
    hora_auditoria: str = Form(...),
    auditor_nombre: str = Form(...),
    auditor_firma: str = Form(""),
    uñas_cortas_limpias: bool = Form(False),
    manos_limpias: bool = Form(False),
    sin_joyas: bool = Form(False),
    uniforme_limpio: bool = Form(False),
    cabello_cubierto: bool = Form(False),
    calzado_adecuado: bool = Form(False),
    sin_lesiones_visibles: bool = Form(False),
    lavado_manos_correcto: bool = Form(False),
    observaciones: str = Form(""),
):
    # Cálculo automático de aprobado (todos los criterios deben ser True)
    criterios = [
        uñas_cortas_limpias, manos_limpias, sin_joyas,
        uniforme_limpio, cabello_cubierto, calzado_adecuado,
        sin_lesiones_visibles, lavado_manos_correcto
    ]
    aprobado = all(criterios)
    
    auditoria = HigienePersonal(
        empleado_nombre=empleado_nombre,
        empleado_cargo=empleado_cargo or None,
        fecha_auditoria=datetime.strptime(fecha_auditoria, "%Y-%m-%d").date(),
        hora_auditoria=datetime.strptime(hora_auditoria, "%H:%M").time(),
        auditor_nombre=auditor_nombre,
        auditor_firma=auditor_firma or None,
        uñas_cortas_limpias=uñas_cortas_limpias,
        manos_limpias=manos_limpias,
        sin_joyas=sin_joyas,
        uniforme_limpio=uniforme_limpio,
        cabello_cubierto=cabello_cubierto,
        calzado_adecuado=calzado_adecuado,
        sin_lesiones_visibles=sin_lesiones_visibles,
        lavado_manos_correcto=lavado_manos_correcto,
        aprobado=aprobado,
        observaciones=observaciones or None,
    )
    db.add(auditoria)
    db.commit()
    return RedirectResponse(url="/higiene", status_code=303)


@app.get("/higiene/{auditoria_id}/editar", response_class=HTMLResponse)
async def edit_higiene_form(request: Request, auditoria_id: int, db: Session = Depends(get_db)):
    auditoria = db.query(HigienePersonal).filter(HigienePersonal.id == auditoria_id).first()
    if not auditoria:
        raise HTTPException(status_code=404, detail="Auditoría no encontrada")
    
    return templates.TemplateResponse("higiene/form.html", {
        "request": request,
        "auditoria": auditoria,
        "action": f"/higiene/{auditoria_id}/editar",
        "title": "Editar Auditoría de Higiene",
    })


@app.post("/higiene/{auditoria_id}/editar")
async def update_higiene(
    auditoria_id: int,
    db: Session = Depends(get_db),
    empleado_nombre: str = Form(...),
    empleado_cargo: str = Form(""),
    fecha_auditoria: str = Form(...),
    hora_auditoria: str = Form(...),
    auditor_nombre: str = Form(...),
    auditor_firma: str = Form(""),
    uñas_cortas_limpias: bool = Form(False),
    manos_limpias: bool = Form(False),
    sin_joyas: bool = Form(False),
    uniforme_limpio: bool = Form(False),
    cabello_cubierto: bool = Form(False),
    calzado_adecuado: bool = Form(False),
    sin_lesiones_visibles: bool = Form(False),
    lavado_manos_correcto: bool = Form(False),
    observaciones: str = Form(""),
):
    auditoria = db.query(HigienePersonal).filter(HigienePersonal.id == auditoria_id).first()
    if not auditoria:
        raise HTTPException(status_code=404, detail="Auditoría no encontrada")
    
    criterios = [
        uñas_cortas_limpias, manos_limpias, sin_joyas,
        uniforme_limpio, cabello_cubierto, calzado_adecuado,
        sin_lesiones_visibles, lavado_manos_correcto
    ]
    aprobado = all(criterios)
    
    auditoria.empleado_nombre = empleado_nombre
    auditoria.empleado_cargo = empleado_cargo or None
    auditoria.fecha_auditoria = datetime.strptime(fecha_auditoria, "%Y-%m-%d").date()
    auditoria.hora_auditoria = datetime.strptime(hora_auditoria, "%H:%M").time()
    auditoria.auditor_nombre = auditor_nombre
    auditoria.auditor_firma = auditor_firma or None
    auditoria.uñas_cortas_limpias = uñas_cortas_limpias
    auditoria.manos_limpias = manos_limpias
    auditoria.sin_joyas = sin_joyas
    auditoria.uniforme_limpio = uniforme_limpio
    auditoria.cabello_cubierto = cabello_cubierto
    auditoria.calzado_adecuado = calzado_adecuado
    auditoria.sin_lesiones_visibles = sin_lesiones_visibles
    auditoria.lavado_manos_correcto = lavado_manos_correcto
    auditoria.aprobado = aprobado
    auditoria.observaciones = observaciones or None
    
    db.commit()
    return RedirectResponse(url="/higiene", status_code=303)


# ──────────────────────────────────────────────
# REGISTRO DE TEMPERATURAS - CRUD
# ──────────────────────────────────────────────

@app.get("/temperaturas", response_class=HTMLResponse)
async def list_temperaturas(request: Request, db: Session = Depends(get_db),
                            equipo: str = "", page: int = 1, per_page: int = 30):
    query = db.query(RegistroTemperatura)
    
    if equipo:
        query = query.filter(RegistroTemperatura.equipo_nombre.ilike(f"%{equipo}%"))
    
    total = query.count()
    registros = query.order_by(desc(RegistroTemperatura.fecha_registro)).offset((page - 1) * per_page).limit(per_page).all()
    
    # Equipos únicos para filtro
    equipos = db.query(RegistroTemperatura.equipo_nombre).distinct().all()
    equipos = [e[0] for e in equipos]
    
    # Alertas de hoy
    hoy = date.today()
    alertas_hoy = db.query(RegistroTemperatura).filter(
        RegistroTemperatura.fecha_medicion == hoy,
        RegistroTemperatura.dentro_rango == False
    ).count()
    
    return templates.TemplateResponse("temperaturas/list.html", {
        "request": request,
        "registros": registros,
        "equipos": equipos,
        "equipo_filter": equipo,
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": (total + per_page - 1) // per_page,
        "alertas_hoy": alertas_hoy,
        "today": hoy,
    })


@app.get("/temperaturas/nueva", response_class=HTMLResponse)
async def new_temperatura_form(request: Request, db: Session = Depends(get_db)):
    # Obtener equipos registrados para sugerencia
    equipos = db.query(RegistroTemperatura.equipo_nombre).distinct().all()
    equipos = [e[0] for e in equipos]
    
    return templates.TemplateResponse("temperaturas/form.html", {
        "request": request,
        "registro": None,
        "equipos": equipos,
        "action": "/temperaturas/nueva",
        "title": "Registrar Temperatura",
        "today": date.today().isoformat(),
        "now": datetime.now().time().isoformat()[:5],
    })


@app.post("/temperaturas/nueva")
async def create_temperatura(
    request: Request,
    db: Session = Depends(get_db),
    equipo_nombre: str = Form(...),
    equipo_ubicacion: str = Form(""),
    temperatura: float = Form(...),
    temperatura_objetivo_min: float = Form(0.0),
    temperatura_objetivo_max: float = Form(4.0),
    fecha_medicion: str = Form(...),
    hora_medicion: str = Form(...),
    responsable: str = Form(...),
    responsable_firma: str = Form(""),
    observaciones: str = Form(""),
):
    dentro_rango = temperatura_objetivo_min <= temperatura <= temperatura_objetivo_max
    
    registro = RegistroTemperatura(
        equipo_nombre=equipo_nombre,
        equipo_ubicacion=equipo_ubicacion or None,
        temperatura=temperatura,
        temperatura_objetivo_min=temperatura_objetivo_min,
        temperatura_objetivo_max=temperatura_objetivo_max,
        fecha_medicion=datetime.strptime(fecha_medicion, "%Y-%m-%d").date(),
        hora_medicion=datetime.strptime(hora_medicion, "%H:%M").time(),
        responsable=responsable,
        responsable_firma=responsable_firma or None,
        dentro_rango=dentro_rango,
        observaciones=observaciones or None,
    )
    db.add(registro)
    db.commit()
    return RedirectResponse(url="/temperaturas", status_code=303)


@app.get("/temperaturas/{registro_id}/editar", response_class=HTMLResponse)
async def edit_temperatura_form(request: Request, registro_id: int, db: Session = Depends(get_db)):
    registro = db.query(RegistroTemperatura).filter(RegistroTemperatura.id == registro_id).first()
    if not registro:
        raise HTTPException(status_code=404, detail="Registro no encontrado")
    
    equipos = db.query(RegistroTemperatura.equipo_nombre).distinct().all()
    equipos = [e[0] for e in equipos]
    
    return templates.TemplateResponse("temperaturas/form.html", {
        "request": request,
        "registro": registro,
        "equipos": equipos,
        "action": f"/temperaturas/{registro_id}/editar",
        "title": "Editar Registro de Temperatura",
    })


@app.post("/temperaturas/{registro_id}/editar")
async def update_temperatura(
    registro_id: int,
    db: Session = Depends(get_db),
    equipo_nombre: str = Form(...),
    equipo_ubicacion: str = Form(""),
    temperatura: float = Form(...),
    temperatura_objetivo_min: float = Form(...),
    temperatura_objetivo_max: float = Form(...),
    fecha_medicion: str = Form(...),
    hora_medicion: str = Form(...),
    responsable: str = Form(...),
    responsable_firma: str = Form(""),
    observaciones: str = Form(""),
):
    registro = db.query(RegistroTemperatura).filter(RegistroTemperatura.id == registro_id).first()
    if not registro:
        raise HTTPException(status_code=404, detail="Registro no encontrado")
    
    dentro_rango = temperatura_objetivo_min <= temperatura <= temperatura_objetivo_max
    
    registro.equipo_nombre = equipo_nombre
    registro.equipo_ubicacion = equipo_ubicacion or None
    registro.temperatura = temperatura
    registro.temperatura_objetivo_min = temperatura_objetivo_min
    registro.temperatura_objetivo_max = temperatura_objetivo_max
    registro.fecha_medicion = datetime.strptime(fecha_medicion, "%Y-%m-%d").date()
    registro.hora_medicion = datetime.strptime(hora_medicion, "%H:%M").time()
    registro.responsable = responsable
    registro.responsable_firma = responsable_firma or None
    registro.dentro_rango = dentro_rango
    registro.observaciones = observaciones or None
    
    db.commit()
    return RedirectResponse(url="/temperaturas", status_code=303)


# ──────────────────────────────────────────────
# API ENDPOINTS (para futuras integraciones)
# ──────────────────────────────────────────────

@app.get("/api/stock/critico")
async def api_stock_critico(db: Session = Depends(get_db)):
    """API: Ingredientes con stock bajo mínimo"""
    items = db.query(IngredienteStock).filter(
        IngredienteStock.activo == True,
        IngredienteStock.stock_actual <= IngredienteStock.stock_minimo
    ).all()
    return [{
        "id": i.id,
        "nombre": i.nombre,
        "stock_actual": i.stock_actual,
        "stock_minimo": i.stock_minimo,
        "unidad": i.unidad_medida.value,
        "categoria": i.categoria_obj.nombre if i.categoria_obj else "Sin categoría"
    } for i in items]


@app.get("/api/dashboard/stats")
async def api_dashboard_stats(db: Session = Depends(get_db)):
    """API: Estadísticas del dashboard"""
    return calculate_dashboard_stats(db)


@app.get("/api/temperaturas/alertas")
async def api_temp_alertas(db: Session = Depends(get_db)):
    """API: Temperaturas fuera de rango hoy"""
    hoy = date.today()
    alertas = db.query(RegistroTemperatura).filter(
        RegistroTemperatura.fecha_medicion == hoy,
        RegistroTemperatura.dentro_rango == False
    ).all()
    return [{
        "id": a.id,
        "equipo": a.equipo_nombre,
        "temperatura": a.temperatura,
        "min": a.temperatura_objetivo_min,
        "max": a.temperatura_objetivo_max,
        "hora": a.hora_medicion.isoformat(),
        "responsable": a.responsable
    } for a in alertas]


# ──────────────────────────────────────────────
# HEALTH CHECK
# ──────────────────────────────────────────────

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "ERP Gastronómico", "version": "2.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)