# CORE_ARCHITECTURE.md — El Cerebro Inmortal del ERP Gastronómico

> **⚠️ LECTURA OBLIGATORIA PARA CUALQUIER SESIÓN DE IA**
> Este documento es la memoria persistente del proyecto. **LEERLO COMPLETO ANTES DE TOCAR CÓDIGO.** Si una sesión futura no tiene este contexto, debe leer este archivo primero. Se actualiza al CIERRE de cada fase de desarrollo.
>
> Última actualización: 2026-08-08 (FASE 3 Inventario Físico ✅ COMPLETADA)

---

## 0. MANIFIESTO

### 0.1 Qué es
ERP Gastronómico es un sistema de gestión integral para cocinas profesionales y restaurantes: inventario, compras, mermas, gastos, checklist de apertura/cierre, higiene personal, control de temperaturas de cadena de frío, usuarios con roles, notificaciones Telegram y requerimientos de cierre.

### 0.2 Historia y pivote
- **Origen**: nació como traducción de un MVP en AppSheet ("Templo del Smash") a una app web FastAPI para un solo local.
- **Hito alcanzado**: el MVP se presentó a gerencia con éxito.
- **PIVOTE (2026-08)**: el proyecto ya NO es un script interno para un solo local. El objetivo a 3 meses es **lanzar el ERP como producto SaaS comercial y escalable**, vendiendo suscripciones a distintos restaurantes.
- **Decisiones estratégicas derivadas**:
  - Migrar de SQLite a **PostgreSQL en la nube (Supabase)**.
  - Evolucionar a **arquitectura Multi-Tenant** (tabla `Empresa`/tenants, aislamiento por RLS + `tenant_id`).
  - Introducir **Alembic** como herramienta canónica de migraciones de esquema.
  - Prioridades de ingeniería: **Escalabilidad, Seguridad de Datos (Zero Data Loss), Código Limpio, Multi-Tenancy**.

### 0.3 Metas a 3 meses (roadmap)
1. Cerebro Inmortal (este documento) — hecho.
2. Migración segura a PostgreSQL con cero pérdida de datos.
3. Modelo multi-tenant con aislamiento criptográfico y RLS.
4. Preparar plan de suscripciones (Free/Pro/Enterprise).

---

## 1. STACK TECNOLÓGICO

| Capa | Tecnología | Versión / Notas |
|------|-----------|-----------------|
| Lenguaje | Python | 3.11 (Windows 10, git-bash/MSYS como shell) |
| Backend | FastAPI | 0.109.0 |
| Servidor ASGI | Uvicorn | 0.27.0 (`uvicorn app.main:app --reload --port 8000`) |
| ORM | SQLAlchemy | 2.0.25, estilo clásico `declarative_base()` |
| Templates | Jinja2 | 3.1.3 (SIEMPRE con kwargs: `TemplateResponse(request=..., name=..., context=...)`) |
| CSS | Tailwind CSS | vía CDN (sin build step) |
| JS | Vanilla JS | Menú responsive con hamburguesa, dropdowns, PWA |
| BD actual | SQLite | `sqlite:///./erp_gastronomico_v2.db` |
| BD objetivo | PostgreSQL | Supabase (nube), driver psycopg2 |
| Migraciones | Alembic | A introducir en Fase de migración PG |
| Auth | JWT en cookie httponly | python-jose, bcrypt directo (sin passlib) |
| Notificaciones | Telegram Bot API | httpx async; `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` en `.env` |
| PWA | manifest.json + sw.js | App instalable standalone en móvil |
| Config | python-dotenv | `.env` en raíz del proyecto |

**Variables de entorno críticas** (`.env`): `SECRET_KEY`, `ALGORITHM=HS256`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`. Futuro: `DATABASE_URL` (PG), `DATABASE_URL_SQLITE` (respaldo).

---

## 2. ARQUITECTURA DE CAPAS

```
┌─────────────────────────────────────────────────────────────┐
│  Capa Presentación: templates/ (Jinja2 + Tailwind CDN)      │
│  base.html, dashboard.html, {entidad}/list.html, form.html  │
├─────────────────────────────────────────────────────────────┤
│  Capa Web/Controllers: app/main.py (rutas @app.get/@app.post)│
│  - Reciben Request + Form/Query params                      │
│  - Dependencies: get_db, require_auth, require_admin,       │
│    require_encargado_or_admin                               │
├─────────────────────────────────────────────────────────────┤
│  Capa Servicios (A CREAR en refactor SaaS):                 │
│  - Lógica de negocio fuera de rutas (stock, aprobaciones,   │
│    cálculo de dashboard, notificaciones)                    │
├─────────────────────────────────────────────────────────────┤
│  Capa Datos: app/database.py (SQLAlchemy models + enums)    │
│  - engine, SessionLocal, Base, init_db(), get_db(),         │
│    seed_initial_data()                                      │
├─────────────────────────────────────────────────────────────┤
│  Capa Infra: SQLite (hoy) → PostgreSQL/Supabase (objetivo)  │
└─────────────────────────────────────────────────────────────┘
```

### 2.1 Inicialización
- `app.main` monta FastAPI, Jinja2Templates, `/static`, y en startup llama `init_db()` (crea tablas) + `seed_initial_data(db)` (semilla de desarrollo).

### 2.2 Dependencies clave (patrones)
- `get_current_user(request, db)` — lee cookie `access_token`, decodifica JWT, normaliza `sub` a int, busca usuario activo.
- `require_auth` — exige login; para rutas web lanza `HTTPException(303, headers={"Location": "/login"})`; para `/api/` lanza 401 JSON. **NUNCA `return RedirectResponse` desde una dependency** (no corta el flujo).
- `require_admin` — rol `RolUsuario.ADMINISTRADOR`.
- `require_encargado_or_admin` — rol `ENCARGADO` o `ADMINISTRADOR`.

### 2.3 Context processor global
Middleware HTTP lee la cookie JWT y setea `request.state.current_user`; un wrapper de `TemplateResponse` inyecta `current_user` en el context de TODAS las rutas (sin tocar rutas existentes). `base.html` usa `{% set u = current_user or user %}`.

---

## 3. CATÁLOGO DE BASE DE DATOS (13 MODELOS)

> Motor actual: SQLite. Convenciones: timestamps `created_at`/`updated_at` con `func.now()`, soft delete con `activo`, auditoría con FKs a `usuarios`.

### 3.0 ENUMS (valores EXACTOS — crítico para RBAC en Jinja2)
```python
class RolUsuario(str, enum.Enum):
    ADMINISTRADOR = "Administrador"    # ← valor mixed-case, NO 'ADMINISTRADOR'
    ENCARGADO = "Encargado"
    OPERADOR = "Operador"

