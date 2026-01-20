
import os
from typing import Optional
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean, Enum
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.sql import func
import enum

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./db.sqlite3")
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# =========================
# Domínio de Clientes
# =========================
class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(160), nullable=False, index=True)
    document = Column(String(32), nullable=True, unique=False)   # CPF/CNPJ (opcional)
    email = Column(String(160), nullable=True, unique=False)
    phone = Column(String(40), nullable=True)
    address_street = Column(String(160), nullable=True)
    address_number = Column(String(30), nullable=True)
    address_district = Column(String(80), nullable=True)
    address_city = Column(String(80), nullable=True)
    address_state = Column(String(2), nullable=True)
    address_zip = Column(String(16), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# =========================
# Cardápio / Catálogo
# =========================
class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    active = Column(Boolean, default=True)
    products = relationship("Product", back_populates="category")


class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(64), nullable=False, unique=True, index=True)
    name = Column(String(160), nullable=False)
    description = Column(Text, nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    price = Column(Float, nullable=False, default=0.0)
    cost = Column(Float, nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    category = relationship("Category", back_populates="products")
    stock_item = relationship("StockItem", back_populates="product", uselist=False)


# =========================
# Estoque
# =========================
class MovementType(str, enum.Enum):
    IN_ = "IN"
    OUT = "OUT"
    ADJUST = "ADJUST"


class StockItem(Base):
    __tablename__ = "stock_items"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), unique=True, nullable=False)
    unit = Column(String(10), nullable=False, default="UN")  # UN, KG, L
    quantity = Column(Float, nullable=False, default=0.0)
    min_quantity = Column(Float, nullable=False, default=0.0)
    product = relationship("Product", back_populates="stock_item")
    movements = relationship("StockMovement", back_populates="product", cascade="all, delete-orphan")


class StockMovement(Base):
    __tablename__ = "stock_movements"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    movement_type = Column(Enum(MovementType), nullable=False)
    quantity = Column(Float, nullable=False, default=0.0)
    unit_price = Column(Float, nullable=True)  # relevante para entradas (compra)
    reason = Column(String(160), nullable=True)
    reference = Column(String(160), nullable=True)  # ex: NF number, Order id
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    product = relationship("Product")


# =========================
# Notas Fiscais de Compra (Lançamentos)
# =========================
class PurchaseInvoice(Base):
    __tablename__ = "purchase_invoices"
    id = Column(Integer, primary_key=True, index=True)
    supplier_name = Column(String(160), nullable=False)
    number = Column(String(40), nullable=False)
    series = Column(String(20), nullable=True)
    issue_date = Column(DateTime(timezone=True), nullable=True)
    total_amount = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    items = relationship("PurchaseInvoiceItem", back_populates="invoice", cascade="all, delete-orphan")


class PurchaseInvoiceItem(Base):
    __tablename__ = "purchase_invoice_items"
    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("purchase_invoices.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"))
    sku = Column(String(64), nullable=False)
    name = Column(String(160), nullable=False)
    qty = Column(Float, nullable=False, default=0.0)
    unit = Column(String(10), nullable=False, default="UN")
    unit_price = Column(Float, nullable=False, default=0.0)
    total = Column(Float, nullable=False, default=0.0)

    invoice = relationship("PurchaseInvoice", back_populates="items")
    product = relationship("Product")


# =========================
# Pedidos (já existentes)
# =========================
class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    external_code = Column(String(64), unique=True, nullable=True)
    customer_name = Column(String(120), nullable=False)
    status = Column(String(32), default="CREATED", index=True)
    note = Column(Text, nullable=True)
    total_amount = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    sku = Column(String(64), nullable=False)
    name = Column(String(160), nullable=False)
    qty = Column(Integer, nullable=False, default=1)
    unit_price = Column(Float, nullable=False, default=0.0)
    total = Column(Float, nullable=False, default=0.0)

    order = relationship("Order", back_populates="items")
    product = relationship("Product")


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
