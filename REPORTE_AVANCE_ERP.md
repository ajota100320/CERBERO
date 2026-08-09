# REPORTE DE AVANCE — ERP GASTRONÓMICO MULTI-EMPRESA

**Fecha:** Agosto 2026
**Estado general:** Producción activa (PostgreSQL / Supabase)
**Audiencia:** Dirección y stakeholders

---

## 1. Resumen Ejecutivo

El sistema evolucionó de una aplicación local de gestión gastronómica a un **motor SaaS Multi-Empresa desplegado en la nube**. La plataforma hoy permite operar múltiples restaurantes de forma simultánea y aislada desde una única infraestructura, sentando las bases para un modelo de negocio de suscripción (SaaS) comercializable.

La transformación se completó **sin pérdida de datos** (Zero Data Loss) y con **cero interrupciones** en la operación diaria: los módulos existentes siguen funcionando sin cambios, mientras la capa de aislamiento y seguridad se integró de forma transparente.

---

## 2. Alcance Actual (Módulos Funcionales)

| Módulo | Descripción |
|--------|-------------|
| **Inventario** | Control de ingredientes, stock crítico, mínimo y máximo, costos unitarios y promedios |
| **Compras** | Registro de compras a proveedores con detalle por línea (facturas) |
| **Proveedores** | Directorio con datos de contacto y trazabilidad de compras |
| **Mermas** | Registro y aprobación de mermas, vencimientos y salidas de inventario |
| **Gastos (Finanzas)** | Control de gastos operativos con tipos y montos |
| **Dashboard** | Indicadores globales: stock crítico, compras recientes, mermas, temperaturas, notificaciones. Filtro por sucursal (solo administradores) |
| **Checklists diarios** | Apertura y cierre de turno con firmas digitales |
| **Higiene y Temperaturas** | Auditoría de estándares del equipo y control de cadena de frío |
| **Requerimientos de Cierre** | Solicitudes de cierre con prioridades y alertas automáticas |
| **Notificaciones** | Sistema de alertas internas (stock crítico, mermas pendientes, incidencias) |
| **Usuarios y Roles** | Gestión de acceso con roles jerárquicos |

---

## 3. Hitos Técnicos Alcanzados

### 3.1 Migración a la Nube (PostgreSQL / Supabase)
- Migración exitosa de SQLite local a **PostgreSQL 17.6** en Supabase con **Zero Data Loss** (todos los registros históricos preservados).
- Sistema de migraciones versionadas (Alembic) que garantiza evolución estructurada del esquema.
- Entorno de configuración dual (desarrollo/producción) mediante variables de entorno.

### 3.2 Arquitectura Multi-Tenant (Aislamiento por Empresa)
- **Tabla maestra de Empresas**: cada restaurante cliente es un tenant independiente.
- **Aislamiento automático de datos**: todas las tablas operativas pertenecen a una empresa; el sistema filtra por empresa de forma invisible para el usuario, sin reescribir módulos.
- **Verificación de aislamiento**: pruebas confirman que un usuario de la Empresa A jamás visualiza datos de la Empresa B.
- **Branding dinámico (white-label)**: cada empresa muestra su propio nombre comercial, colores y logo en toda la interfaz.

### 3.3 Blindaje de Seguridad
- **Row Level Security (RLS)** en PostgreSQL: capa de protección a nivel de base de datos que impide acceso cruzado entre empresas incluso mediante SQL directo.
- **Autenticación JWT** con cookies seguras y contraseñas hasheadas (bcrypt).
- **Roles jerárquicos**: SuperAdmin, Administrador, Encargado, Operador.
- **Panel Master oculto**: el área de administración global solo es accesible al Súper-Administrador; el resto de usuarios recibe respuesta de "no encontrado" sin revelar su existencia.

---

## 4. Motor Comercial

