import pandas as pd
import re # For more sophisticated matching, like whole word

# Initial Keyword Sets (as simple lists, category will be the keyword itself)
DEFAULT_EARNINGS_KEYWORDS = [
    'Salary', 'Deposit', 'Transfer In', 'Interest', 'Refund',
    'Dividend', 'Freelance', 'Consulting', 'Reimbursement', 'Payment Received'
]

DEFAULT_SPENDINGS_KEYWORDS = [
    'Groceries', 'Restaurant', 'Fuel', 'Rent', 'Utilities', 'EMI',
    'Subscription', 'Online Purchase', 'ATM Withdrawal', 'Shopping',
    'Travel', 'Health', 'Education', 'Bill Payment', 'Food', 'Entertainment', 'Transfer Out'
]

def categorize_transactions(df: pd.DataFrame,
                           earnings_keywords: list[str] = None,
                           spendings_keywords: list[str] = None) -> pd.DataFrame:
    """
    Categorizes transactions based on keywords found in the 'Description' column.
    Adds a 'Category' column to the DataFrame.
    """
    if df is None:
        print("Categorizer received a None DataFrame.")
        return pd.DataFrame() # Return a new empty DataFrame if input was None
    if df.empty:
        print("Categorizer received an empty DataFrame.")
        df_copy = df.copy()
        df_copy['Category'] = None
        return df_copy

    categorized_df = df.copy()

    if earnings_keywords is None:
        earnings_keywords = DEFAULT_EARNINGS_KEYWORDS
    if spendings_keywords is None:
        spendings_keywords = DEFAULT_SPENDINGS_KEYWORDS

    earnings_keywords_lower = {k.lower(): k for k in earnings_keywords}
    spendings_keywords_lower = {k.lower(): k for k in spendings_keywords}

    categories = []
    if 'Description' not in categorized_df.columns:
        categorized_df['Description'] = "" # Ensure Description column exists
    if 'Transaction_Type' not in categorized_df.columns:
        # Ensure Transaction_Type column exists, try to infer if Debit/Credit are present
        if 'Debit' in categorized_df.columns and 'Credit' in categorized_df.columns:
             # Basic inference, can be made more robust
            categorized_df['Transaction_Type'] = categorized_df.apply(
                lambda row: 'Earning' if row['Credit'] > 0 and row['Debit'] == 0 else
                            ('Spending' if row['Debit'] > 0 and row['Credit'] == 0 else 'Undefined'),
                axis=1
            )
        else:
            categorized_df['Transaction_Type'] = "Undefined"


    for index, row in categorized_df.iterrows():
        description = str(row.get('Description', '')).lower()
        transaction_type = row.get('Transaction_Type', 'Undefined')
        assigned_category = None

        for ek_lower, ek_original in earnings_keywords_lower.items():
            if re.search(r'\b' + re.escape(ek_lower) + r'\b', description):
                assigned_category = ek_original
                break

        if not assigned_category:
            for sk_lower, sk_original in spendings_keywords_lower.items():
                if re.search(r'\b' + re.escape(sk_lower) + r'\b', description):
                    assigned_category = sk_original
                    break

        if not assigned_category:
            if transaction_type == 'Earning':
                assigned_category = 'Miscellaneous Earnings'
            elif transaction_type == 'Spending':
                assigned_category = 'Miscellaneous Spendings'
            else: # Transaction_Type is 'Undefined' or something else
                debit_val = row.get('Debit', 0.0)
                credit_val = row.get('Credit', 0.0)
                if credit_val > 0 and debit_val == 0:
                     assigned_category = 'Miscellaneous Earnings'
                elif debit_val > 0 and credit_val == 0:
                     assigned_category = 'Miscellaneous Spendings'
                else:
                    assigned_category = 'Uncategorized'

        categories.append(assigned_category)

    categorized_df['Category'] = categories
    # print("Transaction categorization complete.") # Moved to main flow for less verbose utils
    return categorized_df

