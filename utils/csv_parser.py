import pandas as pd

# Define common header names for required columns
COMMON_COLUMN_HEADERS = {
    'Date': ['Date', 'Transaction Date', 'Posting Date'],
    'Description': ['Description', 'Narrative', 'Particulars', 'Details', 'Transaction Details'],
    'Debit': ['Debit', 'Withdrawal', 'Withdrawals', 'Amount Debited', 'Payment'],
    'Credit': ['Credit', 'Deposit', 'Deposits', 'Amount Credited', 'Receipt']
}

REQUIRED_COLUMNS = ['Date', 'Description', 'Debit', 'Credit']

def find_column_name(df_columns, common_names_list):
    """Helper function to find the first matching column name from a list of common names."""
    for name in common_names_list:
        if name in df_columns:
            return name
        # Also check for case-insensitive matches
        for col in df_columns:
            if col.lower() == name.lower():
                return col
    return None

def parse_csv(file_path: str) -> pd.DataFrame | None:
    """
    Parses a CSV file into a pandas DataFrame and standardizes column names.
    """
    print(f"Attempting to parse CSV: {file_path}")
    try:
        df = pd.read_csv(file_path)
        print(f"Successfully loaded CSV into DataFrame. Shape: {df.shape}")

        column_mapping = {}
        identified_columns = {} # To store actual names found

        for standard_col_name, common_options in COMMON_COLUMN_HEADERS.items():
            found_col_name = find_column_name(df.columns, common_options)
            if found_col_name:
                column_mapping[found_col_name] = standard_col_name
                identified_columns[standard_col_name] = found_col_name
            elif standard_col_name in REQUIRED_COLUMNS:
                # For now, print a message. User prompt would be more complex.
                print(f"Warning: Required column '{standard_col_name}' could not be automatically identified from headers: {list(df.columns)}")
                # In a real scenario: request_user_input(f"Please specify the column for {standard_col_name}.")
                # For now, we'll allow processing to continue, but it might fail later if column is missing.
                # Alternatively, return None here if strict adherence is needed.

        # Rename columns to standard names
        df_renamed = df.rename(columns=column_mapping)

        # Check if all *required* columns are present after renaming attempt
        missing_required = [rc for rc in REQUIRED_COLUMNS if rc not in df_renamed.columns]
        if missing_required:
            print(f"Error: Missing required columns after attempting to map: {missing_required}. Identified: {identified_columns}")
            print("Please ensure your CSV has identifiable columns for Date, Description, Debit, and Credit.")
            # Placeholder for prompting user for mapping:
            # print("User prompt needed: 'Please specify the columns for Date, Description, Debit, and Credit.'")
            return None

        print(f"Columns identified and mapped: {identified_columns}")

        # Keep only the standardized columns, plus any others that were not mapped (optional)
        # For now, let's select only the required ones and any other potentially useful ones.
        # This step can be adjusted based on whether to keep all original columns or only standardized ones.
        # For simplicity, let's just ensure the required ones are there.
        # We can decide later if we need to subset to only REQUIRED_COLUMNS or keep others.

        return df_renamed

    except FileNotFoundError:
        print(f"Error: CSV file not found at {file_path}")
        return None
    except pd.errors.EmptyDataError:
        print(f"Error: CSV file is empty: {file_path}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while parsing CSV: {e}")
        return None

if __name__ == '__main__':
    # Create dummy CSV files for testing
    dummy_csv_path_ok = "dummy_statement_ok.csv"
    dummy_csv_path_missing = "dummy_statement_missing.csv"
    dummy_csv_path_custom_headers = "dummy_statement_custom_headers.csv"

    # Test case 1: Good CSV
    with open(dummy_csv_path_ok, 'w') as f:
        f.write("Transaction Date,Description,Debit,Credit\n")
        f.write("01/01/2023,Grocery Store,50.00,\n")
        f.write("01/02/2023,Salary,,2000.00\n")

    # Test case 2: CSV with a missing required column (e.g., no recognizable Debit)
    with open(dummy_csv_path_missing, 'w') as f:
        f.write("Date,Particulars,Amount Credited\n") # Missing Debit
        f.write("01/03/2023,Refund,10.00\n")

    # Test case 3: CSV with different but common headers
    with open(dummy_csv_path_custom_headers, 'w') as f:
        f.write("Posting Date,Transaction Details,Withdrawal,Deposit\n")
        f.write("01/04/2023,Online Purchase,75.50,\n")
        f.write("01/05/2023,Client Payment,,500.00\n")

    print("--- Testing CSV Parser ---")

    print("\n--- Test Case 1: OK CSV ---")
    df1 = parse_csv(dummy_csv_path_ok)
    if df1 is not None:
        print(df1.head())

    print("\n--- Test Case 2: Missing Column CSV ---")
    df2 = parse_csv(dummy_csv_path_missing)
    if df2 is not None:
        print(df2.head())
    else:
        print("Parsing failed or returned None as expected for missing column CSV.")

    print("\n--- Test Case 3: Custom Headers CSV ---")
    df3 = parse_csv(dummy_csv_path_custom_headers)
    if df3 is not None:
        print(df3.head())

    # Clean up
    import os
    os.remove(dummy_csv_path_ok)
    os.remove(dummy_csv_path_missing)
    os.remove(dummy_csv_path_custom_headers)
    print("\nRemoved dummy CSV files.")
