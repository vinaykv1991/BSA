import re
import io
import pdfplumber
from datetime import datetime, UTC
from typing import Dict, Any, List, Optional

class NormalizationService:
    @staticmethod
    def parse_pdf(file_content: bytes) -> List[Dict[str, Any]]:
        transactions = []
        try:
            with pdfplumber.open(io.BytesIO(file_content)) as pdf:
                for page in pdf.pages:
                    tables = page.extract_tables()
                    for table in tables:
                        if not table:
                            continue

                        header = table[0]
                        # Heuristic: Find indexes for Date, Description, Amount/Debit/Credit
                        date_idx = -1
                        desc_idx = -1
                        amount_idx = -1
                        debit_idx = -1
                        credit_idx = -1

                        for i, col in enumerate(header):
                            if not col: continue
                            col_clean = col.lower()
                            if "date" in col_clean: date_idx = i
                            elif "description" in col_clean or "particulars" in col_clean: desc_idx = i
                            elif "amount" in col_clean: amount_idx = i
                            elif "debit" in col_clean: debit_idx = i
                            elif "credit" in col_clean: credit_idx = i

                        # Process rows
                        for row in table[1:]:
                            if not any(row): continue

                            try:
                                # Extract data based on found indexes
                                date_str = row[date_idx] if date_idx != -1 else ""
                                description = row[desc_idx] if desc_idx != -1 else "No description"

                                amount = 0.0
                                if amount_idx != -1 and row[amount_idx]:
                                    amount = float(row[amount_idx].replace(",", ""))
                                elif debit_idx != -1 and row[debit_idx]:
                                    amount = float(row[debit_idx].replace(",", ""))
                                elif credit_idx != -1 and row[credit_idx]:
                                    amount = float(row[credit_idx].replace(",", ""))

                                # Parse date (simple attempt)
                                if date_str:
                                    # Try a few common formats
                                    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d %b %Y"):
                                        try:
                                            date_obj = datetime.strptime(date_str, fmt).replace(tzinfo=UTC)
                                            break
                                        except ValueError:
                                            continue
                                    else:
                                        date_obj = datetime.now(UTC)
                                else:
                                    date_obj = datetime.now(UTC)

                                transactions.append({
                                    "amount": abs(amount),
                                    "merchant": description, # Simple merchant extraction from description
                                    "account_name": "PDF Account",
                                    "date": date_obj,
                                    "description": description,
                                    "source": "PDF",
                                    "raw_data": str(row)
                                })
                            except (ValueError, IndexError, TypeError):
                                continue
        except Exception as e:
            print(f"Error parsing PDF: {e}")

        return transactions

    SMS_PATTERNS = [
        # HDFC Style: INR 1,245.00 spent on HDFC Credit Card at AMAZON on 22-Jan
        r"INR (?P<amount>[\d,.]+) spent on (?P<account>.+) at (?P<merchant>.+) on (?P<date>.+)",
        # Generic: Spent (?P<amount>[\d,.]+) at (?P<merchant>.+) using (?P<account>.+)"
        r"Spent (?P<amount>[\d,.]+) at (?P<merchant>.+) using (?P<account>.+)"
    ]

    @classmethod
    def parse_sms(cls, sms_text: str) -> Dict[str, Any]:
        for pattern in cls.SMS_PATTERNS:
            match = re.search(pattern, sms_text, re.IGNORECASE)
            if match:
                groups = match.groupdict()
                amount_str = groups["amount"].replace(",", "")
                amount = float(amount_str)
                merchant = groups.get("merchant", "Unknown").strip()
                account_name = groups.get("account", "Default").strip()
                date_str = groups.get("date", "").strip()

                if date_str:
                    try:
                        date_obj = datetime.strptime(date_str, "%d-%b")
                        date_obj = date_obj.replace(year=datetime.now(UTC).year, tzinfo=UTC)
                    except ValueError:
                        date_obj = datetime.now(UTC)
                else:
                    date_obj = datetime.now(UTC)

                return {
                    "amount": amount,
                    "merchant": merchant,
                    "account_name": account_name,
                    "date": date_obj,
                    "description": sms_text,
                    "source": "SMS",
                    "raw_data": sms_text
                }
        return {}

    @staticmethod
    def parse_csv_row(row: Dict[str, Any]) -> Dict[str, Any]:
        amount = 0.0
        if "Debit" in row and row["Debit"]:
            amount = -float(str(row["Debit"]).replace(",", ""))
        elif "Credit" in row and row["Credit"]:
            amount = float(str(row["Credit"]).replace(",", ""))

        date_str = row.get("Date", "")
        try:
            date_obj = datetime.strptime(date_str, "%d/%m/%Y").replace(tzinfo=UTC)
        except ValueError:
            date_obj = datetime.now(UTC)

        return {
            "amount": abs(amount),
            "merchant": row.get("Description", "Unknown"),
            "account_name": "Default Bank",
            "date": date_obj,
            "description": row.get("Description", ""),
            "source": "CSV",
            "raw_data": str(row)
        }