class TipoNotificacion(str, enum.Enum):
    TAREA = "Tarea"; ALERTA = "Alerta"; MERMA_PENDIENTE = "Merma Pendiente"; INCIDENCIA = "Incidencia"

class CategoriaIngrediente(str, enum.Enum):
    CARNES="Carnes"; VERDURAS="Verduras"; FRUTAS="Frutas"; LACTEOS="Lácteos";
    GRANOS="Granos y Cereales"; CONDIMENTOS="Condimentos"; BEBIDAS="Bebidas"; OTROS="Otros"

class UnidadMedida(str, enum.Enum):
    KG="kg"; G="g"; L="L"; ML="ml"; UNIDAD="unidad"; CAJA="caja"; BOLSA="bolsa"

class EstadoAprobacion(str, enum.Enum):
    PENDIENTE="Pendiente"; APROBADO="Aprobado"; RECHAZADO="Rechazado"

class TipoGasto(str, enum.Enum):
    SERVICIOS="Servicios"; INSUMOS_NO_ALIMENTICIOS="Insumos No Alimenticios";
    TRANSPORTE="Transporte"; MANTENIMIENTO="Mantenimiento"; OTROS="Otros"

class TipoMerma(str, enum.Enum):
    VENCIMIENTO="Vencimiento"; DAÑO="Daño"; DERRAME="Derrame"; ROBO="Robo"; OTRO="Otro"

class TipoChecklist(str, enum.Enum):
    APERTURA="Apertura"; CIERRE="Cierre"

class Prioridad(str, enum.Enum):
    ALTA="Alta"; MEDIA="Media"; BAJA="Baja"
