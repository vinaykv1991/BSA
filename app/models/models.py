from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.database import Base
import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    monthly_income = Column(Float, default=0.0)
    accounts = relationship("Account", back_populates="owner")
    budgets = relationship("Budget", back_populates="user")

class Account(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String)
    type = Column(String) # Bank, Credit Card, Cash
    owner = relationship("User", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account")

class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    type = Column(String) # Fixed, Variable, Discretionary, Investment, Transfer
    transactions = relationship("Transaction", back_populates="category")
    budgets = relationship("Budget", back_populates="category")

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"))
    date = Column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))
    amount = Column(Float)
    merchant = Column(String)
    description = Column(String)
    category_id = Column(Integer, ForeignKey("categories.id"))
    transaction_type = Column(String) # Earning, Spending
    source = Column(String) # SMS, PDF, CSV, Manual
    raw_data = Column(String)

    account = relationship("Account", back_populates="transactions")
    category = relationship("Category", back_populates="transactions")

class Budget(Base):
    __tablename__ = "budgets"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    category_id = Column(Integer, ForeignKey("categories.id"))
    amount = Column(Float)
    period = Column(String, default="monthly")

    user = relationship("User", back_populates="budgets")
    category = relationship("Category", back_populates="budgets")
