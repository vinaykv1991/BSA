import os
import pandas as pd
import json
import argparse # New import
import time # For potential future use, e.g. FILE_UPLOAD_TIMEOUT if interactive mode added

# --- Utility Imports ---
from utils.pdf_parser import parse_pdf
from utils.csv_parser import parse_csv
from utils.excel_parser import parse_excel
from utils.data_preprocessor import preprocess_data
from utils.categorizer import categorize_transactions, refine_categories_with_user_feedback
from utils.summary_generator import generate_monthly_summary_text
from utils.chart_generator import request_and_generate_charts


# --- Global In-Memory Storage Structures ---
monthly_earnings_summary = {}
monthly_spendings_summary = {}
MASTER_EARNINGS_COLUMNS = ['Date', 'Description', 'Amount', 'Category', 'Year', 'Month']
MASTER_SPENDINGS_COLUMNS = ['Date', 'Description', 'Amount', 'Category', 'Year', 'Month']
master_earnings_transactions = pd.DataFrame(columns=MASTER_EARNINGS_COLUMNS)
master_spendings_transactions = pd.DataFrame(columns=MASTER_SPENDINGS_COLUMNS)

# --- Plan for Persistence (Conceptual) ---
# (Comments from previous step remain here)
# To enable long-term memory of analyzed transactions and summaries,
# the following functions could be implemented:
#
# 1. save_data_to_disk(storage_dir: str = "app_data"):
#    - Purpose: To save the current state of the in-memory storage structures to disk.
#    - Actions:
#      - Create the `storage_dir` if it doesn't exist.
#      - master_earnings_transactions.to_parquet(os.path.join(storage_dir, "master_earnings.parquet"))
#      - master_spendings_transactions.to_parquet(os.path.join(storage_dir, "master_spendings.parquet"))
#      - with open(os.path.join(storage_dir, "monthly_earnings_summary.json"), 'w') as f:
#          json.dump(monthly_earnings_summary, f, indent=4)
#      - with open(os.path.join(storage_dir, "monthly_spendings_summary.json"), 'w') as f:
#          json.dump(monthly_spendings_summary, f, indent=4)
#    - Trigger: Could be called at the end of a processing session, periodically,
#               or upon explicit user action (e.g., "Save Data").
#
# 2. load_data_from_disk(storage_dir: str = "app_data"):
#    - Purpose: To load previously saved data from disk into the in-memory storage structures.
#    - Actions:
#      - Check if `storage_dir` and the respective files exist.
#      - If master_earnings.parquet exists:
#          master_earnings_transactions = pd.read_parquet(os.path.join(storage_dir, "master_earnings.parquet"))
#      - If master_spendings.parquet exists:
#          master_spendings_transactions = pd.read_parquet(os.path.join(storage_dir, "master_spendings.parquet"))
#      - If monthly_earnings_summary.json exists:
#          with open(os.path.join(storage_dir, "monthly_earnings_summary.json"), 'r') as f:
#              monthly_earnings_summary = json.load(f)
#      - If monthly_spendings_summary.json exists:
#          with open(os.path.join(storage_dir, "monthly_spendings_summary.json"), 'r') as f:
#              monthly_spendings_summary = json.load(f)
#    - Trigger: Would be called at the beginning of the application/script execution
#               to restore state from a previous session.
#
# - Alternative for DataFrames: SQLite database for more robust querying and transactional safety.
#   Each DataFrame could be a table in the SQLite DB.
#   Example:
#     import sqlite3
#     conn = sqlite3.connect(os.path.join(storage_dir, "bank_analysis.db"))
#     master_earnings_transactions.to_sql("master_earnings", conn, if_exists="replace", index=False)
#     # ... and for loading:
#     # master_earnings_transactions = pd.read_sql("SELECT * FROM master_earnings", conn)
#     conn.close()
#
# - User Keyword Customization:
#   - Persisting user-defined keywords (from the feedback loop) would also be crucial.
#   - This could be a simple JSON file storing lists/dictionaries of keywords.
#   - `save_keywords(keywords_path="user_keywords.json")`
#   - `load_keywords(keywords_path="user_keywords.json")` -> returns keyword dicts
#     These would then be passed to `categorize_transactions`.


