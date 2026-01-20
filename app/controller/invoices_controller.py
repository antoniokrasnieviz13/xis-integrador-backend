
# ... (demais imports e endpoints iguais aos que você já tem)
from sqlalchemy.orm import Session
from app.models import SessionLocal, Order, OrderItem, Product, StockItem, StockMovement, MovementType

# Substitua a função update_order_status pela abaixo:
@router.patch("/orders/{order_id}/status", response_model=OrderOut, tags=["Orders"])
def update_order_status(order_id: int, patch: StatusPatchIn):
    db: Session = SessionLocal()
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Pedido não encontrado")

        previous = order.status
        order.status = patch.status
        db.commit(); db.refresh(order)

        # Quando confirmar, baixa estoque (apenas 1x)
        if previous != "CONFIRMED" and patch.status == "CONFIRMED":
            for oi in order.items:
                # encontra produto pelo SKU
                p = db.query(Product).filter(Product.sku == oi.sku).first()
                if not p:
                    # se o item não estiver no catálogo, não baixa
                    continue
                si = db.query(StockItem).filter(StockItem.product_id == p.id).first()
                if not si:
                    continue
                qty = float(oi.qty)
                si.quantity -= qty
                mv = StockMovement(
                    product_id=p.id,
                    movement_type=MovementType.OUT,
                    quantity=qty,
                    unit_price=None,
                    reason="Order confirmed",
                    reference=f"ORDER {order.id}"
                )
                db.add(mv)
            db.commit()

        return order
    finally:
        db.close()
``
