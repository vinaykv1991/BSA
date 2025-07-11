# Bank Statement Analyzer

This application processes bank statement files (PDF, CSV, Excel) to extract transaction data, categorize earnings and spendings, and generate financial summaries and visualizations. It aims to provide insights into financial habits by automatically parsing statements and presenting the information in an understandable format.

## Features

- **Multiple File Format Support**: Parses bank statements from PDF, CSV, and Excel (.xls, .xlsx) files.
- **Robust PDF Parsing**: Utilizes `camelot-py` for table extraction from PDFs, with a text-based fallback using `PyPDF2`.
- **Data Standardization**: Automatically identifies and standardizes key columns (Date, Description, Debit, Credit).
- **Comprehensive Preprocessing**:
    - Converts dates to a consistent datetime format.
    - Cleans and converts monetary amounts to numeric types.
    - Assigns transaction types (Earning/Spending).
    - Extracts Year and Month for periodic analysis.
- **Keyword-Based Categorization**: Assigns categories to transactions based on keywords found in their descriptions (e.g., "Salary", "Groceries", "Utilities"). Includes fallback to "Miscellaneous Earnings/Spendings".
- **In-Memory Data Storage**: Maintains processed data in memory for the current session, including:
    - Master lists of all earning and spending transactions.
    - Monthly aggregated summaries of earnings and spendings by category.
- **Text-Based Financial Summary**: Generates a detailed monthly financial overview in text format, showing total earnings, total spendings, category breakdowns, and net savings/loss.
- **Visual Chart Generation**: Creates and saves a bar chart (`monthly_totals_bar_chart.png`) visualizing total monthly earnings versus total monthly spendings using `matplotlib`.
- **User Feedback Simulation (Placeholder)**: Includes a placeholder mechanism to indicate where user feedback could be incorporated to refine transaction categories.
- **Conceptual Persistence Plan**: Outlines a plan within the code comments for future implementation of data persistence (saving/loading analyzed data).

## Setup Instructions

### Prerequisites

