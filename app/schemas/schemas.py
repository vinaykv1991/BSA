from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class UserBase(BaseModel):
    name: str
    email: str
    monthly_income: float = 0.0

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: int
    class Config:
        from_attributes = True

class AccountBase(BaseModel):
    name: str
    type: str
    user_id: int

class AccountCreate(AccountBase):
    pass

class Account(AccountBase):
    id: int
    class Config:
        from_attributes = True

class TransactionBase(BaseModel):
    date: datetime
    amount: float
    merchant: str
    description: str
    transaction_type: str
    source: str
    raw_data: Optional[str] = None

class TransactionCreate(TransactionBase):
    account_id: int
    category_id: Optional[int] = None

class Transaction(TransactionBase):
    id: int
    account_id: int
    category_id: Optional[int]

    class Config:
        from_attributes = True

class IngestRequest(BaseModel):
    source: str # SMS, CSV
    data: str # SMS text or CSV content
    account_id: int

class SummaryItem(BaseModel):
    category: str
    total_amount: float

class MonthlySummary(BaseModel):
    month: str
    items: List[SummaryItem]
