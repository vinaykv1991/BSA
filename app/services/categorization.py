from typing import Dict, Any, Optional

class CategorizationService:
    DEFAULT_RULES = {
        "AMAZON": "Shopping",
        "FLIPKART": "Shopping",
        "UBER": "Travel",
        "OLA": "Travel",
        "ZOMATO": "Food",
        "SWIGGY": "Food",
        "NETFLIX": "Entertainment",
        "SPOTIFY": "Entertainment",
        "AIRTEL": "Utilities",
        "JIO": "Utilities",
        "HDFC": "Investment", # Simplified
        "RENT": "Fixed",
        "SALARY": "Income"
    }

    @classmethod
    def categorize(cls, merchant: str, description: str) -> Dict[str, str]:
        # Rule-based categorization
        merchant_upper = merchant.upper()
        description_upper = description.upper()

        for keyword, category in cls.DEFAULT_RULES.items():
            if keyword in merchant_upper or keyword in description_upper:
                tx_type = "Earning" if category == "Income" else "Spending"
                return {"category": category, "type": tx_type}

        # LLM Fallback Placeholder
        cat = cls.llm_categorize_fallback(merchant, description)
        return {"category": cat, "type": "Spending"}

    @staticmethod
    def llm_categorize_fallback(merchant: str, description: str) -> str:
        # In a real app, this would call an LLM API
        # print(f"Calling LLM fallback for: {merchant}")
        return "Miscellaneous"