- **Python**: Python 3.7 or higher is recommended.
- **System Dependencies for PDF Parsing**:
    - `camelot-py` (used for PDF table extraction) requires Ghostscript and Tkinter.
        - **On Debian/Ubuntu**:
          ```bash
          sudo apt-get update
          sudo apt-get install ghostscript python3-tk
          ```
        - **On macOS (using Homebrew)**:
          ```bash
          brew install ghostscript tcl-tk
          ```
        - **On Windows**:
            - Install Ghostscript from [the official website](https://www.ghostscript.com/download/gsdnld.html). Ensure the installation directory's `bin` folder (containing `gswin64c.exe` or similar) is added to your system's PATH.
            - Python for Windows usually comes with Tkinter. If not, you might need to reinstall Python ensuring Tk/Tcl is included.

### Python Dependencies

The application relies on several Python libraries. You can install them using pip:

```bash
pip install pandas camelot-py[cv] PyPDF2 openpyxl xlrd matplotlib reportlab
```

**Explanation of Libraries:**
*(Note: The script also uses the `argparse` module for command-line argument parsing, which is part of the Python standard library and does not require separate installation.)*
- `pandas`: For data manipulation and analysis, core to handling transaction DataFrames.
- `camelot-py[cv]`: For robust table extraction from PDF files. The `[cv]` extra installs OpenCV, which is needed by Camelot for some PDF processing strategies.
- `PyPDF2`: As a fallback PDF parser if Camelot fails, and for text-based extraction.
- `openpyxl`: Required by pandas to read and write Excel 2007+ files (.xlsx).
- `xlrd`: Required by pandas to read older Excel files (.xls).
- `matplotlib`: For generating charts.
- `reportlab`: Used in the test/example code to create dummy PDF files. While not strictly necessary for analyzing existing statements, it's included if you intend to run the full example script as is.

## How to Use

### 1. Prepare Your Bank Statements
Ensure your bank statements are available in one of the supported formats (PDF, CSV, XLS, XLSX).

### 2. Run the Analysis from the Command Line
Open your terminal or command prompt, navigate to the project directory, and run the `statement_analyzer.py` script, providing the paths to your bank statement files as arguments.

**Command Syntax:**
```bash
python statement_analyzer.py [options] <file1> [file2 ...]
```
- `<file1> [file2 ...]` are the paths to one or more bank statement files.
- `[options]` can include:
    - `--charts_dir <directory_name>`: Specifies the directory where generated charts will be saved. Defaults to `generated_charts`.

**Examples:**

- **Processing a single PDF file:**
  ```bash
  python statement_analyzer.py /path/to/your/bank_statement.pdf
  ```

- **Processing multiple files (a CSV and an XLSX):**
  ```bash
  python statement_analyzer.py "/path/to/your/jan_statement.csv" "/path/to/your/feb_statement.xlsx"
  ```
  *(Note: Use quotes around file paths if they contain spaces.)*

- **Processing files and specifying a custom charts directory:**
  ```bash
  python statement_analyzer.py --charts_dir my_financial_charts /path/to/statement1.pdf /path/to/statement2.csv
  ```

### 3. Review the Output
The application will produce the following outputs:

- **Console Output**:
    - Logs detailing the processing steps for each file (parsing, preprocessing, categorization).
    - An overall summary of how many files were attempted and how many were successfully processed.
    - If any files were successfully processed:
        - A preview (first 5 rows) of the master earnings and spendings transaction tables, aggregated from all processed files.
        - The monthly earnings and spendings summary dictionaries (in JSON format), aggregated from all processed files.
        - A formatted text-based "Monthly Financial Overview", aggregated from all processed files.
        - Messages related to placeholder features (like the user feedback loop for categorization and other chart types).
        - A confirmation message when the chart is saved.
    - If no files could be processed successfully, a message indicating this and that summaries/charts will be skipped.

- **Generated Chart**:
    - If data was processed, a bar chart image file named `monthly_totals_bar_chart.png` will be saved in the directory specified by `--charts_dir` (or in `generated_charts/` by default). This chart visualizes total monthly earnings versus total spendings based on all successfully processed statements.

### Important Notes:
- **File Paths**: If your file paths contain spaces, ensure you enclose them in quotes (e.g., `"my statement file.pdf"`).
- **PDF Parsing**: The success of PDF parsing heavily depends on the structure and quality of the PDF file. `camelot-py` is powerful but may struggle with scanned PDFs or non-standard layouts. The text-based `PyPDF2` fallback is very basic.
- **Categorization**: Transaction categorization is based on a predefined set of keywords. You can modify `DEFAULT_EARNINGS_KEYWORDS` and `DEFAULT_SPENDINGS_KEYWORDS` in `utils/categorizer.py` to better suit your specific transactions if needed.

## Project Structure

The project is organized as follows:

```
.
├── statement_analyzer.py   # Main executable script, orchestrates the analysis pipeline.
├── utils/                    # Directory for utility modules.
│   ├── __init__.py           # Makes 'utils' a Python package.
│   ├── pdf_parser.py         # Logic for parsing PDF files.
│   ├── csv_parser.py         # Logic for parsing CSV files.
│   ├── excel_parser.py       # Logic for parsing Excel files.
│   ├── data_preprocessor.py  # Universal data cleaning and preprocessing.
│   ├── categorizer.py        # Transaction categorization and feedback placeholder.
│   ├── summary_generator.py  # Text-based monthly summary generation.
│   └── chart_generator.py    # Chart generation (actual and placeholders).
├── generated_charts/         # Default output directory for generated charts (e.g., monthly_totals_bar_chart.png).
└── README.md                 # This documentation file.
```

- **`statement_analyzer.py`**: This is the entry point of the application. It handles the overall workflow, including file processing, calling utility functions for parsing, preprocessing, categorization, storage, summary generation, and chart requests.
- **`utils/`**: This directory contains specialized modules, each responsible for a specific part of the analysis pipeline. This modular design helps in keeping the code organized and maintainable.
    - **Parsers (`pdf_parser.py`, `csv_parser.py`, `excel_parser.py`)**: Handle the specifics of reading data from different file formats.
    - **`data_preprocessor.py`**: Standardizes the raw data extracted by the parsers.
    - **`categorizer.py`**: Implements the logic for assigning categories to transactions.
    - **`summary_generator.py`**: Creates the formatted text overview of financial data.
    - **`chart_generator.py`**: Responsible for creating visual charts from the data.
- **`generated_charts/`**: This directory is created by the application (if it doesn't exist) to store any charts generated, such as the `monthly_totals_bar_chart.png`.

## Future Enhancements

This application provides a solid foundation for bank statement analysis. Potential future enhancements could include:

- **Interactive User Feedback Loop**: Fully implement the user feedback mechanism for transaction categorization, allowing users to correct miscategorizations and dynamically update keyword sets.
- **Data Persistence**: Implement the conceptualized data persistence plan (e.g., using SQLite or Parquet/JSON files) to save and load analyzed data across sessions. This would allow for historical data accumulation and trend analysis over longer periods.
- **Advanced Charting**:
    - Implement more chart types (e.g., pie charts for category distribution, line charts for category trends over time).
    - Allow users to interactively select chart types and parameters (e.g., specific months or categories).
- **Command-Line Interface (CLI)**: Develop a proper CLI using libraries like `argparse` or `click` for easier file input, output directory specification, and control over application behavior without modifying the script directly.
- **Graphical User Interface (GUI)**: Create a GUI (e.g., using Tkinter, PyQt, or a web framework like Flask/Django) for a more user-friendly experience.
- **Improved PDF Parsing**: Enhance robustness for a wider variety of PDF layouts, possibly integrating OCR for scanned documents if `camelot-py` and `PyPDF2` are insufficient.
- **Smarter Categorization**: Explore more advanced categorization techniques, potentially using machine learning (ML) for suggestions or automatic categorization based on past user choices.
- **Budgeting Features**: Add functionality for setting budgets by category and tracking spending against them.
- **Export Options**: Allow users to export processed data, summaries, or reports to formats like CSV or Excel.
- **Configuration File**: Manage settings (like keyword lists, default paths) through an external configuration file.

## License

This project is licensed under the MIT License - see the `LICENSE.md` file for details (if one is created).