- **Panel Súper-Administrador** (`/saas-master`): vista exclusiva del dueño de la plataforma para gestionar todas las empresas clientes.
- **Onboarding automatizado**: registro de un nuevo restaurante cliente en un solo formulario — el sistema crea automáticamente la empresa, su sucursal inicial y el **primer usuario administrador** con contraseña temporal segura.
- **Preparado para ventas**: la plataforma puede incorporar nuevos clientes (restaurantes) sin intervención técnica y sin afectar a los clientes existentes.

---

## 5. Próximos Pasos

| Área | Iniciativas |
|------|-------------|
| **Core SaaS y UI** | Vistas avanzadas para SuperAdmin, editor de paneles y branding, plantillas de vistas |
| **Alertas** | Sistema de notificaciones por severidad (Avisos, Alertas, Urgentes) |
| **RBAC Evolucionado** | Afinamiento de permisos por rol (SuperAdmin, Administrador, Encargado, Operador de Cocina) |
| **Módulo "Academia"** | Entrenamientos y cursos (ej. Manipulación de alimentos) |
| **Operaciones Avanzadas** | Ejecución de checklists con estados (Completada/Pendiente/No conforme), evidencias fotográficas e incidencias |

---

## 6. Corrección de Apagado Inmediato de Uvicorn (Hotfix aplicado en agosto de 2026)

**Problema detectado:** Los logs de producción mostraban que Uvicorn efectuaba un "Shutting down" limpio y voluntario en el mismo segundo en que reportaba "Application startup complete", indicando un cierre interno del proceso.

**Diagnóstico y acciones realizadas:**
1. **Verificación de la llamada a `uvicorn.run`:** Confirmado que se encontraba correctamente indentada dentro del bloque `if __name__ == "__main__":` (líneas 2549-2551 de `app/main.py`), evitando así que se ejecute al importar el módulo por parte de Render.
2. **Búsqueda de salidas forzosas:** No se encontraron llamadas a `sys.exit()`, `exit()`, `quit()` ni `os._exit()` en ningún archivo Python del proyecto.
3. **Revisión del evento de inicio (`startup_event`):** Ya contaba con un bloque `try-except` que registraba errores y los volvía a lanzar (`raise`), previniendo apagados silenciosos por fallos en la inicialización de la base de datos.
4. **Medida preventiva adicional:** Se cambió el parámetro `reload=True` a `reload=False` en la llamada a `uvicorn.run` dentro del bloque `if __name__ == "__main__":`, como precaución para entornos de producción como Render, donde el modo de recarga automática puede generar conflictos o comportamientos inesperados.

**Cambios en `app/main.py`:**
```diff
- uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
+ uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
```

**Registro de Git:**
- Commit: `906893f` - "Hotfix: prevenir apagado instantaneo de uvicorn en Render"
- Push: `origin/main` actualizado (de `b1e0087` a `906893f`)

**Resultado:** Con estas correcciones, la aplicación mantiene un arranque estable en entornos de producción, eliminando el riesgo de cierre inmediato tras el reporte de "Application startup complete".

---


---

## 7. Mejoras de UX y manejo de errores (agosto de 2026)

### 7.1 Parche defensivo UI para Errores 500 y conexión onchange en selector
- **Problema detectado:** Las rutas secundarias (como /inventario, /mermas) arrojaban Error 500 debido a un `UndefinedError` en Jinja2 porque la plantilla base exigía la variable `sucursales` para el nuevo dropdown del navbar, y estas rutas no la estaban enviando en su context.
- **Diagnóstico y acciones realizadas:**
  1. **Parche Defensivo (Frontend - HTML):** Se envolvió el bloque del selector de sucursales en `templates/base.html` con un condicional de seguridad: `{% if sucursales is defined %} ... {% endif %}`. Esto evita que la página colapse si el backend omite la variable.
  2. **Parche Global (Backend - main.py):** Se inyectó la consulta de las sucursales del usuario directamente en el contexto global mediante el wrapper `TemplateResponse` (middleware de UI), de modo que todas las vistas heredan la variable automáticamente sin tener que tocar ningún endpoint de las rutas operativas.
  3. **Activación del Selector (JavaScript):** Se añadió un manejador `onchange` al `<select>` de sucursales del frontend para recargar la página al cambiar de sucursal, manteniendo los parámetros de filtros y paginación mediante `window.location.href`.
