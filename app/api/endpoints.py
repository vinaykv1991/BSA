from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from app.database import SessionLocal
from app.models import models
from app.schemas import schemas
from app.services.ingestion import IngestionService
from app.services.budget import BudgetService

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/users", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = models.User(name=user.name, email=user.email, monthly_income=user.monthly_income)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.post("/accounts", response_model=schemas.Account)
def create_account(account: schemas.AccountCreate, db: Session = Depends(get_db)):
    db_account = models.Account(user_id=account.user_id, name=account.name, type=account.type)
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return db_account

@router.post("/ingest", response_model=List[schemas.Transaction])
def ingest_data(request: schemas.IngestRequest, db: Session = Depends(get_db)):
    return IngestionService.ingest_raw_data(db, request)

@router.get("/users/{user_id}/transactions", response_model=List[schemas.Transaction])
def read_transactions(user_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    transactions = db.query(models.Transaction)\
        .join(models.Account)\
        .filter(models.Account.user_id == user_id)\
        .offset(skip).limit(limit).all()
    return transactions

@router.get("/users/{user_id}/summary", response_model=List[schemas.SummaryItem])
def get_summary(user_id: int, db: Session = Depends(get_db)):
    summary = db.query(
        models.Category.name,
        func.sum(models.Transaction.amount).label("total_amount")
    ).join(models.Transaction)\
    .join(models.Account)\
    .filter(models.Account.user_id == user_id)\
    .group_by(models.Category.name).all()

    return [schemas.SummaryItem(category=s[0], total_amount=s[1]) for s in summary]

@router.get("/users/{user_id}/budget_status")
def get_budget_status(user_id: int, db: Session = Depends(get_db)):
    return BudgetService.get_budget_status(db, user_id)

@router.get("/users/{user_id}/safe_to_spend")
def get_safe_to_spend(user_id: int, db: Session = Depends(get_db)):
    return {"safe_to_spend": BudgetService.get_safe_to_spend(db, user_id)}
