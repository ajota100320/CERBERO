"""Schemas Pydantic (FASE 5 — Motor de Mermas).

Definen el contrato de entrada/salida del router de mermas. Los tipos coinciden
exactamente con el modelo SQLAlchemy ``RegistroMerma`` (Regla de Oro 6).

Mapeo campo lógico → columna del modelo:
  insumo_id   -> ingrediente_id
  motivo      -> observaciones
  costo_total -> valor_perdida
  sucursal_id -> sucursal_id
"""
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class MermaCreate(BaseModel):
    """Payload para registrar una merma (POST /api/v1/mermas/)."""
    insumo_id: int = Field(..., gt=0, description="ID del insumo (ingrediente) a mermar")
    sucursal_id: Optional[int] = Field(
        None, gt=0,
        description="Sucursal donde ocurre la merma. Si se omite, se usa la del usuario autenticado.",
    )
    cantidad: float = Field(..., gt=0, description="Cantidad perdida (> 0)")
    motivo: str = Field(..., min_length=1, max_length=300, description="Motivo de la merma")
    costo_total: Optional[float] = Field(
        None, ge=0,
        description="Costo monetario de la merma. Si se omite, se calcula como cantidad × costo_promedio.",
    )
    tipo: Optional[str] = Field(
        None, description="Tipo de merma ('Vencimiento' | 'Daño' | 'Merma'). Default: 'Vencimiento'.",
    )


class MermaOut(BaseModel):
    """Respuesta serializada de una merma registrada (Regla 7: contratos claros)."""
    id: int
    insumo_id: int
    insumo: Optional[str] = None
    sucursal_id: Optional[int] = None
    sucursal: Optional[str] = None
    cantidad: float
    motivo: Optional[str] = None
    costo_total: float = 0.0
    tipo: Optional[str] = None
    fecha_merma: Optional[date] = None
    fecha_registro: Optional[datetime] = None
    responsable_usuario_id: Optional[int] = None
    estado: Optional[str] = None
