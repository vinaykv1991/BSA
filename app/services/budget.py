from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import models
from datetime import datetime, UTC

class BudgetService:
    @staticmethod
    def get_budget_status(db: Session, user_id: int):
        budgets = db.query(models.Budget).filter(models.Budget.user_id == user_id).all()

        status = []
        for budget in budgets:
            now = datetime.now(UTC)
            start_of_month = datetime(now.year, now.month, 1, tzinfo=UTC)

            total_spent = db.query(func.sum(models.Transaction.amount))\
                .join(models.Account)\
                .filter(models.Account.user_id == user_id)\
                .filter(models.Transaction.category_id == budget.category_id)\
                .filter(models.Transaction.transaction_type == "Spending")\
                .filter(models.Transaction.date >= start_of_month)\
                .scalar() or 0.0

            status.append({
                "category": budget.category.name,
                "budgeted": budget.amount,
                "spent": total_spent,
                "remaining": budget.amount - total_spent,
                "status": "Over Budget" if total_spent > budget.amount else "Under Budget"
            })
        return status

    @staticmethod
    def get_safe_to_spend(db: Session, user_id: int):
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            return 0.0

        now = datetime.now(UTC)
        start_of_month = datetime(now.year, now.month, 1, tzinfo=UTC)

        # Base monthly income
        safe_to_spend = user.monthly_income

        # Add actual earnings this month
        total_earnings = db.query(func.sum(models.Transaction.amount))\
            .join(models.Account)\
            .filter(models.Account.user_id == user_id)\
            .filter(models.Transaction.transaction_type == "Earning")\
            .filter(models.Transaction.date >= start_of_month)\
            .scalar() or 0.0

        # Subtract actual spendings this month
        total_spendings = db.query(func.sum(models.Transaction.amount))\
            .join(models.Account)\
            .filter(models.Account.user_id == user_id)\
            .filter(models.Transaction.transaction_type == "Spending")\
            .filter(models.Transaction.date >= start_of_month)\
            .scalar() or 0.0

        return safe_to_spend + total_earnings - total_spendings
