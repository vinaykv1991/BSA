import pandas as pd
import re

def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Performs universal data preprocessing on the input DataFrame.
    Assumes df has 'Date', 'Description', 'Debit', 'Credit' columns.
    """
    if df is None or df.empty:
        print("Preprocessor received an empty or None DataFrame.")
        return pd.DataFrame() # Return empty DF to avoid downstream errors

    processed_df = df.copy()

    # 1. Date Conversion
    if 'Date' in processed_df.columns:
        try:
            # Attempt to infer datetime format, then standardize
            # errors='coerce' will turn unparseable dates into NaT (Not a Time)
            processed_df['Date'] = pd.to_datetime(processed_df['Date'], errors='coerce')
            # Check if all dates became NaT, which indicates a parsing problem
            if processed_df['Date'].isnull().all() and not df['Date'].empty : # Add check for initially empty Date column
                print("Warning: All dates failed to parse. Please check the 'Date' column format.")
            else:
                # Log how many dates failed to parse if any
                failed_dates = processed_df['Date'].isnull().sum()
                if failed_dates > 0:
                    print(f"Warning: {failed_dates} out of {len(processed_df)} dates failed to parse and were set to NaT.")
            # Standard format YYYY-MM-DD (handled by to_datetime, for display use .dt.strftime('%Y-%m-%d'))
            # The actual object in pandas is Timestamp, which is fine.
        except Exception as e:
            print(f"Error during date conversion: {e}. 'Date' column might not be in a recognizable format.")
            # Potentially drop rows with unparseable dates or flag them
            processed_df['Date'] = pd.NaT # Set all to NaT if a general error occurs
    else:
        print("Warning: 'Date' column not found for preprocessing. Creating it as NaT.")
        # Add an empty Date column if missing to prevent errors later, though this is not ideal
        processed_df['Date'] = pd.NaT


    # 2. Amount Conversion (Debit and Credit)
    amount_columns = ['Debit', 'Credit']
    for col_name in amount_columns:
        if col_name in processed_df.columns:
            # Convert to string first to handle mixed types and apply string methods
            processed_df[col_name] = processed_df[col_name].astype(str)
            # Remove currency symbols, commas, and other non-numeric characters (except decimal point and minus sign)
            processed_df[col_name] = processed_df[col_name].apply(
                lambda x: re.sub(r"[^\d\.\-]", "", str(x)) if pd.notnull(x) else x
            )
            # Convert to numeric, coercing errors to NaN
            processed_df[col_name] = pd.to_numeric(processed_df[col_name], errors='coerce')
            # Replace NaN with 0.0
            processed_df[col_name] = processed_df[col_name].fillna(0.0)
        else:
            print(f"Warning: '{col_name}' column not found for preprocessing. Creating it with 0.0.")
            processed_df[col_name] = 0.0

    # 3. Transaction Type Assignment
    # Ensure Debit and Credit columns exist after previous step
    if 'Debit' not in processed_df.columns: processed_df['Debit'] = 0.0
    if 'Credit' not in processed_df.columns: processed_df['Credit'] = 0.0

    processed_df['Transaction_Type'] = 'Undefined' # Default

    # Iterate row by row for clarity in logic, can be optimized with apply or np.select
    for index, row in processed_df.iterrows():
        debit = row['Debit']
        credit = row['Credit']
        transaction_type = 'Undefined'

        if credit > 0 and debit == 0:
            transaction_type = 'Earning'
        elif debit > 0 and credit == 0:
            transaction_type = 'Spending'
        elif debit > 0 and credit > 0:
            print(f"Warning: Transaction at index {index} has both Debit ({debit}) and Credit ({credit}) values.")
            if debit > credit:
                transaction_type = 'Spending' # Prioritize Spending
                print(f"  Classified as 'Spending' (Debit > Credit). Description: {row.get('Description', 'N/A')}")
            else:
                transaction_type = 'Earning' # Prioritize Earning (includes Debit == Credit)
                print(f"  Classified as 'Earning' (Credit >= Debit). Description: {row.get('Description', 'N/A')}")
        # Case: debit == 0 and credit == 0 (already handled by default or if no specific condition met)
        # Or one is negative, etc. - current logic focuses on positive values.

        processed_df.loc[index, 'Transaction_Type'] = transaction_type

    # 4. Monthly Perioding (Year and Month)
    if 'Date' in processed_df.columns and not processed_df['Date'].isnull().all():
        valid_dates = processed_df['Date'].notna()
        processed_df.loc[valid_dates, 'Year'] = processed_df.loc[valid_dates, 'Date'].dt.year
        processed_df.loc[valid_dates, 'Month'] = processed_df.loc[valid_dates, 'Date'].dt.month
        # Fill NaN for Year/Month where Date is NaT
        processed_df['Year'] = processed_df['Year'].fillna(0).astype(int)
        processed_df['Month'] = processed_df['Month'].fillna(0).astype(int)
    else:
        print("Warning: 'Date' column is missing or all dates are invalid; 'Year' and 'Month' columns will be empty or zero.")
        processed_df['Year'] = 0
        processed_df['Month'] = 0

    print("Data preprocessing complete.")
    return processed_df

if __name__ == '__main__':
    # Create a sample DataFrame for testing
    sample_data = {
        'Date': ['01/25/2023', 'Jan 30 2023', '2023-02-15', 'Invalid Date', '05/10/2023'],
        'Description': ['Salary', 'Groceries', 'Freelance Gig', 'Refund', 'Utilities'],
        'Debit': ['$50.00', '25.99', None, 'N/A', '120.00'], # Mixed types, currency symbols
        'Credit': [None, None, '€1,500.00', '20.00', None], # Mixed types, currency symbols
        'Extra_Col': [1,2,3,4,5] # To ensure it's preserved
    }
    test_df = pd.DataFrame(sample_data)

    # Simulate a case where Debit/Credit might be numbers already
    test_df_numeric_amounts = pd.DataFrame({
        'Date': ['03/15/2023', '03/20/2023'],
        'Description': ['Consulting', 'Software Subscription'],
        'Debit': [None, 75.0], # Debit is float
        'Credit': [2500.0, None]  # Credit is float
    })

    # Simulate a case with both debit and credit populated
    test_df_both_amounts = pd.DataFrame({
        'Date': ['04/10/2023', '04/12/2023', '04/15/2023'],
        'Description': ['Complex Transaction 1', 'Complex Transaction 2', 'ZeroBoth'],
        'Debit': [100.00, 50.00, 0.00],
        'Credit': [20.00, 80.00, 0.00]
    })


    print("--- Testing Data Preprocessor ---")
    print("\n--- Test Case 1: Mixed Data Types ---")
    processed_df1 = preprocess_data(test_df.copy()) # Use .copy() to avoid modifying original test_df
    print(processed_df1.to_string())
    print("\n--- Data Types After Preprocessing (Test Case 1) ---")
    print(processed_df1.dtypes)

    print("\n--- Test Case 2: Numeric Amounts ---")
    processed_df2 = preprocess_data(test_df_numeric_amounts.copy())
    print(processed_df2.to_string())
    print("\n--- Data Types After Preprocessing (Test Case 2) ---")
    print(processed_df2.dtypes)

    print("\n--- Test Case 3: Both Debit and Credit Populated ---")
    processed_df3 = preprocess_data(test_df_both_amounts.copy())
    print(processed_df3.to_string())
    print("\n--- Data Types After Preprocessing (Test Case 3) ---")
    print(processed_df3.dtypes)

    print("\n--- Test Case 4: Empty DataFrame ---")
    empty_df = pd.DataFrame()
    processed_empty_df = preprocess_data(empty_df.copy())
    print(processed_empty_df.to_string())
    print("\n--- Data Types After Preprocessing (Empty DF) ---")
    print(processed_empty_df.dtypes)

    print("\n--- Test Case 5: DataFrame with missing standard columns ---")
    missing_cols_df = pd.DataFrame({'Random': ['data']})
    processed_missing_cols_df = preprocess_data(missing_cols_df.copy())
    print(processed_missing_cols_df.to_string())
    print("\n--- Data Types After Preprocessing (Missing Cols DF) ---")
    print(processed_missing_cols_df.dtypes)