```

### 3.1 Sucursal — `sucursales`
`id`, `nombre` (unique, index), `direccion`, `activa` (bool, index), `created_at`, `updated_at`. Relación: `usuarios`. → **Futuro**: añadir `empresa_id` FK a `Empresa`.

### 3.2 Usuario — `usuarios`
`id`, `nombre_completo`, `email` (unique, index, login key), `password_hash` (bcrypt), `rol` (SQLEnum RolUsuario, default OPERADOR, index), `sucursal_id` (FK sucursales, nullable), `activo`, `ultimo_acceso`, `created_at`, `updated_at`. Relaciones: sucursal, mermas_registradas, mermas_aprobadas, gastos_registrados, gastos_aprobados, checklists, notificaciones. → **Futuro**: `empresa_id` FK.

### 3.3 Notificacion — `notificaciones`
`id`, `usuario_id` (FK usuarios), `titulo`, `mensaje`, `tipo` (SQLEnum TipoNotificacion), `leida`, `fecha_creacion`, `fecha_lectura`, `entidad_relacionada`, `entidad_id`.

### 3.4 Proveedor — `proveedores`
`id`, `nombre`, `contacto`, `telefono`, `email`, `direccion`, `activo`, `created_at`, `updated_at`. Relación: `compras`.

### 3.5 IngredienteStock — `ingredientes_stock` (tabla maestra de inventario)
`id`, `nombre` (index), `categoria` (SQLEnum), `unidad_medida` (SQLEnum), `stock_actual` (Float), `stock_minimo` (Float), `stock_maximo` (Float), `costo_unitario`, `costo_promedio`, `dias_alerta_vencimiento`, `activo`, `created_at`, `updated_at`. Properties: `necesita_reposicion`, `valor_stock`. Relaciones: detalles_compra, mermas. → Consolidado global (sin sucursal).

### 3.6 RegistroCompra — `registro_compras` (cabecera, PADRE)
`id`, `numero_factura` (unique), `proveedor_id` (FK), `fecha_compra`, `fecha_registro`, `subtotal`, `iva`, `total`, `foto_recibo`, `observaciones`, `estado` (SQLEnum EstadoAprobacion, default PENDIENTE), `creado_por_usuario_id` (FK), `aprobado_por_usuario_id` (FK), `fecha_aprobacion`. Relación: `detalles` (cascade all, delete-orphan).

### 3.7 DetalleCompra — `detalle_compras` (hijo)
`id`, `compra_id` (FK, ondelete CASCADE), `ingrediente_id` (FK), `cantidad`, `costo_unitario`, `costo_total` (= cantidad × costo_unitario), `fecha_vencimiento`, `lote`, `observaciones`.

### 3.8 RegistroMerma — `registro_mermas`
`id`, `ingrediente_id` (FK), `tipo` (SQLEnum TipoMerma), `cantidad`, `valor_perdida` (= cantidad × costo_promedio), `fecha_merma`, `fecha_registro`, `responsable_usuario_id` (FK, index), `observaciones`, `foto_evidencia`, `estado`, `aprobado_por_usuario_id` (FK), `fecha_aprobacion`.

### 3.9 ControlGasto — `control_gastos`
`id`, `tipo` (SQLEnum TipoGasto), `descripcion`, `monto`, `fecha_gasto`, `fecha_registro`, `proveedor` (texto libre), `numero_comprobante`, `foto_comprobante`, `estado`, `responsable_usuario_id` (FK, index), `aprobado_por_usuario_id` (FK), `fecha_aprobacion`, `observaciones`.

### 3.10 ListaVerificacionDiario — `lista_verificacion_diario`
`id`, `tipo` (SQLEnum TipoChecklist: APERTURA/CIERRE), `fecha` (index), `hora_registro`, `fecha_hora_completa`, `responsable_usuario_id` (FK, index), `responsable_firma` (Base64), checklist booleans: `cocina_limpia`, `cocina_ordenada`, `basureros_vacios`, `equipos_funcionando`, `temperaturas_ok`, `extintores_ok`, `uniformes_limpios`, `manos_lavadas`, `cabello_cubierto`, `almacen_ordenado`, `sin_plagas`, `fecha_vencimiento_revisada`, `observaciones`, `foto_evidencia`.

### 3.11 HigienePersonal — `higiene_personal`
`id`, `empleado_nombre`, `empleado_cargo`, `fecha_auditoria` (index), `hora_auditoria`, `fecha_registro`, `auditor_nombre`, `auditor_firma` (Base64), criterios: `uñas_cortas_limpias`, `manos_limpias`, `sin_joyas`, `uniforme_limpio`, `cabello_cubierto`, `calzado_adecuado`, `sin_lesiones_visibles`, `lavado_manos_correcto`, `aprobado`, `observaciones`, `foto_evidencia`. Property: `puntuacion`.

### 3.12 RegistroTemperatura — `registro_temperaturas`
`id`, `equipo_nombre`, `equipo_ubicacion`, `temperatura`, `temperatura_objetivo_min`, `temperatura_objetivo_max`, `fecha_medicion` (index), `hora_medicion`, `fecha_registro` (index), `responsable` (texto), `responsable_firma`, `dentro_rango` (auto), `observaciones`, `foto_evidencia`. Property: `esta_en_rango`.

### 3.13 Requerimientos — `requerimientos` (MÓDULO NUEVO, Fase 2)
`id`, `producto` (String, ahora alimentado por `<select>` desde inventario), `cantidad` (Float), `precio_estimado` (Float), `prioridad` (SQLEnum Prioridad), `sucursal_id` (FK sucursales), `fecha_registro` (DateTime default now). Relación: `sucursal`. Rutas: GET (lista + total_proyectado = Σ cantidad×precio_estimado) y POST (crea + alerta Telegram) en `/requerimientos`.

---

## 4. RBAC Y MATRIZ DE PERMISOS

### 4.1 Roles (valores EXACTOS del enum)
- **Administrador** ("Administrador") — Socios/Superusuarios: acceso total, multi-sucursal, Finanzas, Configuración, crea requerimientos.
- **Encargado** ("Encargado") — Jefes de cocina: gestión operativa + aprobación (compras/mermas/gastos), ve Finanzas.
- **Operador** ("Operador") — Trabajadores: registro de datos.

### 4.2 Reglas de visibilidad (base.html, SIEMPRE con `.value` mixed-case)
```jinja2
{% if u and u.rol.value in ['Administrador', 'Encargado'] %}  {# Finanzas #}
{% if u and u.rol.value == 'Administrador' %}                 {# Configuración, filtro multi-sucursal #}
```

### 4.3 Protección en rutas (dependencies)
| Recurso | Dependency |
|---------|-----------|
| `/` dashboard, todos los módulos | `require_auth` |
| `/usuarios` (+ toggle), filtro multi-sucursal | `require_admin` |
| `/compras/*/aprobar`, `/mermas/*/aprobar`, `/gastos/*/aprobar` | `require_encargado_or_admin` |
| `/requerimientos` GET/POST | `require_encargado_or_admin` |

### 4.4 Futuro SaaS
Nuevo rol **SuperAdmin** (plataforma, gestiona tenants) vs. **Administrador** (tenant). Matriz por plan de suscripción.

---

## 5. REGLAS DE DISEÑO (CONVENCIONES)

> ### ⚜️ REGLA DE ORO: INYECTAR / PARCHEAR, NUNCA REESCRIBIR
> **Prohibido reescribir archivos enteros** (`app/main.py`, templates) desde cero. Todo cambio es una **adición** (append), una **inyección** (nuevo bloque), o un **patch quirúrgico** (línea específica). Razón: el código heredado tiene lógica frágil (RBAC, auth, context processor) y una reescritura introduce regresiones silenciosas. Los fixes se hacen con `patch` (old_string → new_string) o scripts AST que solo reescriben el patrón objetivo.

### 5.1 Convenciones obligatorias
1. **TemplateResponse SIEMPRE con kwargs**: `templates.TemplateResponse(request=request, name="x.html", context={...})`. Nunca posicional (Starlette ≥0.29 rompe con dict posicional).
2. **Dependencies de auth**: lanzar `HTTPException(303, headers={"Location": "/login"})` — NUNCA `return RedirectResponse` (no corta flujo).
3. **JWT**: `sub` SIEMPRE `str(user.id)` (RFC 7519). Cookie httponly guarda SOLO el JWT, sin prefijo `Bearer ` (Starlette envuelve en comillas los valores con espacio).
4. **Password hashing**: bcrypt directo (`hashpw`/`gensalt`/`checkpw`). Prohibido passlib (roto con bcrypt ≥4.0).
5. **Enums**: valores mixed-case human-readable; comparaciones con `.value` y el valor EXACTO.
6. **Multi-sucursal**: las tablas transaccionales NO tienen sucursal_id — se filtran vía subquery sobre `Usuario.sucursal_id` usando `.scalar_subquery()` en `.in_()` (nunca `.subquery()`).
7. **Timestamps**: `created_at` (default now), `updated_at` (onupdate now). **Soft delete**: `activo` bool. **Auditoría**: FKs `creado_por`/`aprobado_por` + `fecha_aprobacion` en transaccionales.
8. **Money**: usar Float hoy; en PG migrar a `Numeric(10,2)`.
9. **Sin SQL crudo**: todo vía SQLAlchemy ORM. Sync DB en async endpoints solo vía dependency `get_db`.
10. **Backup antes de modificar**: `.bak` + anti-script de reversión para operaciones destructivas.

### 5.2 Anti-patrones a evitar
- ❌ Lógica de negocio en templates (usar properties/filtros).
- ❌ Reescribir `main.py` completo. ❌ Hardcodear URLs. ❌ Olvidar cascade en padre-hijo. ❌ Ignorar `IntegrityError` en unique constraints.

---

## 6. PITFALLS CRÍTICOS (MURO DE LOS LAMENTOS)

Cada uno con síntoma → causa → fix. **NO repetir.**

| # | Bug | Síntoma | Fix |
|---|-----|---------|-----|
| 1 | passlib + bcrypt ≥4.0 | `AttributeError: 'bcrypt' has no attribute '__about__'`, luego "password cannot be longer than 72 bytes" | Usar bcrypt directo; abandonar passlib |
| 2 | JWT `sub` int | Bucle de redirect `/login ↔ /` (excepción tragada) | `sub: str(user.id)`; normalizar a int en `get_current_user` |
| 3 | Cookie con `Bearer ` | Cookie envuelta en comillas; `startswith("Bearer ")` falla | Guardar solo el JWT en la cookie; limpiar defensivamente si hay legado |
| 4 | `return RedirectResponse` en dependency | `AttributeError: 'RedirectResponse' object has no attribute 'id'` (500) | `raise HTTPException(303, headers={"Location": "/login"})` |
| 5 | Enum mixed-case vs Jinja2 uppercase | Menú Admin invisible sin errores en log | Comparar con `.value` y valor exacto ('Administrador', no 'ADMINISTRADOR') |
| 6 | `current_user` ausente del context | Menú RBAC desaparece en rutas que no pasan `user` | Context processor global (middleware + wrapper TemplateResponse) |
| 7 | `.subquery()` en `.in_()` | SAWarning silencioso | `.scalar_subquery()` |
| 8 | `TemplateResponse` posicional | `TypeError: unhashable type 'dict'` | kwargs siempre; migración masiva con script AST |
| 9 | Menú/rutas drift | 404 silencioso en módulos del menú | Script `verify-global.py` (links base.html vs @app.get) |
| 10 | Scripting estático greedy (re.DOTALL) | Falsos negativos en verificación | Extracción línea por línea por indentación |

---

## 7. MULTI-TENANCY (DISEÑO OBJETIVO)

### 7.1 Decisión de aislamiento: **Shared schema + tenant_id + RLS**
- ❌ BD por tenant (caro, migraciones ×N) — descartado.
- ⏸️ Schema por tenant (PG native) — opcional futuro.
- ✅ **Shared schema + `empresa_id` en todas las tablas + Row-Level Security (RLS) de PostgreSQL** — defensa en profundidad: filtro a nivel de app (rápido) + garantía a nivel de motor (seguro aunque la app tenga un bug).

### 7.2 Modelo de datos objetivo
**Nueva tabla `Empresa` (Tenant)** — `empresas`:
`id`, `nombre`, `slug` (subdominio `restaurante1.tudominio.com`, unique), `plan` (enum: Free/Pro/Enterprise), `estado` (activo/suspendido/prueba), `settings` (JSONB), `fecha_alta`, `fecha_baja`, `created_at`, `updated_at`.

**Propagación de `empresa_id`**:
- `Sucursal.empresa_id` FK → sucursales pertenecen a una Empresa.
- `Usuario.empresa_id` FK (además de sucursal_id).
- Tablas transaccionales (Compras, DetalleCompra, Mermas, Gastos, Checklist, Higiene, Temperaturas, Requerimientos, Notificaciones): **denormalizar `empresa_id`** en las de acceso frecuente para filtrado barato; consistencia vía triggers o capa de servicios.
- Maestras sin sucursal hoy (IngredienteStock): ganan `empresa_id` — el inventario pasa a ser por-tenant (cada restaurante tiene SU inventario).

**Filtrado global automático (SQLAlchemy 2.0)**: listener de eventos `do_orm_execute` que inyecta `WHERE empresa_id = :tenant_actual` en todas las queries — sin tocar las rutas existentes.

### 7.3 Aislamiento criptográfico
1. **RLS de PostgreSQL**: políticas `USING (empresa_id = current_setting('app.tenant_id'))` — garantía de motor.
2. **TLS** en tránsito (Supabase gratis). 3. **Cifrado en reposo** (TDE + backups cifrados).
4. **Cifrado a nivel de columna** (pgcrypto, AES-256-GCM) para datos sensibles (facturas, documentos), con **claves por tenant** (KEK/DEK) — aislamiento criptográfico real.
5. **Resolución de tenant**: middleware lee subdominio → `request.state.tenant` → JWT lleva `empresa_id`.

### 7.4 Migración incremental
- **A**: crear `Empresa` + columnas `empresa_id` NULLABLE en todas las tablas (Alembic).
- **B**: crear empresa raíz (local actual) + backfill `empresa_id`.
- **C**: NOT NULL + índices compuestos `(empresa_id, ...)`.
- **D**: activar RLS + políticas. **E**: middleware tenant + filtro global. **F**: rol SuperAdmin.

---

## 8. OPERACIÓN Y VERIFICACIÓN

### 8.1 Levantar el sistema
```bash
cd "C:\Users\hola\Documents\Mi segundo Cerebro\Nuevo proyecto ERP"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
# Login dev: admin@erp.cl / 123456
```

### 8.2 Scripts de verificación reutilizables
- `scripts/verify-global.py` — 47 checks: TemplateResponse kwargs, rutas vs menú (404), PWA, TestClient autenticado recorre el menú.
- `scripts/verify-redirect-fix.py` — 17 checks de los bugs JWT/redirect (TestClient + ast.parse, sin red).
- `scripts/fix-templateresponse.py` — migración masiva AST de TemplateResponse posicional → kwargs (dry-run safe).

### 8.3 Protocolo de seguridad (obligatorio)
1. **Respaldo previo**: `.bak` antes de modificar cualquier archivo existente.
2. **Anti-script**: toda acción destructiva tiene su reversión exacta.
3. **Freno de mano**: eliminación masiva/formateo → pedir confirmación explícita (Y/N).
4. **Rollback DB**: `DATABASE_URL` en `.env` — revertir = cambiar variable.

### 8.4 Control de versiones
Repositorio Git local (pendiente de conectar remoto). Commits por fase. Este archivo se versiona con el repo.

---

## 9. REGISTRO DE DECISIONES (ADR)

| Fecha | Decisión | Contexto | Consecuencias |
|-------|----------|----------|---------------|
| 2026-08-06 | **Pivote a SaaS comercial** | MVP aprobado por gerencia | Priorizar escalabilidad, seguridad, multi-tenancy |
| 2026-08-06 | **Migrar a PostgreSQL (Supabase)** | SQLite insuficiente para SaaS | Introducir Alembic; `DATABASE_URL` en `.env`; cero cambios en rutas |
| 2026-08-06 | **Multi-tenant: shared schema + RLS** | Vender ERP a múltiples restaurantes | Tabla `Empresa`; `empresa_id` global; listener `do_orm_execute`; pgcrypto para datos sensibles |
| 2026-08-06 | **Crear CORE_ARCHITECTURE.md** | Memoria persistente ante sesiones de IA | Lectura obligatoria; actualizar al cierre de cada fase |
| 2026-08-06 | **Módulo Requerimientos con alerta Telegram** | Necesidad operativa de cierre | Modelo + GET/POST + select dinámico de inventario |
| 2026-08-06 | **✅ MIGRACIÓN SQLite → PostgreSQL COMPLETADA** | Fase 0 cerrada: entorno reparado (venv con jose/httpx/bcrypt), Supabase conectado | **Zero Data Loss: 22 filas migradas** (2 sucursales, 6 usuarios, 4 proveedores, 8 ingredientes, 2 notificaciones) vía `migrate_data_to_pg.py` (preserva IDs, orden topológico, setval). Sistema operando en `ENVIRONMENT=production` con PostgreSQL 17.6. Alembic en `head` (`503d5a1c2297`) |
| 2026-08-06 | **📐 FASE 1 SAAS: Multi-Tenant (Empresa + tenant_id + RLS)** | Producto comercial para múltiples restaurantes | Diseño aprobado: tabla `Empresas`, columna `empresa_id` en todas las tablas, listener `do_orm_execute` para filtrado automático sin reescribir rutas, RLS de PostgreSQL como garantía de aislamiento |
| 2026-08-06 | **✅ FASE 1 COMPLETADA — Aislamiento Multi-Tenant Activo** | Pasos 1-5 ejecutados y verificados (18/18 checks) | **Modelos**: `Empresa` + `TenantMixin` en 13 tablas. **Migración**: `a006e679678a` (3 fases, idempotente, 22 filas → empresa 1). **Contexto**: `tenant_context` (ContextVar) inyectado desde JWT en `get_current_user`, middleware resetea por request. **Listener**: `before_compile` sobre `Query` (SELECT incluido count()), monkey‑patch `Query.count()`, `do_orm_execute` sobre `Session` (UPDATE/DELETE), `before_flush` (INSERT auto). **RLS**: migración `225d1158bcb6` — 13 políticas activas con fallback permisivo. **Funcional**: tenant=999 → count=0, all=0, first=None. |
| 2026-08-06 | **📐 FASE 2 COMERCIAL: Panel Master + Branding Dinámico** | SaaS listo para ventas; se necesita: (A) interfaz exclusiva del dueño del SaaS, (B) white-label dinámico | Diseño aprobado: rol `SUPER_ADMIN` global + endpoint `/saas-master` que evade el listener; tabla `Empresas` extiende con branding (`logo_url`, `nombre_comercial`, `color_primario`) + context processor global Jinja2 |
| 2026-08-07 | **✅ FASE 3 (Blueprint F4): INVENTARIO FÍSICO COMPLETADO** | 4 modelos nuevos con aislamiento multi-tenant: `PlantillaInventario`, `ConteoFisico`, `ItemConteo`, `AjusteInventario` | **Modelos**: heredan `TenantMixin` → `empresa_id` automático + RLS. **Enum**: `EstadoConteo` (Borrador, En_Conteo, Revision, Cerrado). **Migración**: `4da61f207883_fase_3_inventario` — 4 tablas creadas en SQLite/PostgreSQL con FKs correctas. **Verificado**: tablas existen en `erp_gastronomico_v2.db` con índices y constraints. |

---

## 10. ROADMAESTRO DE DESARROLLO (ACTUALIZADO 2026-08-08)

> Roadmap consolidado que integra módulos heredados del blueprint AppSheet + Game Changers aprobados.
> **Decisiones del propietario (2026-08-08):**
> - ✅ **Integrar al roadmap activo:** GC-3 (Bot Telegram), GC-4 (Food Cost en Vivo), GC-2 (Receta con Costo Vivo)
> - ⏸️ **Diferir (aislar para después):** GC-1 (Reposición Predictiva IA), GC-5 (Academia con Certificaciones) — se desarrollarán cuando el mapa base esté completo.

### 10.1 Fases Ejecutadas (Completadas)

| Fase | Descripción | Estado | ADR |
|------|-------------|--------|-----|
| Fase 0 | Migración SQLite → PostgreSQL (Supabase) | ✅ Completada | Zero Data Loss: 22 filas |
| Fase 1 | Multi-Tenant (Empresa + tenant_id + RLS) | ✅ Completada | 13 tablas con aislamiento |
| Fase 2 | Panel Master + Branding Dinámico | ✅ Completada | SuperAdmin + white-label |
| Fase 3 | Inventario Físico (blueprint AppSheet F3) | ✅ Completada | 4 modelos nuevos (2026-08-07) |

**✅ FASE 3 SELLADA (2026-08-08):** Modelos `PlantillaInventario`, `ConteoFisico`, `ItemConteo`, `AjusteInventario` + enum `EstadoConteo` integrados con `TenantMixin` y RLS. 8 endpoints FastAPI protegidos (`require_encargado_or_admin`/`require_admin`). 4 vistas Jinja2+Tailwind (`inventario_fisico.html`, `_nuevo.html`, `_detalle.html`, `_plantillas.html`) operativas. Menú integrado en `base.html` (dropdown Inventario). Migración Alembic `4da61f207883_fase_3_inventario` aplicada en PostgreSQL (producción) y SQLite (desarrollo). Listo para producción.

### 10.2 Roadmap Activo (A Desarrollar — En Orden)

| Orden | Fase | Módulo | Origen | Modelos nuevos | Config | Tests | Complejidad |
|-------|------|--------|--------|-----------------|--------|-------|-------------|
| **1** | Fase 4 | **Mermas 2.0** (extender) | Blueprint F2 | 0 (ampliar existente) | — | 20 | Media |
| **2** | Fase 5 | **Transferencias entre sucursales** | Blueprint F4 | 3 (OrdenTransferencia, ItemTransferencia, RecepcionTransferencia) | CFG_013, CFG_014 | 22 | Media |
| **3** | Fase 6 | **Recetas + Costos + Producción** + ⭐ **GC-2: Receta con Costo Vivo** | Blueprint F5 + Game Changer | 5 (Receta, RecetaIngrediente, HistorialCosto, Produccion, ProduccionDetalle) | CFG_015–018 | 25 | Media |
| **4** | Fase 7 | **Tareas + KPIs + Incidencias** | Blueprint F6 | 8 (Tarea, ProgramacionTarea, EjecucionTarea, KPI, RegistroKPI, Meta, Incidencia, SeguimientoIncidencia, CategoriaIncidencia) | CFG_019–025 | 28 | Media |
| **5** | Fase GC-A | ⭐ **GC-3: Bot Telegram Operacional** | Game Changer | 0 (usa infraestructura existente) | — | — | **Baja** |
| **6** | Fase GC-B | ⭐ **GC-4: Food Cost en Vivo** | Game Changer | 0 (dashboard sobre modelos existentes) | — | — | Media |

### 10.3 Roadmap Diferido (Aislado — Post-Mapa Completo)

> **Política:** Estas funcionalidades EXISTEN en el radar pero NO se desarrollarán hasta que el roadmap activo (10.2) esté 100% completo.

| # | Propuesta | Descripción | Condición de activación |
|---|---------|-------------|------------------------|
| GC-1 | **Reposición Predictiva con IA** | Análisis de histórico para predecir agotamiento y sugerir órdenes de compra | requiere 3+ meses de datos de compras + mermas acumulados |
| GC-5 | **Academia con Certificaciones** | Capacitación obligatoria con vencimiento + bloqueo de acceso por cert caducada | requiere módulo de usuarios + RBAC evolucionado maduro |

### 10.4 Backlog Original (Mantenido como Referencia)

| Prioridad | Área | Descripción |
|-----------|------|-------------|
| 1 | Core SaaS y UI | Vistas SuperAdmin, editor de paneles/branding, plantillas de vistas |
| 2 | Alertas | Avisos, Alertas, Urgentes |
| 3 | RBAC Evolucionado | SuperAdmin, Administrador, Encargado, Operador de Cocina |
| 4 | Módulo "Academia" | Entrenamientos, cursos (ej. Manipulación de alimentos) → ver GC-5 diferido |
| 5 | Operaciones Avanzadas | EjecucionesChecklist (Completada/Pendiente/No conforme), Evidencias (fotos), Incidencias |

---

## 11. BLUEPRINT FUNCIONAL HEREDADO DE APPSHEET (Entregas_Hermes/README_MAESTRO.md)

> **Fuente:** `C:\Users\hola\Documents\Mi segundo Cerebro\Entregas_Hermes\` — 6 fases planificadas el 2026-07-30 para AppSheet, pre-pivote.
> **Estado:** Los artefactos AppSheet (Actions/Bots/Views JSON, Security Filters) NO aplican a FastAPI. Pero la **especificación funcional** (qué módulos, tablas, flujos de estado, dependencias y tests de aceptación) SÍ es el blueprint de construcción para nuestro SaaS.
> **Ubicación de artefactos:** `Entregas_Hermes/Fase{N}_*/` — CSVs de tablas y checklists de validación consultables como referencia.

### 11.1 Módulos pendientes que NO existen en FastAPI (extraídos del blueprint AppSheet)

| Fase origen | Módulo | Modelos/tablas a crear en FastAPI | Flujo de estados | Dependencias |
|-------------|--------|-----------------------------------|------------------|--------------|
| **F2** | Mermas 2.0 (extender modelo actual) | `RegistroMerma` + columnas: `estado` (Borrador→Pendiente→En revisión→Aprobada→Rechazada→Corrección→Anulada), `valor_anterior`, `correccion_motivo`, `correccion_responsable_id` | Operador reporta → Encargado revisa → Admin resuelve | `IngredienteStock` (existente), `Usuario` (existente) |
| **F3** | Inventario Físico (conteos) | `PlantillaInventario`, `ConteoInventario`, `ItemConteo`, `AjusteInventario` | Pendiente→En curso→Completado→Aprobado→Rechazado | `IngredienteStock` (existente), `Usuario` (existente) |
| **F4** | Transferencias entre sucursales | `OrdenTransferencia`, `ItemTransferencia`, `RecepcionTransferencia` | Borrador→Solicitada→Aprobada→En preparación→Despachada→Recibida con diferencias→Recibida completa→Cancelada | `IngredienteStock` (existente), `Sucursal` (existente) |
| **F5** | Recetas y Costos | `Receta`, `RecetaIngrediente`, `HistorialCosto`, `Produccion`, `ProduccionDetalle` | Receta: Borrador→Vigente→Deprecated. Producción: Planificada→En curso→Completada→Cancelada | `IngredienteStock` (existente), `RegistroMerma` (F2) |
| **F5** | Producción | `Produccion`, `ProduccionDetalle` | Planificada→En curso→Completada→Cancelada | `Receta` (F5), `IngredienteStock` (existente) |
| **F6** | Tareas y Requerimientos (extender) | `Tarea`, `ProgramacionTarea`, `EjecucionTarea` | Asignada→En curso→Completada→Vencida→Cancelada | `Usuario` (existente), `Sucursal` (existente) |
| **F6** | KPIs y Metas | `KPI`, `RegistroKPI`, `Meta` | Evaluación: Encargado evalúa→Admin revisa | `Usuario` (existente), `RolUsuario` (existente) |
| **F6** | Capacitación (Academia) | `Curso`, `Leccion`, `CapacitacionUsuario`, `Certificacion` | Asignada→En progreso→Completada→Vencida | `Usuario` (existente) |
| **F6** | Incidencias | `Incidencia`, `SeguimientoIncidencia`, `CategoriaIncidencia` | Abierta→Asignada→En resolución→Resuelta→Cerrada→Escalada | `Usuario` (existente), `Sucursal` (existente) |

### 11.2 Configuraciones globales del blueprint (a migrar como tabla `Configuracion`)

| Código | Parámetro | Valor por defecto | Módulo |
|---------|-----------|-------------------|--------|
| CFG_010 | Frecuencia inventario por defecto | Diario | Inventario Físico |
| CFG_011 | Productos críticos conteo obligatorio | true | Inventario Físico |
| CFG_012 | Tolerancia % conteo vs stock | 5% | Inventario Físico |
| CFG_013 | Aprobación requerida transferencia | true | Transferencias |
| CFG_014 | Notificar diferencias recepción | true | Transferencias |
| CFG_015 | Recalcular costos recetas al cambiar precio | true | Recetas/Costos |
| CFG_016 | Variación costo alerta % | 15% | Recetas/Costos |
| CFG_017 | Rendimiento default receta | 1.0 | Recetas/Costos |
| CFG_018 | Producción planificada requiere receta | true | Producción |
| CFG_019 | SLA tarea vencida (horas) | 24 | Tareas |
| CFG_020 | KPI frecuencia evaluación | Mensual | KPIs |
| CFG_021 | Capacitación vencimiento alerta (días) | 30 | Capacitación |
| CFG_022 | Incidencia gravedad crítica escalamiento auto | true | Incidencias |
| CFG_023 | Incidencia SLA crítica (horas) | 4 | Incidencias |
| CFG_024 | Notificar push tareas nuevas | true | Tareas |
| CFG_025 | Recordatorio inventario pendiente (horas) | 2 | Inventario Físico |

### 11.3 Tests de aceptación heredados (128 casos)

> Ubicación original: `Entregas_Hermes/Fase{N}_*/08_Checklist_Validacion_*.md`
> **Uso:** Cada checklist define casos de prueba end-to-end por módulo. Al implementar cada módulo en FastAPI, ejecutar los tests correspondientes como validación de aceptación.

| Fase | Casos | Cobertura |
|------|-------|-----------|
| F1 Fundaciones | 15 | Multi-sucursal, roles, auditoría, offline |
| F2 Mermas 2.0 | 20 | Flujo estados, stock, merma auto, notificaciones |
| F3 Inventario Físico | 25 | Plantillas, conteos, tolerancias, ajustes |
| F4 Transferencias | 22 | Origen→Destino, stock dual, recepción diffs |
| F5 Recetas + Costos | 25 | BOM, costeo, versionado, producción real vs teórico |
| F6 Tareas + KPIs + Cap + Inc | 28 | Ciclo tareas, KPIs, capacitación, incidencias, integración total |
| **TOTAL** | **135** | Cobertura funcional completa del ERP |

### 11.4 Dependencias entre fases (orden de construcción en FastAPI)

```
FASE 1 (EXISTENTE)          FASE 2 (EXISTENTE)         FASE COMERCIAL (EXISTENTE)
├── 13 modelos base          ├── Multi-tenant          ├── Panel SuperAdmin
├── RBAC (3 roles)           ├── RLS PostgreSQL         ├── Branding dinámico
├── JWT + bcrypt             ├── Alembic head           └── Onboarding empresas
├── PWA                      └── Supabase prod
│
▼
FASE 3: MERMAS 2.0 (EXTENDER)
├── Ampliar RegistroMerma con estados y flujo aprobación
├── Historial de correcciones
├── Evidencia fotográfica (Supabase Storage)
└── Tests: 20 casos (F2)
│
▼
FASE 4: INVENTARIO FÍSICO
├── 4 modelos nuevos (PlantillaInventario, ConteoInventario, ItemConteo, AjusteInventario)
├── Configuración CFG_010, CFG_011, CFG_012
├── Tolerancias y alertas
└── Tests: 25 casos (F3)
│
▼
FASE 5: TRANSFERENCIAS
├── 3 modelos nuevos (OrdenTransferencia, ItemTransferencia, RecepcionTransferencia)
├── Configuración CFG_013, CFG_014
├── Stock dual (origen y destino)
└── Tests: 22 casos (F4)
│
▼
FASE 6: RECETAS + COSTOS + PRODUCCIÓN
├── 5 modelos nuevos (Receta, RecetaIngrediente, HistorialCosto, Produccion, ProduccionDetalle)
├── Configuración CFG_015 al CFG_018
├── Recálculo automático de costos
├── Producción real vs teórico
└── Tests: 25 casos (F5)
│
▼
FASE 7: TAREAS + KPIs + CAPACITACIÓN + INCIDENCIAS
├── 8 modelos nuevos (Tarea, ProgramacionTarea, EjecucionTarea, KPI, RegistroKPI, Meta, Curso, Certificacion, Incidencia, SeguimientoIncidencia, CategoriaIncidencia)
├── Configuración CFG_019 al CFG_025
├── SLA, escalamiento, vencimientos
├── Dashboards por rol (Admin/Encargado/Operador)
└── Tests: 28 casos (F6)
```

**REGLA DE ORO: No saltar fases. Cada fase valida la anterior antes de continuar.**

### 11.5 Game Changers — Estado de Aprobación (2026-08-08)

> **Decisión del propietario:** 3 aprobados para desarrollo activo, 2 diferidos.

#### ✅ Game Changers Aprobados (Integrados al Roadmap Activo — Sección 10.2)

| # | Módulo | Descripción | Impacto | Fase | Estado |
|---|--------|-------------|---------|------|--------|
| GC-2 | **Receta con Costo Vivo** | Receta con foto del plato + costo recalculado automáticamente al cambiar precio de insumo | Control de margen por plato | Fase 6 (integrado con Recetas) | 📐 Diseñado |
| GC-3 | **Bot Telegram Operacional** | Alertas críticas (stock, merma, incidencia, temperatura) + aprobación de mermas desde Telegram | Velocidad de decisión sin abrir app | Fase GC-A (post-Fase 7) | 📐 Diseñado |
| GC-4 | **Food Cost en Vivo** | KPI diario que cruza inventario + compras + mermas + producción para mostrar costo real por plato en tiempo real | Margen financiero controlable | Fase GC-B (post-Bot Telegram) | 📐 Diseñado |

#### ⏸️ Game Changers Diferidos (Aislados — Sección 10.3)

> **Política:** Existen en el radar pero NO se desarrollan hasta que el roadmap activo esté 100% completo.

| # | Módulo | Descripción | Impacto | Condición de activación | Estado |
|---|--------|-------------|---------|------------------------|--------|
| GC-1 | **Reposición Predictiva con IA** | Análisis de histórico para predecir agotamiento y sugerir órdenes de compra | Reduce quiebres de stock | 3+ meses de datos acumulados | ⏸️ Congelado |
| GC-5 | **Academia con Certificaciones** | Capacitación obligatoria con vencimiento + bloqueo de acceso por certificación caducada | Cumplimiento SAG/fiscalización | RBAC maduro + mapa base completo | ⏸️ Congelado |

---

*Próxima sesión: continuar desde este backlog priorizado. Orden sugerido: Fase 3 (Mermas 2.0) → Fase 4 (Inventario Físico) → Fase 5 (Transferencias).*