ACCEPTED_FORMATS = ['.pdf', '.csv', '.xls', '.xlsx']
# FILE_UPLOAD_TIMEOUT = 60 # Less relevant for CLI based input

# --- Core Processing Functions ---

def get_file_extension_valid(filepath: str) -> bool:
    """Checks if the file extension is in ACCEPTED_FORMATS."""
    if not os.path.isfile(filepath): # Check if it's a file first
        print(f"Input path is not a file: '{filepath}'")
        return False
    _, file_extension = os.path.splitext(filepath)
    if file_extension.lower() not in ACCEPTED_FORMATS:
        print(f"Unsupported file format for '{filepath}': {file_extension}. Supported: {', '.join(ACCEPTED_FORMATS)}.")
        return False
    return True

def update_storage(categorized_df: pd.DataFrame):
    """
    Updates the global in-memory storage structures with categorized transactions.
    """
    global monthly_earnings_summary, monthly_spendings_summary
    global master_earnings_transactions, master_spendings_transactions

    if categorized_df is None or categorized_df.empty:
        print("Update Storage: Received empty or None DataFrame. No updates will be made.")
        return

    required_cols_for_storage = ['Date', 'Description', 'Debit', 'Credit', 'Category', 'Year', 'Month', 'Transaction_Type']
    for col in required_cols_for_storage:
        if col not in categorized_df.columns:
            print(f"Update Storage Error: DataFrame is missing required column '{col}'. Skipping storage update for this item.")
            return

    earnings_df = categorized_df[categorized_df['Transaction_Type'] == 'Earning'].copy()
    spendings_df = categorized_df[categorized_df['Transaction_Type'] == 'Spending'].copy()

    if not earnings_df.empty:
        earnings_df.rename(columns={'Credit': 'Amount'}, inplace=True)
        if 'Amount' not in earnings_df.columns and 'Credit' in earnings_df.columns:
             earnings_df['Amount'] = earnings_df['Credit']

        current_cols = earnings_df.columns.tolist()
        cols_to_add = [col for col in MASTER_EARNINGS_COLUMNS if col not in current_cols]
        for col in cols_to_add: earnings_df[col] = None # Add missing master columns with None

        if 'Amount' in earnings_df.columns: # Ensure 'Amount' is present before concat
            master_earnings_transactions = pd.concat(
                [master_earnings_transactions, earnings_df[MASTER_EARNINGS_COLUMNS]],
                ignore_index=True
            )
        else:
            print("Update Storage: 'Amount' column (from 'Credit') missing in earnings_df. Cannot update master_earnings_transactions.")


    if not spendings_df.empty:
        spendings_df.rename(columns={'Debit': 'Amount'}, inplace=True)
        if 'Amount' not in spendings_df.columns and 'Debit' in spendings_df.columns:
            spendings_df['Amount'] = spendings_df['Debit']

        current_cols = spendings_df.columns.tolist()
        cols_to_add = [col for col in MASTER_SPENDINGS_COLUMNS if col not in current_cols]
        for col in cols_to_add: spendings_df[col] = None

        if 'Amount' in spendings_df.columns:
            master_spendings_transactions = pd.concat(
                [master_spendings_transactions, spendings_df[MASTER_SPENDINGS_COLUMNS]],
                ignore_index=True
            )
        else:
            print("Update Storage: 'Amount' column (from 'Debit') missing in spendings_df. Cannot update master_spendings_transactions.")


    if not earnings_df.empty and 'Amount' in earnings_df.columns and earnings_df['Amount'].notna().any():
        valid_earnings = earnings_df.dropna(subset=['Year', 'Month', 'Category', 'Amount'])
        if not valid_earnings.empty:
            valid_earnings['Year'] = valid_earnings['Year'].astype(int)
            valid_earnings['Month'] = valid_earnings['Month'].astype(int)
            monthly_earning_groups = valid_earnings.groupby(['Year', 'Month', 'Category'])['Amount'].sum().reset_index()
            for _, row in monthly_earning_groups.iterrows():
                year_month_str = f"{int(row['Year'])}-{int(row['Month']):02d}"
                category = row['Category']
                amount = row['Amount']
                monthly_earnings_summary.setdefault(year_month_str, {}).setdefault(category, 0.0) # Ensure float
                monthly_earnings_summary[year_month_str][category] += amount
            print("Updated monthly_earnings_summary.")

    if not spendings_df.empty and 'Amount' in spendings_df.columns and spendings_df['Amount'].notna().any():
        valid_spendings = spendings_df.dropna(subset=['Year', 'Month', 'Category', 'Amount'])
        if not valid_spendings.empty:
            valid_spendings['Year'] = valid_spendings['Year'].astype(int)
            valid_spendings['Month'] = valid_spendings['Month'].astype(int)
            monthly_spending_groups = valid_spendings.groupby(['Year', 'Month', 'Category'])['Amount'].sum().reset_index()
            for _, row in monthly_spending_groups.iterrows():
                year_month_str = f"{int(row['Year'])}-{int(row['Month']):02d}"
                category = row['Category']
                amount = row['Amount']
                monthly_spendings_summary.setdefault(year_month_str, {}).setdefault(category, 0.0) # Ensure float
                monthly_spendings_summary[year_month_str][category] += amount
            print("Updated monthly_spendings_summary.")