def refine_categories_with_user_feedback(df: pd.DataFrame, sample_size: int = 5) -> None:
    """
    Placeholder function to simulate a user feedback loop for refining categories.
    Identifies transactions in 'Miscellaneous' or 'Uncategorized' categories
    and prints a prompt.
    """
    if df is None or df.empty or 'Category' not in df.columns:
        print("User Feedback Loop: No data or 'Category' column to refine.")
        return

    misc_categories = ['Miscellaneous Earnings', 'Miscellaneous Spendings', 'Uncategorized']
    ambiguous_transactions = df[df['Category'].isin(misc_categories)]

    if ambiguous_transactions.empty:
        print("User Feedback Loop: No transactions found in miscellaneous/uncategorized categories for feedback.")
        return

    print("\n--- User Feedback for Category Refinement ---")
    print("I've processed your transactions. Some could not be specifically categorized.")
    print("For these descriptions, please provide a suitable category or suggest new keywords:")

    # Display a sample of descriptions
    sample_to_show = ambiguous_transactions.head(sample_size)
    for index, row in sample_to_show.iterrows():
        # Ensure Description exists in the row before trying to access it
        description_text = row['Description'] if 'Description' in row and pd.notna(row['Description']) else "N/A"
        print(f"  - Description: \"{description_text}\" (Current Category: {row['Category']})")

    if len(ambiguous_transactions) > sample_size:
        print(f"  (... and {len(ambiguous_transactions) - sample_size} more such transactions)")

    print("\n(This is a placeholder. In a real application, you would be prompted to input categories/keywords here.)")
    # Future: Implement logic to capture user input and update keyword sets or re-categorize.

if __name__ == '__main__':
    sample_data = {
        'Date': pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05', '2023-01-06']),
        'Description': [
            'Monthly Salary Payment',
            'Random Cafe Purchase', # Will be Misc Spending
            'Received payment for Freelance project X',
            'Unknown income source XYZ', # Will be Misc Earning
            'Totally new type of expense', # Misc Spending
            'An item with no clear type' # Uncategorized if debit/credit are zero or ambiguous
        ],
        'Debit': [0, 22.50, 0, 0, 45.00, 0.0], # Ensure float for consistency
        'Credit': [3000.00, 0, 500.00, 25.00, 0, 0.0], # Last one is 0/0, ensure float
        'Transaction_Type': ['Earning', 'Spending', 'Earning', 'Earning', 'Spending', 'Undefined'],
    }
    test_df = pd.DataFrame(sample_data)
    # Ensure Debit/Credit columns exist for the 'Undefined' fallback in categorize_transactions
    if 'Debit' not in test_df.columns: test_df['Debit'] = 0.0
    if 'Credit' not in test_df.columns: test_df['Credit'] = 0.0


    print("--- Testing Transaction Categorizer (in categorizer.py) ---")
    categorized_df = categorize_transactions(test_df.copy())
    print("\nCategorized DataFrame:")
    print(categorized_df[['Description', 'Transaction_Type', 'Debit', 'Credit', 'Category']].to_string())

    print("\n--- Testing User Feedback Loop Placeholder ---")
    refine_categories_with_user_feedback(categorized_df)

    print("\n--- Testing Feedback Loop with No Misc Categories ---")
    all_categorized_data = {
        'Description': ['Salary', 'Groceries'],
        'Transaction_Type': ['Earning', 'Spending'],
        'Category': ['Salary', 'Groceries'], # Already well categorized
        'Debit': [0.0, 50.0], # Added Debit/Credit for consistency with expected columns
        'Credit': [5000.0, 0.0]
    }
    all_categorized_df = pd.DataFrame(all_categorized_data)
    # Ensure Transaction_Type is present, as categorize_transactions might add it if missing
    # but refine_categories_with_user_feedback doesn't strictly need it if Category is present
    all_categorized_df = categorize_transactions(all_categorized_df.copy()) # Run through categorizer to ensure all columns
    refine_categories_with_user_feedback(all_categorized_df)

    print("\n--- Testing Feedback with Empty DataFrame ---")
    empty_df = pd.DataFrame(columns=['Description', 'Transaction_Type', 'Debit', 'Credit', 'Category'])
    refine_categories_with_user_feedback(empty_df.copy())

    print("\n--- Testing Feedback with None DataFrame ---")
    refine_categories_with_user_feedback(None)
