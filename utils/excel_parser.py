import pandas as pd

# --- Replicated from csv_parser.py (Ideally, this would be in a shared util module) ---
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
        for col in df_columns: # Case-insensitive check
            if col.lower() == name.lower():
                return col
    return None
# --- End of replicated code ---

def parse_excel(file_path: str) -> pd.DataFrame | None:
    """
    Parses an Excel file (XLS, XLSX) into a pandas DataFrame,
    standardizes column names, and handles multiple sheets by loading the first one.
    """
    print(f"Attempting to parse Excel file: {file_path}")
    try:
        # Check for multiple sheets
        excel_file = pd.ExcelFile(file_path)
        sheet_names = excel_file.sheet_names

        sheet_to_load = 0 # Default to the first sheet
        if len(sheet_names) > 1:
            print(f"Multiple sheets found: {sheet_names}. Loading the first sheet: '{sheet_names[0]}'.")
            # Placeholder for prompting user:
            # user_choice = request_user_input(f"Multiple sheets found: {sheet_names}. Which sheet contains the bank statement data? (Enter sheet name or number)")
            # sheet_to_load = user_choice or sheet_names[0]
            # For now, we always pick the first one.

        # Load the selected sheet (first one by default)
        df = pd.read_excel(file_path, sheet_name=sheet_to_load)
        print(f"Successfully loaded sheet '{sheet_names[sheet_to_load]}' from Excel. Shape: {df.shape}")

        column_mapping = {}
        identified_columns = {}

        for standard_col_name, common_options in COMMON_COLUMN_HEADERS.items():
            found_col_name = find_column_name(df.columns, common_options)
            if found_col_name:
                column_mapping[found_col_name] = standard_col_name
                identified_columns[standard_col_name] = found_col_name
            elif standard_col_name in REQUIRED_COLUMNS:
                print(f"Warning: Required column '{standard_col_name}' could not be automatically identified in sheet '{sheet_names[sheet_to_load]}' from headers: {list(df.columns)}")
                # Placeholder for user prompt

        df_renamed = df.rename(columns=column_mapping)

        missing_required = [rc for rc in REQUIRED_COLUMNS if rc not in df_renamed.columns]
        if missing_required:
            print(f"Error: Missing required columns in sheet '{sheet_names[sheet_to_load]}' after attempting to map: {missing_required}. Identified: {identified_columns}")
            # Placeholder for prompting user for mapping
            return None

        print(f"Columns identified and mapped in sheet '{sheet_names[sheet_to_load]}': {identified_columns}")
        return df_renamed

    except FileNotFoundError:
        print(f"Error: Excel file not found at {file_path}")
        return None
    except pd.errors.EmptyDataError: # Though read_excel might raise other errors for empty sheets
        print(f"Error: Excel file or the selected sheet is empty: {file_path}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while parsing Excel: {e}")
        return None

if __name__ == '__main__':
    # Create dummy Excel files for testing
    dummy_excel_path_ok_xlsx = "dummy_statement_ok.xlsx"
    dummy_excel_path_multi_sheet_xlsx = "dummy_statement_multi.xlsx"

    # Test case 1: Good Excel (.xlsx)
    df_ok_data = {
        'Transaction Date': ['01/01/2023', '01/02/2023'],
        'Description': ['Grocery Store', 'Salary'],
        'Debit': [50.00, None],
        'Credit': [None, 2000.00]
    }
    pd.DataFrame(df_ok_data).to_excel(dummy_excel_path_ok_xlsx, index=False, sheet_name="Transactions")

    # Test case 2: Excel with multiple sheets (.xlsx)
    with pd.ExcelWriter(dummy_excel_path_multi_sheet_xlsx) as writer:
        pd.DataFrame({
            'Date': ['01/03/2023'], 'Details': ['Refund'], 'Amount Credited': [10.00]
        }).to_excel(writer, index=False, sheet_name="Statement1")
        pd.DataFrame({
            'Other Data': ['Info A', 'Info B']
        }).to_excel(writer, index=False, sheet_name="SummarySheet")

    print("--- Testing Excel Parser ---")

    print("\n--- Test Case 1: OK XLSX ---")
    df1 = parse_excel(dummy_excel_path_ok_xlsx)
    if df1 is not None:
        print(df1.head())

    print("\n--- Test Case 2: Multi-sheet XLSX (loading first sheet) ---")
    df2 = parse_excel(dummy_excel_path_multi_sheet_xlsx)
    if df2 is not None:
        print(df2.head()) # Should be data from "Statement1"

    # Clean up
    import os
    os.remove(dummy_excel_path_ok_xlsx)
    os.remove(dummy_excel_path_multi_sheet_xlsx)
    print("\nRemoved dummy Excel files.")
