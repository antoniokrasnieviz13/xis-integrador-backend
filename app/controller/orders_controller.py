
# app/controller/orders_controller.py
from fastapi import APIRouter, Request, status, HTTPException, Query
from pydantic import BaseModel, Field, PositiveInt, NonNegativeFloat
from typing import List, Optional, Literal
from sqlalchemy.orm import Session
import logging

from app.models import (
    SessionLocal,
    Order,
    OrderItem,
    Product,
    StockItem,
    StockMovement,
    MovementType,
)

router = APIRouter()
logger = logging.getLogger("uvicorn.error")

# =========================
# Pydantic Schemas (Pydantic v2)
# =========================
class OrderItemIn(BaseModel):
    sku: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=160)
    qty: PositiveInt
    unit_price: NonNegativeFloat

class OrderIn(BaseModel):
    customer_name: str = Field(..., min_length=1, max_length=120)
    items: List[OrderItemIn] = Field(..., min_length=1)
    note: Optional[str] = Field(None, max_length=500)
    external_code: Optional[str] = Field(None, max_length=64)

class OrderItemOut(BaseModel):
    id: int
    sku: str
    name: str
    qty: int
    unit_price: float
    total: float

    class Config:
        from_attributes = True  # pydantic v2

class OrderOut(BaseModel):
    id: int
    external_code: Optional[str]
    customer_name: str
    status: str
    note: Optional[str]
    total_amount: float
    items: List[OrderItemOut]

    class Config:
        from_attributes = True  # pydantic v2

class StatusPatchIn(BaseModel):
    status: Literal["CREATED", "CONFIRMED", "IN_PREPARATION", "READY", "FULFILLED", "CANCELLED"]

def _db_session() -> Session:
    return SessionLocal()

# =========================
# Endpoints
# =========================
@router.post("/orders/manual", response_model=OrderOut, status_code=status.HTTP_201_CREATED, tags=["Orders"])
def create_order_manual(payload: OrderIn):
    db = _db_session()
    try:
        total = sum(it.qty * float(it.unit_price) for it in payload.items)

        order = Order(
            external_code=payload.external_code,
            customer_name=payload.customer_name,
            note=payload.note,
            total_amount=total,
            status="CREATED",
        )
        db.add(order)
        db.flush()  # gera order.id

        for it in payload.items:
            db.add(
                OrderItem(
                    order_id=order.id,
                    sku=it.sku,
                    name=it.name,
                    qty=it.qty,
                    unit_price=float(it.unit_price),
                    total=it.qty * float(it.unit_price),
                )
            )

        db.commit()
        db.refresh(order)
        return order

    except Exception as e:
        db.rollback()
        logger.exception("Erro ao criar pedido manual: %s", e)
        raise HTTPException(status_code=500, detail="Erro ao salvar pedido")
    finally:
        db.close()

@router.get("/orders/{order_id}", response_model=OrderOut, tags=["Orders"])
def get_order(order_id: int):
    db = _db_session()
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Pedido não encontrado")
        return order
    finally:
        db.close()

@router.get("/orders", response_model=List[OrderOut], tags=["Orders"])
def list_orders(
    status_eq: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    db = _db_session()
    try:
        q = db.query(Order)
        if status_eq:
            q = q.filter(Order.status == status_eq)
        return q.order_by(Order.id.desc()).offset(offset).limit(limit).all()
    finally:
        db.close()

@router.patch("/orders/{order_id}/status", response_model=OrderOut, tags=["Orders"])
def update_order_status(order_id: int, patch: StatusPatchIn):
    db = _db_session()
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Pedido não encontrado")

        previous = order.status
        order.status = patch.status
        db.commit()
        db.refresh(order)

        # baixa de estoque ao confirmar (apenas 1x)
        if previous != "CONFIRMED" and patch.status == "CONFIRMED":
            for oi in order.items:
                p = db.query(Product).filter(Product.sku == oi.sku).first()
                if not p:
                    continue
                si = db.query(StockItem).filter(StockItem.product_id == p.id).first()
                if not si:
                    continue
                qty = float(oi.qty)
                si.quantity -= qty
                db.add(
                    StockMovement(
                        product_id=p.id,
                        movement_type=MovementType.OUT,
                        quantity=qty,
                        unit_price=None,
                        reason="Order confirmed",
                        reference=f"ORDER {order.id}",
                    )
                )
            db.commit()

        return order
    finally:
        db.close()

@router.post("/orders/webhook", status_code=status.HTTP_200_OK, tags=["Orders"])
async def orders_webhook(request: Request):
    """
    Webhook para receber pedidos do iFood (ou outro integrador).
    - Aceita JSON genérico (dict).
    - Normaliza campos comuns para o modelo interno.
    """
    db = _db_session()
    try:
        data = await request.json()
        if not isinstance(data, dict):
            raise HTTPException(status_code=400, detail="Payload inválido")

        external_code = data.get("external_code") or data.get("orderId") or data.get("id")
        customer_name = data.get("customer_name") or (data.get("customer") or {}).get("name") or "Cliente"
        note = data.get("note") or data.get("observation")

        raw_items = data.get("items") or data.get("orderItems") or []
        if not isinstance(raw_items, list) or len(raw_items) == 0:
            raise HTTPException(status_code=400, detail="Pedido sem itens")

        normalized_items = []
        for it in raw_items:
            sku = it.get("sku") or it.get("id") or it.get("code")
            name = it.get("name") or it.get("description") or "Item"
            qty = it.get("qty") or it.get("quantity") or 0
            unit_price = it.get("unit_price") or it.get("unitPrice") or it.get("price") or 0
            if not sku or not name or not qty:
                raise HTTPException(status_code=422, detail="Item do pedido inválido")
            normalized_items.append(
                {"sku": str(sku), "name": str(name), "qty": int(qty), "unit_price": float(unit_price)}
            )

        total = sum(i["qty"] * i["unit_price"] for i in normalized_items)

        order = Order(
            external_code=external_code,
            customer_name=customer_name,
            note=note,
            total_amount=total,
            status="CREATED",
        )
        db.add(order)
        db.flush()

        for it in normalized_items:
            db.add(
                OrderItem(
                    order_id=order.id,
                    sku=it["sku"],
                    name=it["name"],
                    qty=it["qty"],
                    unit_price=it["unit_price"],
                    total=it["qty"] * it["unit_price"],
                )
