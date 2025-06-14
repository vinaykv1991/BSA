import pandas as pd
import re # For more sophisticated matching, like whole word

# Initial Keyword Sets (as simple lists, category will be the keyword itself)
DEFAULT_EARNINGS_KEYWORDS = [
    'Salary', 'Deposit', 'Transfer In', 'Interest', 'Refund',
    'Dividend', 'Freelance', 'Consulting', 'Reimbursement', 'Payment Received' # Added one
]

DEFAULT_SPENDINGS_KEYWORDS = [
    'Groceries', 'Restaurant', 'Fuel', 'Rent', 'Utilities', 'EMI',
    'Subscription', 'Online Purchase', 'ATM Withdrawal', 'Shopping',
    'Travel', 'Health', 'Education', 'Bill Payment', 'Food', 'Entertainment', 'Transfer Out' # Added one
]

def categorize_transactions(df: pd.DataFrame,
                           earnings_keywords: list[str] = None,
                           spendings_keywords: list[str] = None) -> pd.DataFrame:
    """
    Categorizes transactions based on keywords found in the 'Description' column.
    Adds a 'Category' column to the DataFrame.
    """
    if df is None or df.empty:
        print("Categorizer received an empty or None DataFrame.")
        # Return a copy or an empty DataFrame with expected 'Category' column if needed downstream
        if df is not None: # Ensure df is not None before trying to add a column
            df_copy = df.copy()
            df_copy['Category'] = None
            return df_copy
        return pd.DataFrame() # Return a new empty DataFrame if input was None

    categorized_df = df.copy()

    if earnings_keywords is None:
        earnings_keywords = DEFAULT_EARNINGS_KEYWORDS
    if spendings_keywords is None:
        spendings_keywords = DEFAULT_SPENDINGS_KEYWORDS

    earnings_keywords_lower = {k.lower(): k for k in earnings_keywords}
    spendings_keywords_lower = {k.lower(): k for k in spendings_keywords}

    categories = []
    for index, row in categorized_df.iterrows():
        description = str(row.get('Description', '')).lower()
        transaction_type = row.get('Transaction_Type', 'Undefined')
        assigned_category = None

        # 1. Check Earnings Keywords
        for ek_lower, ek_original in earnings_keywords_lower.items():
            if re.search(r'\b' + re.escape(ek_lower) + r'\b', description):
                assigned_category = ek_original # Use original casing for category name
                break

        # 2. Check Spendings Keywords if no earning category found
        if not assigned_category:
            for sk_lower, sk_original in spendings_keywords_lower.items():
                if re.search(r'\b' + re.escape(sk_lower) + r'\b', description):
                    assigned_category = sk_original # Use original casing
                    break

        # 3. Fallback Category
        if not assigned_category:
            if transaction_type == 'Earning':
                assigned_category = 'Miscellaneous Earnings'
            elif transaction_type == 'Spending':
                assigned_category = 'Miscellaneous Spendings'
            else: # Transaction_Type is 'Undefined' or something else
                # Attempt to infer from Debit/Credit if present and non-zero
                debit_val = row.get('Debit', 0.0)
                credit_val = row.get('Credit', 0.0)
                if credit_val > 0 and debit_val == 0:
                     assigned_category = 'Miscellaneous Earnings'
                elif debit_val > 0 and credit_val == 0:
                     assigned_category = 'Miscellaneous Spendings'
                # If still ambiguous (e.g. both > 0, or both == 0 after being non-zero before preproc)
                # or if Transaction_Type was already 'Undefined' due to debit/credit ambiguity
                else:
                    assigned_category = 'Uncategorized'

        categories.append(assigned_category)

    categorized_df['Category'] = categories
    print("Transaction categorization complete.")
    return categorized_df

if __name__ == '__main__':
    sample_data = {
        'Date': pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05', '2023-01-06', '2023-01-07', '2023-01-08']),
        'Description': [
            'Monthly Salary Payment',
            'Shell Fuel Station',
            'Received payment for Freelance project X',
            'Unknown income source',
            'Netflix Subscription',
            'Transfer to savings account', # Example of a spending keyword match
            'Restaurant ABC',
            'Cash withdrawal at ATM' # Example of multi-word keyword
        ],
        'Debit': [0, 50.00, 0, 0, 15.00, 100.00, 60.00, 200.00],
        'Credit': [3000.00, 0, 500.00, 25.00, 0, 0, 0, 0],
        'Transaction_Type': ['Earning', 'Spending', 'Earning', 'Earning', 'Spending', 'Spending', 'Spending', 'Spending'],
        'Year': [2023, 2023, 2023, 2023, 2023, 2023, 2023, 2023],
        'Month': [1, 1, 1, 1, 1, 1, 1, 1]
    }
    test_df = pd.DataFrame(sample_data)

    print("--- Testing Transaction Categorizer ---")
    print("Original DataFrame:")
    print(test_df.to_string())

    categorized_df = categorize_transactions(test_df.copy())

    print("\nCategorized DataFrame:")
    print(categorized_df[['Description', 'Transaction_Type', 'Debit', 'Credit', 'Category']].to_string())

    # Test with custom keywords
    custom_earnings_list = ['Client Alpha Payment', 'Side Hustle Gig']
    custom_spendings_list = ['My Favourite Coffee Shop', 'Local Gym Membership']

    print("\n--- Testing with Custom Keyword Lists ---")
    test_df_custom_data = {
        'Description': ['Payment from Client Alpha Payment', 'Local Gym Membership fee', 'Random stuff', 'Income from Side Hustle Gig'],
        'Transaction_Type': ['Earning', 'Spending', 'Spending', 'Earning'],
        'Debit': [0, 50, 10, 0],
        'Credit': [1000, 0, 0, 200]
    }
    test_df_custom = pd.DataFrame(test_df_custom_data)
    categorized_df_custom = categorize_transactions(test_df_custom.copy(),
                                                  earnings_keywords=custom_earnings_list,
                                                  spendings_keywords=custom_spendings_list)
    print(categorized_df_custom[['Description', 'Transaction_Type', 'Category']].to_string())

    print("\n--- Testing with Empty DataFrame ---")
    empty_df = pd.DataFrame(columns=['Description', 'Transaction_Type', 'Debit', 'Credit'])
    categorized_empty_df = categorize_transactions(empty_df.copy())
    print(categorized_empty_df.to_string())

    print("\n--- Testing with None DataFrame ---")
    none_df = None
    categorized_none_df = categorize_transactions(none_df)
    print(categorized_none_df.to_string())