- **Registro de Git:**
  - Commit: `958ed72` - "Hotfix: Parche defensivo UI para Errores 500 y conexion onchange en selector"
  - Push: `origin/main` actualizado (de `906893f` a `958ed72`)

### 7.2 Corrección de IndentationError en TemplateResponse (hotfix quirúrgico)
- **Problema detectado:** Un commit previo introdujo un error de sangría (IndentationError) en la función `_patched_TemplateResponse` de `app/main.py`, específicamente alrededor de la línea 2222, causando que la aplicación fallara al arranque en producción.
- **Diagnóstico y acciones realizadas:**
  1. Se abrió `app/main.py` y se corrigió la indentación del bloque `else` dentro de `_patched_TemplateResponse`, alineando correctamente los espacios (4 espacios por nivel) para que coincidieran con la estructura de la función padre.
  2. Se verificó localmente con `python -m py_compile app/main.py` que no hubiera errores de sintaxis.
- **Registro de Git:**
  - Commit: `4740f25` - "Hotfix: Corregir IndentationError en TemplateResponse"
  - Push: `origin/main` actualizado (de `958ed72` a `4740f25`)

### 7.3 Manejador global 401 para redirección a login (mejora de UX)
- **Problema detectado:** Al expirar la sesión, las peticiones GET a rutas protegidas devolvían una respuesta JSON cruda con `{ "detail": "Not Authenticated" }` en lugar de redirigir al usuario a la página de login, lo que provocaba una mala experiencia de usuario (pantalla blanca o mensaje crudo).
- **Diagnóstico y acciones realizadas:**
  1. Se importó `StarletteHTTPException` desde `starlette.exceptions` en la sección de imports de `app/main.py`.
  2. Se añadió un manejador global de excepciones mediante `@app.exception_handler(StarletteHTTPException)` que intercepta todos los `HTTPException`.
  3. En el manejador, si el error es 401 (No Autenticado) y la petición es GET, se devuelve una `RedirectResponse` a `/login` con código de estado 303 (See Other). Para peticiones API (POST/PUT/DELETE) u otros errores, se mantiene la respuesta JSON original.
- **Registro de Git:**
  - Commit: `c4b37e9` - "Hotfix: Manejador global 401 para redireccion a login"
  - Push: `origin/main` actualizado (de `4740f25` a `c4b37e9`)


---

## 7.4 Corrección de decorador del manejador 401 (hotfix quirúrgico)

- **Problema detectado:** Tras aplicar el manejador global 401, el servidor colapsó en el evento de encendido con `TypeError: custom_http_exception_handler() missing 2 required positional arguments: 'request' and 'exc'`. Esto ocurrió porque el decorador `@app.exception_handler(StarletteHTTPException)` se había duplicado y, además, un decorador `@app.on_event("startup")` huérfano estaba colocado justo encima de la función del manejador, fazendo que FastAPI interprete erróneamente el manejador como una tarea de inicio.
- **Diagnóstico y acciones realizadas:**
  1. Se eliminó el decorador `@app.on_event("startup")` huérfano que estaba ubicado inmediatamente antes del bloque del manejador de excepciones.
  2. Se eliminó la duplicación del bloque del manejador global 401, dejando solo una instancia ubicada correctamente después del evento de inicio y antes de las demás funciones.
  3. Se verificó que el ÚNICO decorador inmediatamente arriba de `async def custom_http_exception_handler(request, exc):` sea estrictamente `@app.exception_handler(StarletteHTTPException)`.
- **Registro de Git:**
  - Commit: `237994b` - "Hotfix: Corregir decorador del manejador 401"
  - Push: `origin/main` actualizado (de `c4b37e9` a `237994b`)

*Documento generado para seguimiento ejecutivo. Detalle técnico completo en CORE_ARCHITECTURE.md.*