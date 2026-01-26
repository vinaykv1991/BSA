from sqlalchemy.orm import Session
from fastapi import HTTPException
from typing import List
import base64
from app.models import models
from app.schemas import schemas
from app.services.normalization import NormalizationService
from app.services.categorization import CategorizationService

class IngestionService:
    @staticmethod
    def ingest_raw_data(db: Session, request: schemas.IngestRequest) -> List[models.Transaction]:
        normalized_list = []
        if request.source.upper() == "SMS":
            data = NormalizationService.parse_sms(request.data)
            if data:
                normalized_list.append(data)
        elif request.source.upper() == "CSV":
            import csv
            import io
            f = io.StringIO(request.data)
            reader = csv.DictReader(f)
            for row in reader:
                data = NormalizationService.parse_csv_row(row)
                if data:
                    normalized_list.append(data)
        elif request.source.upper() == "PDF":
            try:
                # Expecting base64 encoded PDF
                pdf_bytes = base64.b64decode(request.data)
                normalized_list = NormalizationService.parse_pdf(pdf_bytes)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Failed to decode or parse PDF: {str(e)}")

        if not normalized_list:
            raise HTTPException(status_code=400, detail="Failed to parse data or no transactions found")

        created_transactions = []
        for normalized_data in normalized_list:
            # Categorize
            cat_result = CategorizationService.categorize(
                normalized_data["merchant"],
                normalized_data["description"]
            )
            category_name = cat_result["category"]
            transaction_type = cat_result["type"]

            # Get or create category
            db_category = db.query(models.Category).filter(models.Category.name == category_name).first()
            if not db_category:
                db_category = models.Category(name=category_name, type="General")
                db.add(db_category)
                try:
                    db.commit()
                    db.refresh(db_category)
                except Exception:
                    db.rollback()
                    db_category = db.query(models.Category).filter(models.Category.name == category_name).first()

            # Create transaction
            db_transaction = models.Transaction(
                account_id=request.account_id,
                date=normalized_data["date"],
                amount=normalized_data["amount"],
                merchant=normalized_data["merchant"],
                description=normalized_data["description"],
                category_id=db_category.id,
                transaction_type=transaction_type,
                source=normalized_data["source"],
                raw_data=normalized_data["raw_data"]
            )
            db.add(db_transaction)
            created_transactions.append(db_transaction)

        db.commit()
        for tx in created_transactions:
            db.refresh(tx)

        return created_transactions
