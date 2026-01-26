import unittest
from datetime import datetime, UTC
from app.services.normalization import NormalizationService
from app.services.categorization import CategorizationService

class TestServices(unittest.TestCase):
    def test_sms_parsing_hdfc(self):
        sms = "INR 1,245.00 spent on HDFC Credit Card at AMAZON on 22-Jan"
        result = NormalizationService.parse_sms(sms)
        self.assertEqual(result["amount"], 1245.0)
        self.assertEqual(result["merchant"], "AMAZON")
        self.assertEqual(result["account_name"], "HDFC Credit Card")
        self.assertEqual(result["date"].day, 22)
        self.assertEqual(result["date"].month, 1)

    def test_sms_parsing_generic(self):
        sms = "Spent 500 at Zomato using Debit Card"
        result = NormalizationService.parse_sms(sms)
        self.assertEqual(result["amount"], 500.0)
        self.assertEqual(result["merchant"], "Zomato")
        self.assertEqual(result["account_name"], "Debit Card")

    def test_categorization(self):
        res = CategorizationService.categorize("AMAZON", "Purchase at Amazon")
        self.assertEqual(res["category"], "Shopping")
        self.assertEqual(res["type"], "Spending")

        res = CategorizationService.categorize("SALARY", "Monthly salary")
        self.assertEqual(res["category"], "Income")
        self.assertEqual(res["type"], "Earning")

        res = CategorizationService.categorize("UNKNOWN", "Something else")
        self.assertEqual(res["category"], "Miscellaneous")
        self.assertEqual(res["type"], "Spending")

    def test_pdf_parsing_mock(self):
        # Since creating a real PDF in unit test might be heavy, we can at least test the logic
        # But we already have reportlab, so let is do it.
        import io
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
        from reportlab.lib import colors
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer)
        data = [["Date", "Description", "Amount"], ["01/01/2026", "TEST", "100.0"]]
        t = Table(data)
        t.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 1, colors.black)]))
        doc.build([t])
        pdf_bytes = buffer.getvalue()

        result = NormalizationService.parse_pdf(pdf_bytes)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["amount"], 100.0)
        self.assertEqual(result[0]["merchant"], "TEST")

if __name__ == "__main__":
    unittest.main()
