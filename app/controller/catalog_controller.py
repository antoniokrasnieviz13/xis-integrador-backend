
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field, conlist
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models import SessionLocal, Category, Product, StockItem

router = APIRouter(tags=["Catalog"])

# Schemas
class CategoryIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    description: Optional[str] = Field(None, max_length=500)
    active: bool = True

class CategoryOut(CategoryIn):
    id: int
    class Config:
        from_attributes = True

class ProductIn(BaseModel):
    sku: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=160)
    description: Optional[str] = None
    category_id: Optional[int] = None
    price: float = Field(ge=0)
    cost: Optional[float] = None
    active: bool = True
    initial_qty: float = 0.0
    unit: str = "UN"
    min_quantity: float = 0.0

class ProductOut(BaseModel):
    id: int
    sku: str
    name: str
    description: Optional[str]
    category_id: Optional[int]
    price: float
    cost: Optional[float]
    active: bool
    class Config:
        from_attributes = True

def _db() -> Session:
    return SessionLocal()

# Category endpoints
@router.post("/categories", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(payload: CategoryIn):
    db = _db()
    try:
        if db.query(Category).filter(Category.name == payload.name).first():
            raise HTTPException(409, "Categoria já existe")
        c = Category(**payload.model_dump())
        db.add(c); db.commit(); db.refresh(c)
        return c
    finally:
        db.close()

@router.get("/categories", response_model=List[CategoryOut])
def list_categories(active: Optional[bool] = None):
    db = _db()
    try:
        q = db.query(Category)
        if active is not None:
            q = q.filter(Category.active == active)
        return q.order_by(Category.name.asc()).all()
    finally:
        db.close()

# Product endpoints
@router.post("/products", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductIn):
    db = _db()
    try:
        if db.query(Product).filter(Product.sku == payload.sku).first():
            raise HTTPException(409, "Produto com esse SKU já existe")
        p = Product(
            sku=payload.sku,
            name=payload.name,
            description=payload.description,
            category_id=payload.category_id,
            price=float(payload.price),
            cost=float(payload.cost) if payload.cost is not None else None,
            active=payload.active
        )
        db.add(p); db.flush()  # gera id

        # Cria registro de estoque (se não existir)
        if not db.query(StockItem).filter(StockItem.product_id == p.id).first():
            si = StockItem(
                product_id=p.id,
                unit=payload.unit,
                quantity=float(payload.initial_qty),
                min_quantity=float(payload.min_quantity)
            )
            db.add(si)

        db.commit(); db.refresh(p)
        return p
    finally:
        db.close()

@router.get("/products", response_model=List[ProductOut])
def list_products(
    search: Optional[str] = Query(None),
    active: Optional[bool] = None,
    category_id: Optional[int] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    db = _db()
    try:
        q = db.query(Product)
        if search:
            like = f"%{search}%"
            q = q.filter((Product.name.ilike(like)) | (Product.sku.ilike(like)))
        if active is not None:
            q = q.filter(Product.active == active)
        if category_id:
            q = q.filter(Product.category_id == category_id)
        return q.order_by(Product.name.asc()).offset(offset).limit(limit).all()
    finally:
        db.close()

@router.get("/products/{product_id}", response_model=ProductOut)
def get_product(product_id: int):
    db = _db()
    try:
        p = db.query(Product).filter(Product.id == product_id).first()
        if not p:
            raise HTTPException(404, "Produto não encontrado")
        return p
    finally:
        db.close()

@router.patch("/products/{product_id}", response_model=ProductOut)
def update_product(product_id: int, patch: ProductIn):
    db = _db()
    try:
        p = db.query(Product).filter(Product.id == product_id).first()
        if not p:
            raise HTTPException(404, "Produto não encontrado")
        data = patch.model_dump()
        # Não permitir troca para SKU duplicado
        if data.get("sku") and data["sku"] != p.sku:
            if db.query(Product).filter(Product.sku == data["sku"]).first():
                raise HTTPException(409, "SKU já utilizado por outro produto")

        p.sku = data["sku"]
        p.name = data["name"]
        p.description = data["description"]
        p.category_id = data["category_id"]
        p.price = float(data["price"])
        p.cost = float(data["cost"]) if data.get("cost") is not None else None
        p.active = data["active"]

        # Atualiza parâmetros de estoque (não altera quantity aqui)
        si = db.query(StockItem).filter(StockItem.product_id == product_id).first()
        if si:
            si.unit = data.get("unit", si.unit)
            si.min_quantity = float(data.get("min_quantity", si.min_quantity))
        db.commit(); db.refresh(p)
        return p
    finally:
        db.close()
