import camelot
import PyPDF2
import pandas as pd
import re # For pattern matching with PyPDF2
import os # For os.path.exists and os.remove

# Ensure ghostscript is installed for camelot to work with PDFs.
# On Debian/Ubuntu: sudo apt-get install ghostscript
# On macOS: brew install ghostscript
# Ensure tk is installed for camelot.
# On Debian/Ubuntu: sudo apt-get install python3-tk
# On macOS: brew install python-tk

def parse_pdf(file_path: str) -> pd.DataFrame | None:
    """
    Parses a PDF file to extract tabular transaction data.
    Uses camelot-py first, then falls back to PyPDF2 if camelot fails.
    """
    print(f"Attempting to parse PDF with camelot: {file_path}")
    try:
        # Camelot can read multiple tables from multiple pages.
        # 'lattice' is often good for tables with clear grid lines.
        # 'stream' can be better for tables without lines.
        # We might need to try both or allow user to specify.
        tables = camelot.read_pdf(file_path, pages='all', flavor='lattice')

        if not tables:
            print("Camelot (lattice) found no tables. Trying with flavor='stream'.")
            tables = camelot.read_pdf(file_path, pages='all', flavor='stream')

        if tables and len(tables) > 0:
            all_dfs = []
            for i, table in enumerate(tables):
                print(f"Extracted table {i+1} with {table.df.shape[0]} rows and {table.df.shape[1]} columns.")
                if table.parsing_report['accuracy'] < 90: # Arbitrary threshold
                    print(f"Warning: Table {i+1} accuracy is low ({table.parsing_report['accuracy']:.2f}%).")
                all_dfs.append(table.df)

            if not all_dfs:
                print("Camelot extracted table objects, but no dataframes were generated.")
                # Fallback will be triggered by the except block if this path leads to an error later
                # or if we explicitly raise one. For now, let it try to concatenate.

            # Assuming all tables have similar column structures.
            # More sophisticated concatenation might be needed if columns vary wildly.
            combined_df = pd.concat(all_dfs, ignore_index=True)
            print(f"Successfully parsed PDF with camelot. Total rows: {combined_df.shape[0]}")
            # Basic validation: check if dataframe is empty or has too few columns
            if combined_df.empty or combined_df.shape[1] < 2: # Expect at least Date and Description
                print("Camelot parsing resulted in an empty or very narrow table. Falling back to PyPDF2.")
                raise Exception("Camelot output unsatisfactory")
            return combined_df
        else:
            print("Camelot found no tables.")
            # Explicitly trigger fallback if camelot finds no tables
            raise Exception("Camelot found no tables")

    except Exception as e:
        print(f"Camelot parsing failed: {e}. Falling back to PyPDF2.")
        try:
            # PyPDF2 fallback (simplified text extraction and pattern matching)
            # This is a placeholder for a more complex text extraction logic.
            # Robustly parsing arbitrary PDF text into structured data is very challenging.
            extracted_text = ""
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page_num in range(len(reader.pages)):
                    page = reader.pages[page_num]
                    extracted_text += page.extract_text() + "\n"

            if not extracted_text.strip():
                print("PyPDF2 extracted no text from the PDF.")
                return None

            print(f"PyPDF2 extracted text. Length: {len(extracted_text)}. Attempting pattern matching (basic).")

            # Placeholder for pattern matching logic.
            # This needs to be significantly more robust for real-world use.
            # Example: Look for lines with dates, some text, and currency amounts.
            # For now, we'll just return an empty DataFrame as a signal that PyPDF2 was tried.
            # In a real implementation, you would populate this DataFrame.
            # Regex examples (very basic, highly dependent on statement format):
            # date_pattern = r"\d{2}/\d{2}/\d{4}"
            # amount_pattern = r"\$\d+\.\d{2}"
            # transactions = []
            # for line in extracted_text.splitlines():
            #   if re.search(date_pattern, line) and re.search(amount_pattern, line):
            #       transactions.append(line) # Further split line into columns

            print("PyPDF2 text extraction successful, but structured parsing is a complex placeholder.")
            print("For now, PyPDF2 path will return None or an empty DataFrame.")
            # Returning None to indicate that PyPDF2 fallback is not fully implemented for data extraction
            return None
            # Example of returning an empty df if you want to signal PyPDF2 was attempted:
            # return pd.DataFrame()

        except Exception as pypdf_e:
            print(f"PyPDF2 parsing also failed: {pypdf_e}")
            return None

if __name__ == '__main__':
    # Create a dummy PDF for testing - camelot won't be able to parse it meaningfully
    # but it will allow testing the flow.
    # For real camelot testing, a PDF with actual tables is needed.
    dummy_pdf_path = "dummy_statement.pdf"
    try:
        from reportlab.pdfgen import canvas
        c = canvas.Canvas(dummy_pdf_path)
        c.drawString(100, 750, "This is a dummy PDF for testing parser flow.")
        c.drawString(100, 735, "Date Description Debit Credit")
        c.drawString(100, 720, "01/01/2023 Test Transaction 10.00 0.00")
        c.save()
        print(f"Created dummy PDF: {dummy_pdf_path}")
    except ImportError:
        print("ReportLab not found, cannot create dummy PDF. Skipping PDF parser test.")
        # If reportlab is not available, create a simple text file and name it .pdf
        # This won't be parsable by camelot or pypdf2 as a valid PDF structure,
        # but helps test the file handling part of the parser function.
        with open(dummy_pdf_path, 'w') as f:
            f.write("This is not a real PDF.")
        print(f"Created simple text file named {dummy_pdf_path} for basic flow testing.")


    if os.path.exists(dummy_pdf_path):
        print("\n--- Testing PDF Parser ---")
        df_result = parse_pdf(dummy_pdf_path)
        if df_result is not None:
            print("\nPDF Parsing Result (dummy):")
            print(df_result.head())
        else:
            print("\nPDF Parsing failed or returned no data (as expected for this dummy PDF).")

        os.remove(dummy_pdf_path)
        print(f"Removed dummy PDF: {dummy_pdf_path}")
    else:
        print("Skipping PDF parser test as dummy PDF could not be created.")
