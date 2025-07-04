import os
import pandas as pd
import time # For FILE_UPLOAD_TIMEOUT simulation if enabled
from utils.pdf_parser import parse_pdf
from utils.csv_parser import parse_csv
from utils.excel_parser import parse_excel
from utils.data_preprocessor import preprocess_data
from utils.categorizer import categorize_transactions, refine_categories_with_user_feedback
from utils.summary_generator import generate_monthly_summary_text
from utils.chart_generator import request_and_generate_charts # New import

# --- Global In-Memory Storage Structures ---
monthly_earnings_summary = {}
monthly_spendings_summary = {}
MASTER_EARNINGS_COLUMNS = ['Date', 'Description', 'Amount', 'Category', 'Year', 'Month']
MASTER_SPENDINGS_COLUMNS = ['Date', 'Description', 'Amount', 'Category', 'Year', 'Month']
master_earnings_transactions = pd.DataFrame(columns=MASTER_EARNINGS_COLUMNS)
master_spendings_transactions = pd.DataFrame(columns=MASTER_SPENDINGS_COLUMNS)

# --- Plan for Persistence (Conceptual) ---
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

# ACCEPTED_FORMATS and FILE_UPLOAD_TIMEOUT remain as global constants
ACCEPTED_FORMATS = ['.pdf', '.csv', '.xls', '.xlsx']
FILE_UPLOAD_TIMEOUT = 60

# Ensure json is imported if not already, for the comments above
import json

def get_user_file(filepath: str = None):
    if filepath is None:
        # print(f"Waiting for file upload... (simulated {FILE_UPLOAD_TIMEOUT}s timeout)")
        # time.sleep(FILE_UPLOAD_TIMEOUT) # Actual sleep disabled for now
        print("No file detected. Please upload your statement.")
        return None
    _, file_extension = os.path.splitext(filepath)
    if file_extension.lower() not in ACCEPTED_FORMATS:
        print(f"Unsupported file format: {file_extension}. Please upload a PDF, CSV, or Excel file.")
        return None
    print(f"File received and validated: {filepath}")
    return filepath

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
            print(f"Update Storage: Missing required column '{col}'. Aborting storage update.")
            return

    earnings_df = categorized_df[categorized_df['Transaction_Type'] == 'Earning'].copy()
    spendings_df = categorized_df[categorized_df['Transaction_Type'] == 'Spending'].copy()

    if not earnings_df.empty:
        earnings_df.rename(columns={'Credit': 'Amount'}, inplace=True)
        if 'Amount' not in earnings_df.columns and 'Credit' in earnings_df.columns: # Should be redundant if rename worked
             earnings_df['Amount'] = earnings_df['Credit']

        # Select only the columns that exist in both earnings_df and MASTER_EARNINGS_COLUMNS
        cols_to_concat = [col for col in MASTER_EARNINGS_COLUMNS if col in earnings_df.columns]
        if 'Amount' in cols_to_concat: # Ensure 'Amount' is actually present before concat
            current_master_earnings = master_earnings_transactions.copy()
            master_earnings_transactions = pd.concat([current_master_earnings, earnings_df[cols_to_concat]], ignore_index=True)
            print(f"Updated master_earnings_transactions. New total rows: {len(master_earnings_transactions)}")
        else:
            print("Update Storage: 'Amount' column missing in earnings_df after rename/check. Cannot update master_earnings_transactions.")


    if not spendings_df.empty:
        spendings_df.rename(columns={'Debit': 'Amount'}, inplace=True)
        if 'Amount' not in spendings_df.columns and 'Debit' in spendings_df.columns: # Should be redundant
            spendings_df['Amount'] = spendings_df['Debit']

        cols_to_concat = [col for col in MASTER_SPENDINGS_COLUMNS if col in spendings_df.columns]
        if 'Amount' in cols_to_concat:
            current_master_spendings = master_spendings_transactions.copy()
            master_spendings_transactions = pd.concat([current_master_spendings, spendings_df[cols_to_concat]], ignore_index=True)
            print(f"Updated master_spendings_transactions. New total rows: {len(master_spendings_transactions)}")
        else:
            print("Update Storage: 'Amount' column missing in spendings_df after rename/check. Cannot update master_spendings_transactions.")


    if not earnings_df.empty and 'Amount' in earnings_df.columns:
        earnings_df['Year'] = earnings_df['Year'].fillna(0).astype(int)
        earnings_df['Month'] = earnings_df['Month'].fillna(0).astype(int)

        monthly_earning_groups = earnings_df.groupby(['Year', 'Month', 'Category'])['Amount'].sum().reset_index()
        for index, row in monthly_earning_groups.iterrows():
            year_month_str = f"{int(row['Year'])}-{int(row['Month']):02d}"
            category = row['Category']
            amount = row['Amount']

            if year_month_str not in monthly_earnings_summary:
                monthly_earnings_summary[year_month_str] = {}

            monthly_earnings_summary[year_month_str][category] = \
                monthly_earnings_summary[year_month_str].get(category, 0) + amount
        print("Updated monthly_earnings_summary.")

    if not spendings_df.empty and 'Amount' in spendings_df.columns:
        spendings_df['Year'] = spendings_df['Year'].fillna(0).astype(int)
        spendings_df['Month'] = spendings_df['Month'].fillna(0).astype(int)

        monthly_spending_groups = spendings_df.groupby(['Year', 'Month', 'Category'])['Amount'].sum().reset_index()
        for index, row in monthly_spending_groups.iterrows():
            year_month_str = f"{int(row['Year'])}-{int(row['Month']):02d}"
            category = row['Category']
            amount = row['Amount']

            if year_month_str not in monthly_spendings_summary:
                monthly_spendings_summary[year_month_str] = {}

            monthly_spendings_summary[year_month_str][category] = \
                monthly_spendings_summary[year_month_str].get(category, 0) + amount
        print("Updated monthly_spendings_summary.")


