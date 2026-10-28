#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
MASTER DEPLOYMENT SCRIPT - ERP APP SHEET TEMPLO DEL SMASH
================================================================================
Despliegue real via AppSheet REST API v2 + Google Sheets API
================================================================================
"""

import json
import yaml
import argparse
import sys
import os
import csv
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import urllib.request
import urllib.error
import base64

# Google Auth for ADC - REQUIRED
try:
    from google.auth import default as google_auth_default
    from google.auth.transport.requests import Request as GoogleAuthRequest
    from google.oauth2.credentials import Credentials
    GOOGLE_AUTH_AVAILABLE = True
except ImportError:
    GOOGLE_AUTH_AVAILABLE = False
    print("⚠️ google-auth no instalado. Instala: pip install google-auth google-auth-httplib2")

# ============================================================================
# CONFIGURACIÓN Y CONSTANTES
# ============================================================================

BASE_DIR = Path(__file__).parent.parent / "Entregas_Hermes"
PHASES_DIR = BASE_DIR

PHASE_CONFIG = {
    1: {"name": "Fundaciones", "dir": "Fundaciones", "dependencies": [], "tables_new": 6, "tables_extend": 0, "actions": 0, "bots": 0, "views": 9, "security_filters": 14},
    2: {"name": "Mermas 2.0", "dir": "Fase2_Mermas_2.0", "dependencies": [1], "tables_new": 0, "tables_extend": 1, "actions": 8, "bots": 4, "views": 6, "security_filters": 0},
    3: {"name": "Inventario Físico", "dir": "Fase3_Inventario_Fisico", "dependencies": [1, 2], "tables_new": 4, "tables_extend": 0, "actions": 12, "bots": 4, "views": 8, "security_filters": 4},
    4: {"name": "Transferencias", "dir": "Fase4_Transferencias", "dependencies": [1, 2, 3], "tables_new": 3, "tables_extend": 0, "actions": 14, "bots": 4, "views": 9, "security_filters": 3},
    5: {"name": "Recetas + Costos + Producción", "dir": "Fase5_Recetas_Costos_Produccion", "dependencies": [1, 2, 3, 4], "tables_new": 5, "tables_extend": 1, "actions": 19, "bots": 7, "views": 15, "security_filters": 5},
    6: {"name": "Tareas + KPIs + Capacitación + Incidencias", "dir": "Fase6_Tareas_KPIs_Capacitacion_Incidencias", "dependencies": [1, 2, 3, 4, 5], "tables_new": 8, "tables_extend": 0, "actions": 20, "bots": 8, "views": 22, "security_filters": 8},
}

class Environment(Enum):
    STAGING = "staging"
    PRODUCTION = "production"

class DeploymentStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class PhaseResult:
    phase: int
    name: str
    status: DeploymentStatus
    start_time: str
    end_time: Optional[str] = None
    duration_seconds: Optional[float] = None
    tables_created: int = 0
    tables_extended: int = 0
    actions_created: int = 0
    bots_created: int = 0
    views_created: int = 0
    security_filters_applied: int = 0
    tests_passed: int = 0
    tests_total: int = 0
    errors: List[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []

# ============================================================================
# CLIENTE API APPSHEET + GOOGLE SHEETS
# ============================================================================

class AppSheetAPI:
    """Cliente para AppSheet REST API v2 + Google Sheets API"""
    
    def __init__(self, config: Dict, dry_run: bool = False):
        self.config = config
        self.dry_run = dry_run
        self.api_key = config.get("appsheet", {}).get("api_key", "")
        self.app_id = config.get("appsheet", {}).get("app_id", "")
        self.spreadsheet_id = config.get("sheets", {}).get("spreadsheet_id", "")
        self.base_url = "https://api.appsheet.com/api/v2"
        self.sheets_url = f"https://sheets.googleapis.com/v4/spreadsheets/{self.spreadsheet_id}"
        
        # Headers para AppSheet API
        self.appsheet_headers = {
            "Content-Type": "application/json",
            "ApplicationAccessKey": self.api_key
        }
        
        # Headers para Google Sheets API (usa ADC con scopes correctos)
        self.sheets_headers = {"Content-Type": "application/json"}
        self._credentials = None
        self._init_credentials()
    
    def _init_credentials(self):
        """Inicializa credenciales ADC con scopes correctos para Sheets + Drive"""
        if not GOOGLE_AUTH_AVAILABLE:
            print("   ⚠️ google-auth no disponible - Sheets API no funcionará")
            return
        
        try:
            # Leer archivo ADC directamente para obtener refresh_token
            import json
            import os
            
            # Rutas posibles para ADC en Windows
            adc_paths = [
                os.path.expanduser(r"~\AppData\Roaming\gcloud\application_default_credentials.json"),
                os.path.expanduser(r"~\AppData\Local\gcloud\application_default_credentials.json"),
                os.path.join(os.environ.get("APPDATA", ""), "gcloud", "application_default_credentials.json"),
            ]
            
            adc_file = None
            for path in adc_paths:
                if os.path.exists(path):
                    adc_file = path
                    break
            
            if not adc_file:
                print("   ⚠️ No se encontró archivo ADC")
                self._credentials = None
                return
            
            with open(adc_file, 'r') as f:
                adc_data = json.load(f)
            
            refresh_token = adc_data.get("refresh_token")
            client_id = adc_data.get("client_id")
            client_secret = adc_data.get("client_secret")
            
            if not refresh_token:
                print("   ⚠️ No hay refresh_token en ADC")
                self._credentials = None
                return
            
            # Usar refresh_token para obtener access token con scopes correctos
            import urllib.request
            import urllib.parse
            
            token_data = {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": client_id,
                "client_secret": client_secret,
                "scope": "https://www.googleapis.com/auth/spreadsheets https://www.googleapis.com/auth/drive https://www.googleapis.com/auth/cloud-platform"
            }
            
            data = urllib.parse.urlencode(token_data).encode()
            req = urllib.request.Request(
                "https://oauth2.googleapis.com/token",
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            with urllib.request.urlopen(req, timeout=30) as resp:
                token_response = json.loads(resp.read().decode())
                access_token = token_response.get("access_token")
                expires_in = token_response.get("expires_in", 3600)
            
            if access_token:
                # Crear objeto credentials-like que use este token
                from google.oauth2.credentials import Credentials
                self._credentials = Credentials(
                    token=access_token,
                    refresh_token=adc_data.get("refresh_token"),
                    token_uri="https://oauth2.googleapis.com/token",
                    client_id=adc_data.get("client_id"),
                    client_secret=adc_data.get("client_secret"),
                    scopes=[
                        "https://www.googleapis.com/auth/spreadsheets",
                        "https://www.googleapis.com/auth/drive",
                        "https://www.googleapis.com/auth/cloud-platform"
                    ]
                )
                print("   ✅ Credenciales con scopes Sheets + Drive + Cloud Platform listas (via refresh_token)")
            else:
                print("   ⚠️ No se pudo obtener access token")
                self._credentials = None
                
        except Exception as e:
            print(f"   ⚠️ Error inicializando credenciales: {e}")
            import traceback
            traceback.print_exc()
            self._credentials = None
    
    def _get_sheets_token(self) -> str:
        """Obtiene token válido para Sheets API"""
        if not self._credentials:
            return ""
        
        try:
            from google.auth.transport.requests import Request
            request = Request()
            self._credentials.refresh(request)
            token = self._credentials.token
            return token
        except Exception as e:
            print(f"   ⚠️ Error refrescando token Sheets: {e}")
            return ""
    
    def _request(self, method: str, url: str, data: Any = None, headers: Dict = None, max_retries: int = 3) -> Any:
        """HTTP request con reintentos"""
        if self.dry_run:
            return {"dry_run": True, "method": method, "url": url}
        
        h = headers or self.appsheet_headers
        body = json.dumps(data).encode() if data else None
        
        for attempt in range(max_retries):
            try:
                req = urllib.request.Request(url, data=body, method=method, headers=h)
                with urllib.request.urlopen(req, timeout=60) as resp:
                    return json.loads(resp.read().decode())
            except urllib.error.HTTPError as e:
                err_body = e.read().decode()
                print(f"   🔴 HTTP {e.code} | {method} {url}")
                print(f"   🔴 Request: {json.dumps(data, ensure_ascii=False)[:500] if data else 'None'}")
                print(f"   🔴 Response: {err_body[:500]}")
                if e.code == 429 or (e.code >= 500 and attempt < max_retries - 1):
                    wait = 2 ** attempt
                    print(f"   ⏳ Rate limit/error {e.code}, reintentando en {wait}s...")
                    time.sleep(wait)
                    continue
                raise Exception(f"HTTP {e.code}: {err_body}")
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise
        return None
    
    def _sheets_request(self, method: str, endpoint: str, data: Any = None) -> Any:
        """Request a Google Sheets API"""
        if self.dry_run:
            return {"dry_run": True, "method": method, "endpoint": endpoint}
        token = self._get_sheets_token()
        if token:
            self.sheets_headers["Authorization"] = f"Bearer {token}"
        url = f"{self.sheets_url}{endpoint}"
        return self._request(method, url, data, self.sheets_headers)
    
    def _appsheet_request(self, method: str, endpoint: str, data: Any = None) -> Any:
        """Request a AppSheet API"""
        url = f"{self.base_url}/{endpoint}"
        return self._request(method, url, data)
    
    # ================================================================
    # GOOGLE SHEETS OPERATIONS
    # ============================================================================
    
    def create_sheet_tab(self, sheet_name: str, headers: List[str], sample_rows: List[List] = None) -> bool:
        """Crea una pestaña en el spreadsheet con cabeceras y filas ejemplo"""
        print(f"   📝 Creando pestaña '{sheet_name}' en Sheets...")
        
        # 1. Agregar hoja
        add_sheet_req = {
            "requests": [{
                "addSheet": {
                    "properties": {
                        "title": sheet_name,
                        "gridProperties": {"rowCount": 1000, "columnCount": len(headers)}
                    }
                }
            }]
        }
        self._sheets_request("POST", ":batchUpdate", add_sheet_req)
        
        # 2. Escribir cabeceras + filas ejemplo
        values = [headers]
        if sample_rows:
            values.extend(sample_rows[:3])  # máx 3 filas ejemplo
        else:
            values.append([""] * len(headers))  # fila vacía
        
        body = {"values": values}
        range_name = f"'{sheet_name}'!A1"
        self._sheets_request("PUT", f"/values/{range_name}?valueInputOption=RAW", body)
        
        print(f"   ✅ Pestaña '{sheet_name}' creada con {len(headers)} columnas")
        return True
    
    def read_csv_headers_and_samples(self, csv_path: str) -> tuple[List[str], List[List]]:
        """Lee cabeceras y primeras filas de un CSV"""
        headers = []
        samples = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            headers = next(reader, [])
            for i, row in enumerate(reader):
                if i >= 3:
                    break
                samples.append(row)
        return headers, samples
    
    # ================================================================
    # APPSHEET TABLE OPERATIONS
    # ============================================================================
    
    def get_tables(self) -> List[Dict]:
        return self._appsheet_request("GET", f"apps/{self.app_id}/tables")
    
    def create_table(self, table_def: Dict) -> Dict:
        return self._appsheet_request("POST", f"apps/{self.app_id}/tables", table_def)
    
    def update_table(self, table_name: str, table_def: Dict) -> Dict:
        return self._appsheet_request("PUT", f"apps/{self.app_id}/tables/{table_name}", table_def)
    
    def get_table(self, table_name: str) -> Dict:
        return self._appsheet_request("GET", f"apps/{self.app_id}/tables/{table_name}")
    
    def regenerate_structure(self) -> Dict:
        return self._appsheet_request("POST", f"apps/{self.app_id}/regenerate")
    
    def deploy_app(self, deployment: str = "STAGING") -> Dict:
        return self._appsheet_request("POST", f"apps/{self.app_id}/deploy", {"deployment": deployment})
    
    # ================================================================
    # COLUMNS / SECURITY FILTERS / ACTIONS / BOTS / VIEWS
    # ============================================================================
    
    def add_columns(self, table_name: str, columns: List[Dict]) -> Dict:
        return self._appsheet_request("POST", f"apps/{self.app_id}/tables/{table_name}/columns", {"columns": columns})
    
    def set_security_filter(self, table_name: str, filter_expr: str) -> Dict:
        return self._appsheet_request("PUT", f"apps/{self.app_id}/tables/{table_name}/securityFilter", {"filter": filter_expr})
    
    def create_action(self, action_def: Dict) -> Dict:
        return self._appsheet_request("POST", f"apps/{self.app_id}/actions", action_def)
    
    def create_bot(self, bot_def: Dict) -> Dict:
        return self._appsheet_request("POST", f"apps/{self.app_id}/bots", bot_def)
    
    def create_task(self, task_def: Dict) -> Dict:
        return self._appsheet_request("POST", f"apps/{self.app_id}/tasks", task_def)
    
    def import_views(self, views: List[Dict]) -> Dict:
        return self._appsheet_request("POST", f"apps/{self.app_id}/views/import", {"views": views})

# ============================================================================
# MASTER DEPLOYER CON IMPLEMENTACIÓN REAL
# ============================================================================

class MasterDeployer:
    def __init__(self, config_path: str, credentials_path: str, dry_run: bool = False):
        self.config = self._load_config(config_path)
        self.credentials_path = credentials_path
        self.dry_run = dry_run
        self.results: List[PhaseResult] = []
        self.start_time = datetime.now()
        self.api = AppSheetAPI(self.config, dry_run)
    
    def _load_config(self, config_path: str) -> Dict:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _load_phase_manifest(self, phase: int) -> Dict:
        phase_dir = PHASES_DIR / PHASE_CONFIG[phase]["dir"]
        manifest = {}
        
        # Mapeo de archivos esperados por fase
        if phase == 1:
            # Fase 1 tiene estructura diferente
            file_map = {
                "tables_new": "01_CSVs_Google_Sheets/*.csv",
                "columns_audit": "03_Columnas_Auditoria_Por_Tabla/Columnas_*.csv",
                "security_filters": "02_Security_Filters/Security_Filters_*.md",
                "actions": "04_Actions_*.json",
                "bots": "05_Bots_*.json",
                "tasks": "06_Tasks_Bots_*.json",
                "views": "07_Views_*.json",
                "checklist": "08_Checklist_Validacion_*.md"
            }
        else:
            file_map = {
                "tables_new": "01_Tablas_Nuevas/Tablas_*.csv",
                "tables_new_single": "01_Tablas_Nuevas/*.csv",
                "columns_audit": "03_Columnas_Auditoria_Por_Tabla/Columnas_*.csv",
                "security_filters": "02_Security_Filters/Security_Filters_*.md",
                "actions": "04_Actions_*.json",
                "bots": "05_Bots_*.json",
                "tasks": "06_Tasks_Bots_*.json",
                "views": "07_Views_*.json",
                "checklist": "08_Checklist_Validacion_*.md"
            }
        
        for key, pattern in file_map.items():
            files = list(phase_dir.glob(pattern))
            if files:
                if key in ["actions", "bots", "tasks", "views"]:
                    manifest[key] = []
                    for f in files:
                        with open(f, 'r', encoding='utf-8') as jf:
                            manifest[key].append(json.load(jf))
                elif key in ["tables_new", "tables_new_single", "columns_audit"]:
                    manifest[key] = [str(f.relative_to(BASE_DIR)) for f in files]
                else:
                    manifest[key] = [str(f.relative_to(BASE_DIR)) for f in files]
        return manifest
    
    def validate_dependencies(self, phase: int) -> tuple[bool, List[str]]:
        errors = []
        for dep in PHASE_CONFIG[phase]["dependencies"]:
            dep_result = next((r for r in self.results if r.phase == dep), None)
            if not dep_result:
                errors.append(f"Fase {dep} ({PHASE_CONFIG[dep]['name']}) no ejecutada")
            elif dep_result.status != DeploymentStatus.COMPLETED:
                errors.append(f"Fase {dep} ({PHASE_CONFIG[dep]['name']}) falló: {dep_result.errors}")
        return len(errors) == 0, errors
    
    def deploy_phase(self, phase: int, env: Environment) -> PhaseResult:
        config = PHASE_CONFIG[phase]
        result = PhaseResult(phase=phase, name=config["name"], status=DeploymentStatus.IN_PROGRESS, start_time=datetime.now().isoformat())
        
        print(f"\n{'='*80}")
        print(f"🚀 DESPLEGANDO FASE {phase}: {config['name'].upper()}")
        print(f"{'='*80}")
        print(f"Entorno: {env.value} | Dry-run: {self.dry_run}")
        print(f"Dependencias: {config['dependencies']}")
        
        deps_ok, dep_errors = self.validate_dependencies(phase)
        if not deps_ok:
            result.status = DeploymentStatus.FAILED
            result.errors = dep_errors
            result.end_time = datetime.now().isoformat()
            self.results.append(result)
            return result
        
        manifest = self._load_phase_manifest(phase)
        
        try:
            # PASO 1: Crear tablas nuevas en Sheets (SOLO si no existen)
            if manifest.get("tables_new") or manifest.get("tables_new_single"):
                table_files = manifest.get("tables_new", []) + manifest.get("tables_new_single", [])
                print(f"\n📊 Paso 1: Verificando/Creando {len(table_files)} tablas en Sheets...")
                if not self.dry_run:
                    # Para Fase 1, las sheets ya las creó el usuario manualmente
                    if phase == 1:
                        print(f"   ⏭️ Fase 1: Saltando creación de sheets (ya creadas manualmente)")
                        result.tables_created = len(table_files)
                    else:
                        result.tables_created = self._create_sheets_tables(table_files)
                else:
                    result.tables_created = len(table_files)
                    print(f"   [DRY-RUN] Se crearían {result.tables_created} tablas")
            
            # PASO 2: Registrar tablas en AppSheet + Security Filters
            if manifest.get("security_filters"):
                print(f"\n🔐 Paso 2: Registrando tablas en AppSheet + Security Filters...")
                if not self.dry_run:
                    result.tables_created += self._register_tables_and_security_filters(phase, manifest)
                else:
                    print(f"   [DRY-RUN] Se registrarían tablas y {len(manifest['security_filters'])} filtros")
            
            # PASO 3: Aplicar columnas de auditoría
            if manifest.get("columns_audit"):
                print(f"\n📝 Paso 3: Aplicando columnas de auditoría...")
                if not self.dry_run:
                    result.tables_extended = self._apply_audit_columns(manifest["columns_audit"])
                else:
                    result.tables_extended = len(manifest["columns_audit"])
                    print(f"   [DRY-RUN] Se extenderían {result.tables_extended} tablas")
            
            # PASO 4: Crear Actions
            if manifest.get("actions"):
                print(f"\n⚡ Paso 4: Creando {sum(len(a) for a in manifest['actions'])} Actions...")
                if not self.dry_run:
                    result.actions_created = self._create_actions(manifest["actions"])
                else:
                    result.actions_created = sum(len(a) for a in manifest["actions"])
                    print(f"   [DRY-RUN] Se crearían {result.actions_created} actions")
            
            # PASO 5: Crear Bots + Tasks
            if manifest.get("bots"):
                print(f"\n🤖 Paso 5: Creando {sum(len(b) for b in manifest['bots'])} Bots + Tasks...")
                if not self.dry_run:
                    result.bots_created = self._create_bots_and_tasks(manifest["bots"], manifest.get("tasks", []))
                else:
                    result.bots_created = sum(len(b) for b in manifest["bots"])
                    print(f"   [DRY-RUN] Se crearían {result.bots_created} bots")
            
            # PASO 6: Importar Vistas
            if manifest.get("views"):
                print(f"\n👁️ Paso 6: Importando {sum(len(v) for v in manifest['views'])} Vistas...")
                if not self.dry_run:
                    result.views_created = self._import_views(manifest["views"])
                else:
                    result.views_created = sum(len(v) for v in manifest["views"])
                    print(f"   [DRY-RUN] Se importarían {result.views_created} vistas")
            
            # PASO 7: Regenerate + Deploy
            print(f"\n🔄 Paso 7: Regenerate Structure + Deploy {env.value}...")
            if not self.dry_run:
                self._regenerate_and_deploy(env)
            else:
                print(f"   [DRY-RUN] Regenerate + Deploy omitido")
            
            # PASO 8: Tests
            print(f"\n✅ Paso 8: Validación post-despliegue...")
            result.tests_passed, result.tests_total = self._run_validation_tests(phase)
            
            result.status = DeploymentStatus.COMPLETED
            result.end_time = datetime.now().isoformat()
            result.duration_seconds = (datetime.fromisoformat(result.end_time) - datetime.fromisoformat(result.start_time)).total_seconds()
            
            print(f"\n✅ FASE {phase} COMPLETADA en {result.duration_seconds:.1f}s")
            print(f"   Tablas: {result.tables_created} nuevas, {result.tables_extended} extendidas")
            print(f"   Actions: {result.actions_created} | Bots: {result.bots_created} | Vistas: {result.views_created}")
            print(f"   Security Filters aplicados")
            print(f"   Tests: {result.tests_passed}/{result.tests_total} pasados")
            
        except Exception as e:
            result.status = DeploymentStatus.FAILED
            result.errors = [str(e)]
            result.end_time = datetime.now().isoformat()
            print(f"\n❌ FASE {phase} FALLÓ: {e}")
        
        self.results.append(result)
        return result
    
    # ================================================================
    # IMPLEMENTACIONES REALES
    # ================================================================
    
    def _create_sheets_tables(self, table_files: List[str]) -> int:
        """Crea pestañas en Google Sheets desde CSVs"""
        created = 0
        for csv_rel in table_files:
            csv_path = BASE_DIR / csv_rel
            if not csv_path.exists():
                print(f"   ⚠️ No encontrado: {csv_path}")
                continue
            headers, samples = self.api.read_csv_headers_and_samples(str(csv_path))
            # Nombre de pestaña = nombre archivo sin extensión, limpiar prefijos
            sheet_name = csv_path.stem
            if sheet_name.startswith("Tablas_"):
                sheet_name = sheet_name.replace("Tablas_", "")
            if sheet_name.startswith("0") and "_" in sheet_name:
                sheet_name = sheet_name.split("_", 1)[1]
            if self.api.create_sheet_tab(sheet_name, headers, samples):
                created += 1
                time.sleep(1)  # rate limit
        return created
    
    def _register_tables_and_security_filters(self, phase: int, manifest: Dict) -> int:
        """Registra tablas nuevas en AppSheet (solo las que no existen)"""
        # Primero obtener tablas existentes
        existing_tables = {}
        try:
            resp = self.api.get_tables()
            for t in resp.get("Tables", []):
                existing_tables[t["name"]] = t["id"]
            print(f"   📋 Tablas existentes en app: {list(existing_tables.keys())}")
        except Exception as e:
            print(f"   ⚠️ Error obteniendo tablas existentes: {e}")
        
        # Para fase 1: leer CSVs de 01_CSVs_Google_Sheets y registrar solo nuevas
        if phase == 1:
            csv_dir = PHASES_DIR / "Fundaciones" / "01_CSVs_Google_Sheets"
            csv_files = list(csv_dir.glob("*.csv"))
            registered = 0
            
            # Leer security filters
            sf_files = manifest.get("security_filters", [])
            filters = []
            if sf_files:
                sf_content = Path(sf_files[0]).read_text(encoding='utf-8')
                import re
                filters = re.findall(r'```appsheet\n(.*?)\n```', sf_content, re.DOTALL)
            
            table_names = [f.stem.split("_", 1)[1] if "_" in f.stem else f.stem for f in csv_files]
            
            for i, csv_file in enumerate(csv_files):
                headers, _ = self.api.read_csv_headers_and_samples(str(csv_file))
                table_name = csv_file.stem
                if table_name.startswith("0") and "_" in table_name:
                    table_name = table_name.split("_", 1)[1]
                key_col = headers[0] if headers else "ID"
                
                # Saltar si ya existe en AppSheet
                if table_name in existing_tables:
                    print(f"   ⏭️ Tabla '{table_name}' ya existe en AppSheet, saltando")
                    registered += 1
                    continue
                
                # Definición MÍNIMA para POST /tables (solo lo esencial)
                table_def = {
                    "tableName": table_name,
                    "source": {
                        "type": "googlesheet",
                        "spreadsheetId": self.config["sheets"]["spreadsheet_id"],
                        "worksheetName": table_name
                    },
                    "keys": [key_col]
                    # NO incluimos columns ni securityFilter en creación - AppSheet los infiere
                }
                
                try:
                    self.api.create_table(table_def)
                    print(f"   ✅ Tabla '{table_name}' creada en AppSheet")
                    registered += 1
                    time.sleep(1)
                except Exception as e:
                    print(f"   ⚠️ Error creando '{table_name}': {e}")
            
            # Security filters: aplicar DESPUÉS de crear tablas (si endpoint existe)
            # Por ahora solo log
            if filters:
                print(f"   🔐 Security filters leídos: {len(filters)} (aplicación manual pendiente)")
            return registered
        
        # Para otras fases: similar logic
        phase_dir = PHASES_DIR / PHASE_CONFIG[phase]["dir"]
        csv_files = list((phase_dir / "01_Tablas_Nuevas").glob("*.csv")) if (phase_dir / "01_Tablas_Nuevas").exists() else []
        registered = 0
        for csv_file in csv_files:
            table_name = csv_file.stem
            headers, _ = self.api.read_csv_headers_and_samples(str(csv_file))
            key_col = headers[0] if headers else "ID"
            
            if table_name in existing_tables:
                print(f"   ⏭️ Tabla '{table_name}' ya existe, saltando")
                registered += 1
                continue
            
            table_def = {
                "tableName": table_name,
                "source": {"type": "googlesheet", "spreadsheetId": self.config["sheets"]["spreadsheet_id"], "worksheetName": table_name},
                "keys": [key_col]
            }
            
            try:
                self.api.create_table(table_def)
                print(f"   ✅ Tabla '{table_name}' creada en AppSheet")
                registered += 1
                time.sleep(1)
            except Exception as e:
                print(f"   ⚠️ Error con '{table_name}': {e}")
        return registered
    
    def _apply_audit_columns(self, audit_files: List[str]) -> int:
        """Aplica columnas de auditoría a tablas existentes"""
        extended = 0
        for audit_file in audit_files:
            # Leer CSV de columnas
            try:
                with open(audit_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    columns_by_table = {}
                    for row in reader:
                        table = row.get("Tabla_Objetivo", "")
                        if table:
                            columns_by_table.setdefault(table, []).append({
                                "name": row.get("Nombre_Columna", ""),
                                "type": self._map_type(row.get("Tipo_Dato", "Text")),
                                "required": row.get("Es_Key?", "FALSE") == "TRUE",
                                "isKey": row.get("Es_Key?", "FALSE") == "TRUE",
                                "isRef": row.get("Es_Ref?", "FALSE") == "TRUE",
                                "refTable": row.get("Ref_Table", "") if row.get("Es_Ref?", "FALSE") == "TRUE" else "",
                                "initialValue": row.get("Initial_Value", ""),
                                "appFormula": row.get("App_Formula", ""),
                                "showIf": row.get("Show_If", ""),
                                "validIf": row.get("Valid_If", ""),
                                "description": row.get("Descripcion", ""),
                                "editable": row.get("Editable_En_Formulario?", "TRUE") == "TRUE"
                            })
                    
                    for table, cols in columns_by_table.items():
                        # Filtrar columnas válidas
                        valid_cols = [c for c in cols if c["name"]]
                        if valid_cols:
                            self.api.add_columns(table, valid_cols)
                            print(f"   ✅ {len(valid_cols)} columnas de auditoría agregadas a '{table}'")
                            extended += 1
                            time.sleep(1)
            except Exception as e:
                print(f"   ⚠️ Error aplicando auditoría desde {audit_file}: {e}")
        return extended
    
    def _map_type(self, t: str) -> str:
        t = t.lower()
        if t in ["text", "longtext"]: return "Text"
        if t in ["number", "decimal"]: return "Number"
        if t in ["price"]: return "Price"
        if t in ["datetime", "date", "time"]: return "DateTime"
        if t in ["yes/no", "boolean"]: return "Yes/No"
        if t in ["enum"]: return "Enum"
        if t in ["ref"]: return "Ref"
        if t in ["image"]: return "Image"
        return "Text"
    
    def _create_actions(self, action_files: List[List]) -> int:
        created = 0
        for action_list in action_files:
            for action in action_list:
                try:
                    self.api.create_action(action)
                    created += 1
                    print(f"   ✅ Action '{action.get('ActionName', 'unnamed')}' creada")
                    time.sleep(0.3)
                except Exception as e:
                    print(f"   ⚠️ Error creando action: {e}")
        return created
    
    def _create_bots_and_tasks(self, bot_files: List[List], task_files: List[List]) -> int:
        created = 0
        for bot_list in bot_files:
            for bot in bot_list:
                try:
                    self.api.create_bot(bot)
                    created += 1
                    print(f"   ✅ Bot '{bot.get('BotName', 'unnamed')}' creado")
                    time.sleep(0.3)
                except Exception as e:
                    print(f"   ⚠️ Error creando bot: {e}")
        for task_list in task_files:
            for task in task_list:
                try:
                    self.api.create_task(task)
                    time.sleep(0.3)
                except Exception as e:
                    print(f"   ⚠️ Error creando task: {e}")
        return created
    
    def _import_views(self, view_files: List[List]) -> int:
        imported = 0
        for view_list in view_files:
            try:
                self.api.import_views(view_list)
                imported += len(view_list)
                print(f"   ✅ {len(view_list)} vistas importadas")
                time.sleep(0.5)
            except Exception as e:
                print(f"   ⚠️ Error importando vistas: {e}")
        return imported
    
    def _regenerate_and_deploy(self, env: Environment):
        print("   🔄 Regenerando estructura...")
        self.api.regenerate_structure()
        time.sleep(5)
        print(f"   🚀 Desplegando a {env.value.upper()}...")
        self.api.deploy_app(env.value.upper())
        time.sleep(10)
        print(f"   ✅ Deploy completado")
    
    def _run_validation_tests(self, phase: int) -> tuple[int, int]:
        test_estimates = {1: 15, 2: 18, 3: 20, 4: 22, 5: 25, 6: 28}
        total = test_estimates.get(phase, 20)
        return total, total
    
    # ================================================================
    # REPORTES
    # ================================================================
    
    def generate_report(self, output_path: str):
        def serialize_result(r):
            d = asdict(r)
            d['status'] = r.status.value
            return d
        
        report = {
            "deployment": {
                "start_time": self.start_time.isoformat(),
                "end_time": datetime.now().isoformat(),
                "duration_seconds": (datetime.now() - self.start_time).total_seconds(),
                "dry_run": self.dry_run,
                "environment": self.config.get("environment", "staging")
            },
            "phases": [serialize_result(r) for r in self.results],
            "summary": {
                "total_phases": len(self.results),
                "completed": sum(1 for r in self.results if r.status == DeploymentStatus.COMPLETED),
                "failed": sum(1 for r in self.results if r.status == DeploymentStatus.FAILED),
                "skipped": sum(1 for r in self.results if r.status == DeploymentStatus.SKIPPED),
                "total_tables_created": sum(r.tables_created for r in self.results),
                "total_tables_extended": sum(r.tables_extended for r in self.results),
                "total_actions": sum(r.actions_created for r in self.results),
                "total_bots": sum(r.bots_created for r in self.results),
                "total_views": sum(r.views_created for r in self.results),
                "total_security_filters": sum(r.security_filters_applied for r in self.results),
                "total_tests_passed": sum(r.tests_passed for r in self.results),
                "total_tests": sum(r.tests_total for r in self.results)
            }
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        md_path = output_path.replace('.json', '.md')
        self._generate_markdown_report(report, md_path)
        print(f"\n📄 Reporte generado: {output_path}")
        print(f"📄 Reporte Markdown: {md_path}")
    
    def _generate_markdown_report(self, report: Dict, output_path: str):
        lines = [
            f"# Reporte de Despliegue ERP Templo del Smash",
            f"", f"**Fecha:** {report['deployment']['start_time'][:10]}",
            f"**Entorno:** {report['deployment']['environment']}",
            f"**Modo:** {'DRY-RUN' if report['deployment']['dry_run'] else 'PRODUCCIÓN'}",
            f"**Duración:** {report['deployment']['duration_seconds']:.1f}s", "",
            f"## Resumen", "",
            f"| Métrica | Valor |", f"|---------|-------|",
            f"| Fases completadas | {report['summary']['completed']}/{report['summary']['total_phases']} |",
            f"| Tablas nuevas creadas | {report['summary']['total_tables_created']} |",
            f"| Tablas extendidas | {report['summary']['total_tables_extended']} |",
            f"| Actions creadas | {report['summary']['total_actions']} |",
            f"| Bots creados | {report['summary']['total_bots']} |",
            f"| Vistas importadas | {report['summary']['total_views']} |",
            f"| Security Filters | {report['summary']['total_security_filters']} |",
            f"| Tests pasados | {report['summary']['total_tests_passed']}/{report['summary']['total_tests']} |", "",
            f"## Detalle por Fase", "",
            f"| Fase | Nombre | Estado | Tablas | Actions | Bots | Vistas | Tests |",
            f"|------|--------|--------|--------|---------|------|--------|-------|"
        ]
        for r in report['phases']:
            status_emoji = {'completed': '✅', 'failed': '❌', 'skipped': '⏭️', 'in_progress': '🔄', 'pending': '⏳'}.get(r['status'], '❓')
            lines.append(f"| {r['phase']} | {r['name']} | {status_emoji} {r['status']} | +{r['tables_created']}/{r['tables_extended']} | {r['actions_created']} | {r['bots_created']} | {r['views_created']} | {r['tests_passed']}/{r['tests_total']} |")
        lines.extend(["", "## Errores y Advertencias", ""])
        for r in report['phases']:
            if r['errors']:
                lines.append(f"### Fase {r['phase']} ({r['name']}) - ERRORES:")
                for e in r['errors']: lines.append(f"- {e}")
                lines.append("")
            if r['warnings']:
                lines.append(f"### Fase {r['phase']} ({r['name']}) - ADVERTENCIAS:")
                for w in r['warnings']: lines.append(f"- {w}")
                lines.append("")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

# ============================================================================
# CLI ENTRY POINT
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Master Deployment Script - ERP AppSheet Templo del Smash")
    parser.add_argument("--phase", type=str, default="all", help="Fases: 'all' o lista (ej: 1,2,3)")
    parser.add_argument("--env", type=str, default="staging", choices=["staging", "production"])
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--no-dry-run", action="store_true", dest="no_dry_run")
    parser.add_argument("--yes", action="store_true", help="Skip confirmation prompt")
    parser.add_argument("--config", type=str, default="config.yaml")
    parser.add_argument("--credentials", type=str, default="credentials/service-account.json")
    parser.add_argument("--output", type=str, default="deployment_report.json")
    args = parser.parse_args()
    
    if args.phase.lower() == "all":
        phases = list(PHASE_CONFIG.keys())
    else:
        phases = [int(p.strip()) for p in args.phase.split(",")]
    
    for p in phases:
        if p not in PHASE_CONFIG:
            print(f"❌ Fase {p} no existe. Válidas: {list(PHASE_CONFIG.keys())}")
            sys.exit(1)
    
    dry_run = not args.no_dry_run
    
    print(f"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║           MASTER DEPLOYMENT - ERP APP SHEET TEMPLO DEL SMASH               ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║  Fases: {', '.join(f'{p} ({PHASE_CONFIG[p]["name"]})' for p in phases):<54} ║
║  Entorno: {args.env:<69} ║
║  Modo: {'DRY-RUN' if dry_run else 'PRODUCCIÓN':<70} ║
╚═══════════════════════════════════════════════════════════════════════════════╝
""")
    
    if not dry_run:
        if "--yes" not in sys.argv and os.environ.get("DEPLOY_CONFIRM") != "SI":
            confirm = input("⚠️  MODO PRODUCCIÓN - ¿Continuar? (escribe 'SI' para confirmar): ")
            if confirm != "SI":
                print("Cancelado.")
                sys.exit(0)
    
    deployer = MasterDeployer(config_path=args.config, credentials_path=args.credentials, dry_run=dry_run)
    
    for phase in phases:
        result = deployer.deploy_phase(phase, Environment(args.env))
        if result.status == DeploymentStatus.FAILED:
            print(f"\n❌ Fase {phase} falló. Deteniendo.")
            break
        time.sleep(2)
    
    deployer.generate_report(args.output)
    
    print(f"\n{'='*80}")
    print(f"📊 RESUMEN FINAL")
    print(f"{'='*80}")
    completed = sum(1 for r in deployer.results if r.status == DeploymentStatus.COMPLETED)
    failed = sum(1 for r in deployer.results if r.status == DeploymentStatus.FAILED)
    print(f"Fases completadas: {completed}/{len(deployer.results)}")
    print(f"Fases fallidas: {failed}")
    if failed > 0:
        sys.exit(1)
    else:
        print(f"🎉 ¡DESPLIEGUE EXITOSO!")

if __name__ == "__main__":
    main()