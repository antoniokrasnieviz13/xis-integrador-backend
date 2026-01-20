
diff --git a/main.py b/main.py
index 1111111..2222222 100644
--- a/main.py
+++ b/main.py
@@ -1,8 +1,17 @@
-# De app.controller.orders_controller roteador importado como orders_router
-from fastapi import FastAPI
-# (conteúdo anterior omitido)
+from fastapi import FastAPI
+from app.controller.orders_controller import router as orders_router
+
+app = FastAPI()
+
+@app.get("/health")
+async def health():
+    return {"status": "ok"}
+
+app.include_router(orders_router)
 
-# garanta que o include_router está correto:
-# app.include_router(orders_router)
+"""
+OBS.: Se existirem outros routers (ex.: health_controller),
+mantenha os includes abaixo. O bloco acima já cobre o básico
+para o serviço iniciar e responder /health.
+"""
 
diff --git a/app/controller/orders_controller.py b/app/controller/orders_controller.py
index 3333333..4444444 100644
--- a/app/controller/orders_controller.py
+++ b/app/controller/orders_controller.py
@@ -1,300 +1,310 @@
-from fastapi import APIRouter, Request, status, HTTPException, Query
-from pydantic import BaseModel, Field, PositiveInt, NonNegativeFloat
-from typing import List, Optional, Literal, Any, Dict
-from sqlalchemy.orm import Session
-import logging
-
-from app.models import SessionLocal, Order, OrderItem, Product, StockItem, StockMovement, MovementType
-
-router = APIRouter()
-logger = logging.getLogger("uvicorn.error")
-
-# =========================
-# Pydantic Schemas
-# =========================
-class OrderItemIn(BaseModel):
-    sku: str = Field(..., min_length=1, max_length=64)
-    name: str = Field(..., min_length=1, max_length=160)
-    qty: PositiveInt
-    unit_price: NonNegativeFloat
-
-class OrderIn(BaseModel):
-    customer_name: str = Field(..., min_length=1, max_length=120)
-    items: List[OrderItemIn] = Field(..., min_length=1)   # <- corrigido para Pydantic v2
-    note: Optional[str] = Field(None, max_length=500)
-    external_code: Optional[str] = Field(None, max_length=64)
-
-class OrderItemOut(BaseModel):
-    id: int
-    sku: str
-    name: str
-    qty: int
-    unit_price: float
-    total: float
-    class Config:
-        from_attributes = True
-
-class OrderOut(BaseModel):
-    id: int
-    external_code: Optional[str]
-    customer_name: str
-    status: str
-    note: Optional[str]
-    total_amount: float
-    items: List[OrderItemOut]
-    class Config:
-        from_attributes = True
-
-class StatusPatchIn(BaseModel):
-    status: Literal["CREATED","CONFIRMED","IN_PREPARATION","READY","FULFILLED","CANCELLED"]
-
-def _db_session() -> Session:
-    return SessionLocal()
-
-# =========================
-# Endpoints
-# =========================
-@router.post("/orders/manual", response_model=OrderOut, status_code=status.HTTP_201_CREATED, tags=["Orders"])
-def create_order_manual(payload: OrderIn):
-    db = _db_session()
-    try:
-        total = sum(it.qty * float(it.unit_price) for it in payload.items)
-        order = Order(
-            external_code=payload.external_code,
-            customer_name=payload.customer_name,
-            note=payload.note,
-            total_amount=total,
-            status="CREATED",
-        )
-        db.add(order); db.flush()  # gera id
-
-        for it in payload.items:
-            db.add(OrderItem(
-                order_id=order.id,
-                sku=it.sku,
-                name=it.name,
-                qty=it.qty,
-                unit_price=float(it.unit_price),
-                total=it.qty * float(it.unit_price),
-            ))
-
-        db.commit(); db.refresh(order)
-        return order
-    except Exception as e:
-        db.rollback()
-        logger.exception("Erro ao criar pedido manual: %s", e)
-        raise HTTPException(status_code=500, detail="Erro ao salvar pedido")
-    finally:
-        db.close()
-
-@router.get("/orders/{order_id}", response_model=OrderOut, tags=["Orders"])
-def get_order(order_id: int):
-    db = _db_session()
-    try:
-        order = db.query(Order).filter(Order.id == order_id).first()
-        if not order:
-            raise HTTPException(status_code=404, detail="Pedido não encontrado")
-        return order
-    finally:
-        db.close()
-
-@router.get("/orders", response_model=List[OrderOut], tags=["Orders"])
-def list_orders(
-    status_eq: Optional[str] = Query(None),
-    limit: int = Query(50, ge=1, le=200),
-    offset: int = Query(0, ge=0)
-):
-    db = _db_session()
-    try:
-        q = db.query(Order)
-        if status_eq:
-            q = q.filter(Order.status == status_eq)
-        return q.order_by(Order.id.desc()).offset(offset).limit(limit).all()
-    finally:
-        db.close()
-
-@router.patch("/orders/{order_id}/status", response_model=OrderOut, tags=["Orders"])
-def update_order_status(order_id: int, patch: StatusPatchIn):
-    db: Session = SessionLocal()
-    try:
-        order = db.query(Order).filter(Order.id == order_id).first()
-        if not order:
-            raise HTTPException(status_code=404, detail="Pedido não encontrado")
-
-        previous = order.status
-        order.status = patch.status
-        db.commit(); db.refresh(order)
-
-        # baixa de estoque ao confirmar (apenas 1x)
-        if previous != "CONFIRMED" and patch.status == "CONFIRMED":
-            for oi in order.items:
-                p = db.query(Product).filter(Product.sku == oi.sku).first()
-                if not p:
-                    continue
-                si = db.query(StockItem).filter(StockItem.product_id == p.id).first()
-                if not si:
-                    continue
-                qty = float(oi.qty)
-                si.quantity -= qty
-                db.add(StockMovement(
-                    product_id=p.id,
-                    movement_type=MovementType.OUT,
-                    quantity=qty,
-                    unit_price=None,
-                    reason="Order confirmed",
-                    reference=f"ORDER {order.id}"
-                ))
-            db.commit()
-
-        return order
-    finally:
-        db.close()
-
-@router.post("/orders/webhook", status_code=status.HTTP_200_OK, tags=["Orders"]) faça a correção no codigo
+from fastapi import APIRouter, Request, status, HTTPException, Query