def process_bank_statement(file_path: str) -> pd.DataFrame | None:
    if file_path is None:
        print("No file path provided to process_bank_statement.")
        return None

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
        print(f"Unsupported file type: {file_extension} passed to process_bank_statement.")
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
        return None
    print(f"Successfully categorized transactions. DataFrame shape: {categorized_df.shape}")

    refine_categories_with_user_feedback(categorized_df)

    print("--- Updating In-Memory Storage ---")
    update_storage(categorized_df)

    return categorized_df


if __name__ == '__main__':
    # Adjusted dummy data for more varied monthly summary
    dummy_files_to_create = {
        "sample_statement.pdf": "Date,Description,Debit,Credit\n03/05/2023,PDF Bonus,,150\n03/10/2023,PDF Utility Bill,40,",
        "sample_statement.csv": (
            "Transaction Date,Description,Debit,Credit\n"
            "01/01/2023,Initial Salary,,3000\n"
            "01/15/2023,Groceries Store Purchase,55.20,\n"
            "01/20/2023,Online Shopping,120.00,\n"
            "02/01/2023,Monthly Salary,,3000\n"
            "02/05/2023,Freelance Income Project A,,450\n"
            "02/10/2023,Restaurant Dinner,75.80,\n"
            "02/15/2023,Fuel Top-up,60.00,"
        ),
        "sample_statement.xlsx": None,
        "sample_statement.txt": "This is an unsupported text file."
    }
    df_xlsx_data = { # XLSX data for Jan, Feb, and Mar
        'Date': ['01/10/2023', '01/25/2023', '02/15/2023', '02/20/2023', '03/12/2023', '03/22/2023'],
        'Description': [
            'Consulting Fee Jan (XLSX)', 'Office Rent Jan (XLSX)',
            'Artwork Sale Feb (XLSX)', 'Software Subscription Feb (XLSX)',
            'Workshop Earnings Mar (XLSX)', 'Travel Expense Mar (XLSX)'
        ],
        'Debit': [None, 800.00, None, 29.99, None, 150.00],
        'Credit': [1500.00, None, 600.00, None, 750.00, None]
    }
    df_xlsx = pd.DataFrame(df_xlsx_data)
    created_files = []

    for filename, content in dummy_files_to_create.items():
        full_path = os.path.join(os.getcwd(), filename) # Ensure files are created in current dir
        if filename.endswith(".xlsx"):
            df_xlsx.to_excel(full_path, index=False)
        elif filename.endswith(".pdf"):
             # Using simple text for PDF to test flow, actual parsing depends on camelot's ability
            try:
                from reportlab.pdfgen import canvas
                c = canvas.Canvas(full_path)
                c.drawString(72, 800, "Date,Description,Debit,Credit")
                c.drawString(72, 780, "01/01/2023,PDF Income,,100")
                c.drawString(72, 760, "01/02/2023,PDF Expense,20,")
                c.save()
                print(f"Created dummy PDF with reportlab: {full_path}")
            except ImportError:
                 with open(full_path, 'w') as f:
                    f.write(content if content else "") # Fallback to text-based
                 print(f"Created simple text-based dummy PDF: {full_path}")
        else:
            with open(full_path, 'w') as f:
                f.write(content if content else "")
        created_files.append(full_path)

    test_scenarios = [
        "sample_statement.csv",
        "sample_statement.xlsx",
        "sample_statement.pdf",
    ]

    for test_file_name in test_scenarios:
        test_file_path = os.path.join(os.getcwd(), test_file_name)
        print(f"\n**************** PROCESSING SCENARIO: {test_file_path} ****************")
        validated_file_path = get_user_file(test_file_path)
        if validated_file_path:
            processed_data = process_bank_statement(validated_file_path)
            if processed_data is not None and not processed_data.empty:
                print(f"--- Final Categorized Data for {validated_file_path} (Head) ---")
                display_cols = ['Date', 'Description', 'Debit', 'Credit', 'Transaction_Type', 'Category', 'Year', 'Month']
                display_cols = [col for col in display_cols if col in processed_data.columns]
                print(processed_data[display_cols].head().to_string()) # .to_string() for better console output
            else:
                print(f"Processing returned no data for {validated_file_path}.")
        print(f"**************** END SCENARIO: {test_file_path} ****************\n")

    print("\n--- Content of In-Memory Storage After All Scenarios ---")
    print("\nMaster Earnings Transactions:")
    print(master_earnings_transactions.to_string())
    print("\nMaster Spendings Transactions:")
    print(master_spendings_transactions.to_string())
    print("\nMonthly Earnings Summary:")
    import json
    print(json.dumps(monthly_earnings_summary, indent=4, sort_keys=True))
    print("\nMonthly Spendings Summary:")
    print(json.dumps(monthly_spendings_summary, indent=4, sort_keys=True))

    print("\n\n--- Generated Monthly Financial Text Summary ---")
    financial_summary_text = generate_monthly_summary_text(monthly_earnings_summary, monthly_spendings_summary)
    print(financial_summary_text)

    financial_summary_text = generate_monthly_summary_text(monthly_earnings_summary, monthly_spendings_summary)
    print(financial_summary_text)

    # Call the charting request function
    charts_output_directory = "generated_charts" # Define an output directory
    request_and_generate_charts(
        monthly_earnings_summary,
        monthly_spendings_summary,
        master_spendings_transactions,
        master_earnings_transactions,
        output_dir=charts_output_directory # Pass the directory
    )

    for f_path in created_files:
        if os.path.exists(f_path):
            os.remove(f_path)
    print("\nCleaned up dummy files.")
