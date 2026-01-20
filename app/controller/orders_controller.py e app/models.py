
diff --git a/app/controller/orders_controller.py b/app/controller/orders_controller.py
index 6b5e1aa..ab12c4e 100644
--- a/app/controller/orders_controller.py
+++ b/app/controller/orders_controller.py
@@ -118,7 +118,7 @@ def list_orders(
 ):
     db = _db_session()
     try:
-        q = db.query(Ordem)
+        q = db.query(Order)
         if status_eq:
             q = q.filter(Order.status == status_eq)
         return q.order_by(Order.id.desc()).offset(offset).limit(limit).all()
@@ -168,6 +168,7 @@ def update_order_status(order_id: int, patch: StatusPatchIn):
                 if not si:
                     continue
                 qty = float(oi.qty)
+                # registra movimento amarrado ao item de estoque
                 si.quantity -= qty
                 db.add(
                     StockMovement(
-                        product_id=p.id,
+                        stock_item_id=si.id,     # <— FK direta para StockItem
+                        product_id=p.id,         # opcional (útil em relatórios)
                         movement_type=MovementType.OUT,
                         quantity=qty,
                         unit_price=None,
                         reason="Order confirmed",
                         reference=f"ORDER {order.id}",
                     )
                 )
             db.commit()
diff --git a/app/models.py b/app/models.py
index 4d3a0b2..91c2e6d 100644
--- a/app/models.py
+++ b/app/models.py
@@ -1,22 +1,26 @@
-from sqlalchemy import (
-    Column, Integer, String, Float, DateTime, Enum, ForeignKey, func
-)
-from sqlalchemy.orm import relationship, declarative_base, sessionmaker
+from sqlalchemy import (
+    Column, Integer, String, Float, DateTime, Enum, ForeignKey, func
+)
+from sqlalchemy.orm import relationship, declarative_base, sessionmaker
 from sqlalchemy import create_engine
 import enum

 Base = declarative_base()

 class MovementType(enum.Enum):
     IN = "IN"
     OUT = "OUT"

 class Product(Base):
     __tablename__ = "products"
     id = Column(Integer, primary_key=True)
     sku = Column(String(64), unique=True, nullable=False)
     name = Column(String(160), nullable=False)
-    stock_items = relationship("StockItem", back_populates="product")
+    stock_items = relationship("StockItem", back_populates="product")

 class StockItem(Base):
     __tablename__ = "stock_items"
     id = Column(Integer, primary_key=True)
     product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
     quantity = Column(Float, default=0, nullable=False)
-    product = relationship("Product", back_populates="stock_items")
-    # (ANTES) movements sem FK direta, causando erro de join
-    # movements = relationship("StockMovement", back_populates="stock_item")
+    product = relationship("Product", back_populates="stock_items")
+    # relação 1:N com StockMovement pela **FK direta** (ver classe abaixo)
+    movements = relationship(
+        "StockMovement",
+        back_populates="stock_item",
+        cascade="all, delete-orphan",
+    )

 class StockMovement(Base):
     __tablename__ = "stock_movements"
     id = Column(Integer, primary_key=True)
-    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
+    # 🔴 NOVA FK direta para resolver o join em StockItem.movements
+    stock_item_id = Column(Integer, ForeignKey("stock_items.id"), nullable=False)
+    # (opcional) manter product_id se já utilizado em relatórios
+    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
     movement_type = Column(Enum(MovementType), nullable=False)
     quantity = Column(Float, nullable=False)
     unit_price = Column(Float)
     reason = Column(String(100))
     reference = Column(String(100))
     created_at = Column(DateTime, server_default=func.now())
-    # (ANTES) sem back_populates funcional
-    # stock_item = relationship("StockItem", back_populates="movements")
+    # back_populates casado com StockItem.movements
+    stock_item = relationship("StockItem", back_populates="movements")
