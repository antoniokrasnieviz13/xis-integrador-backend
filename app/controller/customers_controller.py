
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models import SessionLocal, Customer

router = APIRouter(tags=["Customers"])

# Schemas
class CustomerIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=160)
    document: Optional[str] = Field(None, max_length=32)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=40)
    address_street: Optional[str] = Field(None, max_length=160)
    address_number: Optional[str] = Field(None, max_length=30)
    address_district: Optional[str] = Field(None, max_length=80)
    address_city: Optional[str] = Field(None, max_length=80)
    address_state: Optional[str] = Field(None, max_length=2)
    address_zip: Optional[str] = Field(None, max_length=16)

class CustomerOut(CustomerIn):
    id: int
    class Config:
        from_attributes = True

class CustomerUpdate(CustomerIn):
    name: Optional[str] = None

def _db() -> Session:
    return SessionLocal()

# Endpoints
@router.post("/customers", response_model=CustomerOut, status_code=status.HTTP_201_CREATED)
def create_customer(payload: CustomerIn):
    db = _db()
    try:
        c = Customer(**payload.model_dump())
        db.add(c)
        db.commit()
        db.refresh(c)
        return c
    finally:
        db.close()

@router.get("/customers/{customer_id}", response_model=CustomerOut)
def get_customer(customer_id: int):
    db = _db()
    try:
        c = db.query(Customer).filter(Customer.id == customer_id).first()
        if not c:
            raise HTTPException(404, "Cliente não encontrado")
        return c
    finally:
        db.close()

@router.get("/customers", response_model=List[CustomerOut])
def list_customers(
    search: Optional[str] = Query(None, description="Filtra por nome/email/documento"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    db = _db()
    try:
        q = db.query(Customer)
        if search:
            like = f"%{search}%"
            q = q.filter(
                (Customer.name.ilike(like)) |
                (Customer.email.ilike(like)) |
                (Customer.document.ilike(like))
            )
        return q.order_by(Customer.id.desc()).offset(offset).limit(limit).all()
    finally:
        db.close()

@router.patch("/customers/{customer_id}", response_model=CustomerOut)
def update_customer(customer_id: int, patch: CustomerUpdate):
    db = _db()
    try:
        c = db.query(Customer).filter(Customer.id == customer_id).first()
        if not c:
            raise HTTPException(404, "Cliente não encontrado")
        for k, v in patch.model_dump(exclude_unset=True).items():
            setattr(c, k, v)
        db.commit()
        db.refresh(c)
        return c
    finally:
        db.close()

@router.delete("/customers/{customer_id}", status_code=204)
def delete_customer(customer_id: int):
    db = _db()
    try:
        c = db.query(Customer).filter(Customer.id == customer_id).first()
        if not c:
            raise HTTPException(404, "Cliente não encontrado")
        db.delete(c)
        db.commit()
        return
    finally:
        db.close()