def process_bank_statement(file_path: str) -> pd.DataFrame | None:
    """
    Main processing function for a single bank statement file.
    Orchestrates parsing, preprocessing, categorization, user feedback (placeholder), and storage updates.
    Returns the categorized DataFrame for that file.
    """
    if not os.path.exists(file_path): # Should be caught by get_file_extension_valid if called first
        print(f"Error: File not found: '{file_path}'")
        return None
    # Validation is now done before calling this in __main__

    print(f"\n--- Starting processing for: {file_path} ---")
    _, file_extension = os.path.splitext(file_path)
    file_extension = file_extension.lower()

    raw_df = None
    if file_extension == '.pdf':
        print("Detected PDF file. Using PDF parser.")
        raw_df = parse_pdf(file_path)
    elif file_extension == '.csv':
        print("Detected CSV file. Using CSV parser.")
        raw_df = parse_csv(file_path)
    elif file_extension in ['.xls', '.xlsx']:
        print("Detected Excel file. Using Excel parser.")
        raw_df = parse_excel(file_path)
    else:
        # This should ideally not be reached if get_file_extension_valid is checked before.
        print(f"Critical Error: Unsupported file type '{file_extension}' passed to process_bank_statement for file '{file_path}'.")
        return None

    if raw_df is None or raw_df.empty:
        print(f"Parsing failed or returned no data for {file_path}.")
        return None
    print(f"Successfully parsed {file_path}. Raw DataFrame shape: {raw_df.shape}")

    preprocessed_df = preprocess_data(raw_df)
    if preprocessed_df is None or preprocessed_df.empty:
        print(f"Data preprocessing failed or returned no data for {file_path}.")
        return None
    print(f"Successfully preprocessed data. DataFrame shape: {preprocessed_df.shape}")

    categorized_df = categorize_transactions(preprocessed_df)
    if categorized_df is None or categorized_df.empty:
        print(f"Transaction categorization failed for {file_path}.")
        return None # Or return preprocessed_df if partial result is acceptable
    print(f"Successfully categorized transactions. DataFrame shape: {categorized_df.shape}")

    refine_categories_with_user_feedback(categorized_df) # Placeholder call

    print("--- Updating In-Memory Storage ---")
    update_storage(categorized_df)

    print(f"--- Finished processing for: {file_path} ---")
    return categorized_df


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Bank Statement Analyzer CLI: Processes bank statement files, categorizes transactions, and generates summaries.",
        formatter_class=argparse.RawTextHelpFormatter # For better help text formatting
    )
    parser.add_argument(
        'files',
        metavar='FILE',
        type=str,
        nargs='+', # Requires at least one file argument.
        help='One or more bank statement files to analyze.\nSupported formats: PDF, CSV, XLS, XLSX.'
    )
    parser.add_argument(
        '--charts_dir',
        type=str,
        default="generated_charts",
        help='Directory where generated charts will be saved (default: "generated_charts").'
    )
    # Example of a potential future argument for loading data
    # parser.add_argument('--load_data', action='store_true', help='Load previously saved data before processing new files.')

    args = parser.parse_args()

    input_files_from_cli = args.files
    charts_output_directory = args.charts_dir

    # if args.load_data:
    #     print("Attempting to load previously saved data...")
    #     # load_data_from_disk() # Conceptual call

    valid_input_files = []
    if input_files_from_cli:
        for f_path in input_files_from_cli:
            if get_file_extension_valid(f_path): # Validates existence and extension
                valid_input_files.append(f_path)
            else:
                print(f"Skipping invalid or unsupported file: {f_path}")

    if not valid_input_files:
        print("No valid input files to process after validation.")
        if not input_files_from_cli: # If initial list was empty (should be caught by nargs='+')
             parser.print_help()
    else:
        print(f"\nProcessing {len(valid_input_files)} valid file(s): {', '.join(valid_input_files)}")
        if charts_output_directory:
            print(f"Charts will be saved to directory: '{os.path.abspath(charts_output_directory)}'")

        successful_files_count = 0
        for file_path in valid_input_files:
            # print(f"\n****************************************************") # Reduced verbosity
            # print(f"Attempting to process file: {file_path}")
            processed_data_single_file = process_bank_statement(file_path)
            if processed_data_single_file is not None and not processed_data_single_file.empty:
                successful_files_count +=1
                # print(f"Successfully processed and extracted data from: {file_path}") # Part of process_bank_statement now
            else:
                print(f"Processing for {file_path} resulted in no data or an error.")
            # print(f"****************************************************")

        print(f"\n--- Overall Processing Summary ---")
        print(f"Total files provided: {len(input_files_from_cli)}.")
        print(f"Valid files attempted: {len(valid_input_files)}.")
        print(f"Successfully processed files: {successful_files_count}.")

        if successful_files_count == 0:
            print("\nNo transactions were extracted from any file. Skipping final summaries and charts.")
        else:
            print("\n--- In-Memory Data Overview (Aggregated from all processed files) ---")
            if not master_earnings_transactions.empty:
                print(f"Master Earnings Transactions: {len(master_earnings_transactions)} rows (First 5 shown below)")
                print(master_earnings_transactions.head().to_string())
            else:
                print("Master Earnings Transactions: (No earnings transactions recorded)")

            if not master_spendings_transactions.empty:
                print(f"Master Spendings Transactions: {len(master_spendings_transactions)} rows (First 5 shown below)")
                print(master_spendings_transactions.head().to_string())
            else:
                print("Master Spendings Transactions: (No spendings transactions recorded)")

            print("\nMonthly Earnings Summary (Aggregated):")
            print(json.dumps(monthly_earnings_summary, indent=4, sort_keys=True) if monthly_earnings_summary else " (No earnings summary)")

            print("\nMonthly Spendings Summary (Aggregated):")
            print(json.dumps(monthly_spendings_summary, indent=4, sort_keys=True) if monthly_spendings_summary else " (No spendings summary)")

            print("\n\n--- Generated Monthly Financial Text Summary (Aggregated) ---")
            financial_summary_text = generate_monthly_summary_text(monthly_earnings_summary, monthly_spendings_summary)
            print(financial_summary_text)

            request_and_generate_charts(
                monthly_earnings_summary,
                monthly_spendings_summary,
                master_spendings_transactions,
                master_earnings_transactions,
                output_dir=charts_output_directory
            )

    print("\nApplication finished.")
