
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from sqlalchemy.orm import Session
from app.models import SessionLocal, Product, StockItem, StockMovement, MovementType

router = APIRouter(tags=["Stock"])

class StockItemOut(BaseModel):
    product_id: int
    sku: str
    name: str
    unit: str
    quantity: float
    min_quantity: float
    class Config:
        from_attributes = True

class StockAdjustIn(BaseModel):
    sku: str = Field(..., min_length=1)
    movement_type: Literal["IN", "OUT", "ADJUST"]
    quantity: float = Field(..., gt=0)
    unit_price: Optional[float] = None
    reason: Optional[str] = None
    reference: Optional[str] = None

class MovementOut(BaseModel):
    id: int
    product_id: int
    movement_type: str
    quantity: float
    unit_price: Optional[float]
    reason: Optional[str]
    reference: Optional[str]
    class Config:
        from_attributes = True

def _db() -> Session:
    return SessionLocal()

@router.get("/stock", response_model=List[StockItemOut])
def list_stock(search: Optional[str] = None):
    db = _db()
    try:
        q = db.query(StockItem).join(Product, StockItem.product_id == Product.id)
        if search:
            like = f"%{search}%"
            q = q.filter((Product.name.ilike(like)) | (Product.sku.ilike(like)))
        rows = q.all()
        result = []
        for si in rows:
            result.append(StockItemOut(
                product_id=si.product_id,
                sku=si.product.sku,
                name=si.product.name,
                unit=si.unit,
                quantity=si.quantity,
                min_quantity=si.min_quantity
            ))
        return result
    finally:
        db.close()

@router.post("/stock/adjust", response_model=MovementOut, status_code=status.HTTP_201_CREATED)
def adjust_stock(payload: StockAdjustIn):
    db = _db()
    try:
        p = db.query(Product).filter(Product.sku == payload.sku).first()
        if not p:
            raise HTTPException(404, "Produto não encontrado pelo SKU")
        si = db.query(StockItem).filter(StockItem.product_id == p.id).first()
        if not si:
            raise HTTPException(400, "Produto sem registro de estoque")

        qty = float(payload.quantity)
        if payload.movement_type == "IN":
            si.quantity += qty
        elif payload.movement_type == "OUT":
            si.quantity -= qty
        elif payload.movement_type == "ADJUST":
            # Ajuste positivo/negativo: usa 'OUT' com sinal? Aqui vamos aplicar como delta positivo.
            si.quantity += qty
        else:
            raise HTTPException(400, "Tipo de movimento inválido")

        mv = StockMovement(
            product_id=p.id,
            movement_type=payload.movement_type,  # type: ignore
            quantity=qty,
            unit_price=float(payload.unit_price) if payload.unit_price is not None else None,
            reason=payload.reason,
            reference=payload.reference
        )
        db.add(mv)
        db.commit(); db.refresh(mv)
        return mv
    finally:
        db.close()

@router.get("/stock/movements", response_model=List[MovementOut])
def list_movements(limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0)):
    db = _db()
    try:
        q = db.query(StockMovement).order_by(StockMovement.id.desc()).offset(offset).limit(limit)
        return q.all()
    finally:
        db.close()
