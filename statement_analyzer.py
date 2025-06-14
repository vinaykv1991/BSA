import os
import time # time is used by FILE_UPLOAD_TIMEOUT simulation if enabled
import pandas as pd
from utils.pdf_parser import parse_pdf
from utils.csv_parser import parse_csv
from utils.excel_parser import parse_excel
from utils.data_preprocessor import preprocess_data
from utils.categorizer import categorize_transactions # Added categorizer

ACCEPTED_FORMATS = ['.pdf', '.csv', '.xls', '.xlsx']
FILE_UPLOAD_TIMEOUT = 60  # seconds

def get_user_file(filepath: str = None):
    """
    Simulates awaiting user file upload, checks format, and handles timeout.
    Returns the filepath if valid, None otherwise.
    """
    if filepath is None:
        # This part simulates waiting for a file.
        # In a real scenario, this would be event-driven or a blocking call from a UI.
        print(f"Waiting for file upload... (simulated {FILE_UPLOAD_TIMEOUT}s timeout)")
        # time.sleep(FILE_UPLOAD_TIMEOUT) # Actual sleep disabled for now
        print("No file detected. Please upload your statement.")
        return None

    _, file_extension = os.path.splitext(filepath)

    if file_extension.lower() not in ACCEPTED_FORMATS:
        print(f"Unsupported file format: {file_extension}. Please upload a PDF, CSV, or Excel file.")
        return None

    print(f"File received and validated: {filepath}")
    return filepath

def process_bank_statement(file_path: str) -> pd.DataFrame | None:
    """
    Main processing function for a bank statement file.
    It determines file type, calls the appropriate parser, and then preprocesses the data.
    """
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
        # This case should ideally be caught by get_user_file, but as a safeguard:
        print(f"Unsupported file type: {file_extension} passed to process_bank_statement.")
        return None

    if raw_df is None or raw_df.empty:
        print(f"Parsing failed or returned no data for {file_path}.")
        return None

    print(f"Successfully parsed {file_path}. Raw DataFrame shape: {raw_df.shape}")
    print("--- Applying Universal Data Preprocessing ---")
    preprocessed_df = preprocess_data(raw_df)

    if preprocessed_df is None or preprocessed_df.empty:
        print(f"Data preprocessing failed or returned no data for {file_path}.")
        return None

    print(f"Successfully preprocessed data. DataFrame shape: {preprocessed_df.shape}")

        print("--- Applying Transaction Categorization ---")
        categorized_df = categorize_transactions(preprocessed_df)

        if categorized_df is None or categorized_df.empty:
            print(f"Transaction categorization failed or returned no data for {file_path}.")
            return None # Or return preprocessed_df if partial result is acceptable

        print(f"Successfully categorized transactions. DataFrame shape: {categorized_df.shape}")
        return categorized_df

# Modify the if __name__ == '__main__': block
if __name__ == '__main__':
    # Create dummy files for testing (ensure pandas is imported as pd for this block)
    dummy_files_to_create = {
        "sample_statement.pdf": "This is a dummy PDF content.", # Content for dummy PDF
        "sample_statement.csv": "Transaction Date,Description,Debit,Credit\n01/01/2023,Test CSV,10.00,\n",
        "sample_statement.xlsx": None, # Will be created using pandas
        "sample_statement.txt": "This is an unsupported text file."
    }

    # Create dummy XLSX using pandas
    df_xlsx = pd.DataFrame({'Date': ['01/01/2024'], 'Description': ['Test XLSX'], 'Debit': [10], 'Credit': [0]})

    created_files = []
    for filename, content in dummy_files_to_create.items():
        if filename.endswith(".xlsx"):
             df_xlsx.to_excel(filename, index=False)
        elif filename.endswith(".pdf"):
            # For PDF, use the existing dummy creation from pdf_parser or a simple text file
            # For simplicity here, just creating a text file named .pdf as camelot/pypdf2 will try to parse
            try:
                from reportlab.pdfgen import canvas
                c = canvas.Canvas(filename)
                c.drawString(100, 750, "Dummy PDF for main flow test.")
                c.drawString(100, 720, "01/01/2023 Test Transaction 10.00 ") # Camelot might pick this up
                c.save()
                print(f"Created dummy PDF with reportlab: {filename}")
            except ImportError:
                with open(filename, 'w') as f:
                    f.write(content if content else "Dummy PDF content")
                print(f"Created simple text-based dummy PDF: {filename}")

        else:
            with open(filename, 'w') as f:
                f.write(content if content else "")
        created_files.append(filename)
        print(f"Created dummy file: {filename}")

    test_scenarios = [
        "sample_statement.csv",
        "sample_statement.xlsx",
        "sample_statement.pdf", # PDF parsing success highly depends on content and camelot setup
        "sample_statement.txt", # Unsupported
        None # No file
    ]

    for test_file_path in test_scenarios:
        print(f"\n****************************************************")
        print(f"Executing Test Scenario: {'No file' if test_file_path is None else test_file_path}")
        print(f"****************************************************")

        # 1. Simulate getting the file from user
        validated_file_path = get_user_file(test_file_path)

        if validated_file_path:
            # 2. Process the validated file
                final_df = process_bank_statement(validated_file_path)
                if final_df is not None and not final_df.empty:
                    print(f"--- Final Processed Data for {validated_file_path} (Head) ---")
                    # Display relevant columns including Category
                    display_cols = ['Date', 'Description', 'Debit', 'Credit', 'Transaction_Type', 'Category', 'Year', 'Month']
                    # Filter for existing columns only to prevent KeyError if some optional columns are missing
                    existing_display_cols = [col for col in display_cols if col in final_df.columns]
                    print(final_df[existing_display_cols].head())
                    print(f"--- Final Processed Data Types ---")
                    print(final_df.dtypes)
            else:
                print(f"Processing returned no data for {validated_file_path}.")
        else:
            if test_file_path is not None: # Only print if it wasn't the 'None' test case already
                print(f"File '{test_file_path}' was not validated by get_user_file.")
        print(f"****************************************************\n")

    # Clean up dummy files
    for f_path in created_files:
        if os.path.exists(f_path):
            os.remove(f_path)
            print(f"Removed dummy file: {f_path}")
