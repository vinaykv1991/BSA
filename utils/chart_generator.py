import pandas as pd
import matplotlib
matplotlib.use('Agg') # Use a non-interactive backend, suitable for saving files
import matplotlib.pyplot as plt
import os

def generate_monthly_totals_bar_chart(monthly_earnings_summary: dict,
                                      monthly_spendings_summary: dict,
                                      output_dir: str = ".") -> bool:
    """
    Generates a bar chart of total monthly earnings vs. total monthly spendings
    and saves it to a file.

    Args:
        monthly_earnings_summary (dict): {'YYYY-MM': {'Category': Amount}}
        monthly_spendings_summary (dict): {'YYYY-MM': {'Category': Amount}}
        output_dir (str): Directory to save the chart.

    Returns:
        bool: True if chart generation was successful, False otherwise.
    """
    if not monthly_earnings_summary and not monthly_spendings_summary:
        print("ChartGen: No data available for monthly totals bar chart.")
        return False

    all_periods = sorted(list(set(list(monthly_earnings_summary.keys()) + list(monthly_spendings_summary.keys()))))
    if not all_periods:
        print("ChartGen: No periods found for charting.")
        return False

    earnings_totals = [sum(monthly_earnings_summary.get(p, {}).values()) for p in all_periods]
    spendings_totals = [sum(monthly_spendings_summary.get(p, {}).values()) for p in all_periods]

    x = range(len(all_periods))  # the label locations
    width = 0.35  # the width of the bars

    fig = None # Initialize fig to None for error handling
    try:
        fig, ax = plt.subplots(figsize=(12, 7)) # Increased figure size for better readability
        rects1 = ax.bar([i - width/2 for i in x], earnings_totals, width, label='Total Earnings', color='mediumseagreen') # Changed color
        rects2 = ax.bar([i + width/2 for i in x], spendings_totals, width, label='Total Spendings', color='lightcoral')  # Changed color

        ax.set_ylabel('Amount ($)')
        ax.set_title('Monthly Total Earnings vs. Spendings', fontsize=16)
        ax.set_xticks(x)
        ax.set_xticklabels(all_periods, rotation=45, ha="right")
        ax.legend(fontsize=10)
        ax.grid(axis='y', linestyle='--', alpha=0.7) # Add a light grid for y-axis

        ax.bar_label(rects1, padding=3, fmt='%.2f', fontsize=9)
        ax.bar_label(rects2, padding=3, fmt='%.2f', fontsize=9)

        fig.tight_layout()

        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        chart_filename = "monthly_totals_bar_chart.png"
        output_path = os.path.join(output_dir, chart_filename)

        plt.savefig(output_path)
        print(f"ChartGen: Successfully generated and saved '{output_path}'")
        return True
    except Exception as e:
        print(f"ChartGen: Error generating monthly totals bar chart: {e}")
        return False
    finally:
        if fig is not None: # Ensure fig was defined
             plt.close(fig) # Close the figure to free up memory


def request_and_generate_charts(monthly_earnings_summary: dict = None,
                                monthly_spendings_summary: dict = None,
                                master_spendings_transactions: pd.DataFrame = None,
                                master_earnings_transactions: pd.DataFrame = None,
                                output_dir: str = "charts") -> None:
    """
    Asks the user if they want charts and attempts to generate some.
    """
    print("\n\n--- Interactive Charting ---")
    print("Would you like to visualize this data with charts? For example, I can create a")
    print("monthly earnings/spendings bar chart, or a pie chart of spending categories")
    print("for a specific month.")

    user_response_placeholder = "yes"

    if user_response_placeholder.lower().strip() in ["yes", "y"]:
        print("\nAttempting chart generation:")

        # Attempt to generate Monthly Totals Bar Chart
        print("  - Generating Monthly Totals Bar Chart (Earnings vs. Spendings)...")
        success_bar = generate_monthly_totals_bar_chart(monthly_earnings_summary, monthly_spendings_summary, output_dir)
        if not success_bar:
            print("    Failed to generate Monthly Totals Bar Chart.")

        # Placeholder for Category Distribution Pie Chart
        print("  - Placeholder: Generating Category Distribution Pie Chart for Spendings (e.g., for first available month)...")
        if monthly_spendings_summary:
            sample_month = next(iter(monthly_spendings_summary)) if monthly_spendings_summary else None
            if sample_month:
                print(f"    (Data available for spendings pie chart for month: {sample_month})")
            else:
                print("    (No spending summary data available for pie chart)")
        else:
             print("    (No spending summary data available for pie chart)")

        # Placeholder for Category Trend Line Chart
        print("  - Placeholder: Generating Category Trend Line Chart (e.g., for 'Groceries')...")
        is_df_valid = False
        if master_spendings_transactions is not None and isinstance(master_spendings_transactions, pd.DataFrame) and not master_spendings_transactions.empty:
            is_df_valid = True

        if is_df_valid:
            if 'Category' in master_spendings_transactions.columns and \
               'Groceries' in master_spendings_transactions['Category'].unique():
                 print("    (Data potentially available for 'Groceries' trend line chart)")
            else:
                 print("    (Category 'Groceries' not found or 'Category' column missing for trend line chart)")
        else:
            print("    (No master transaction data available or DataFrame is not valid for trend line chart)")

        if success_bar : # Only print this if at least one chart was attempted (the bar chart here)
             print("\n(Actual chart files are saved if generation was successful. Other messages are placeholders.)")

    else:
        print("No charts requested.")
    # Conceptual error handling comment block as before...


if __name__ == '__main__':
    print("--- Testing Chart Generator ---")
    # Create dummy data
    dummy_earnings = {'2023-01': {'Salary': 5000, 'Bonus': 200}, '2023-02': {'Salary': 5100, 'Bonus': 500}, '2023-03': {'Salary': 5200}}
    dummy_spendings = {'2023-01': {'Groceries': 300, 'Rent': 1500, 'Utilities': 50},
                       '2023-02': {'Groceries': 320, 'Utilities': 100, 'Travel': 150},
                       '2023-03': {'Groceries': 280, 'Rent': 1500, 'Entertainment': 120}}

    output_chart_dir = "test_charts_output_standalone" # Different name for standalone test

    # Test the bar chart generation directly
    print("\nTesting generate_monthly_totals_bar_chart directly:")
    generate_monthly_totals_bar_chart(dummy_earnings, dummy_spendings, output_dir=output_chart_dir)
    print(f"Check the '{output_chart_dir}' directory for the saved chart (if successful).")

    # Test the main request function (which will call the bar chart function)
    print("\nTesting request_and_generate_charts:")

    MASTER_SPENDINGS_COLUMNS_TEST = ['Date', 'Description', 'Amount', 'Category', 'Year', 'Month']
    dummy_master_spendings = pd.DataFrame({
        'Date': pd.to_datetime(['2023-01-10', '2023-02-10', '2023-01-15']),
        'Description': ['Grocery Store', 'More Groceries', 'Gas'],
        'Amount': [100, 120, 40],
        'Category': ['Groceries', 'Groceries', 'Fuel'], # Added 'Fuel' to test other categories
        'Year': [2023, 2023, 2023],
        'Month': [1, 2, 1]
    }, columns=MASTER_SPENDINGS_COLUMNS_TEST)

    request_and_generate_charts(dummy_earnings, dummy_spendings, dummy_master_spendings, output_dir=output_chart_dir)
    print(f"If charts were requested, check the '{output_chart_dir}' directory.")

    print("\nTesting with no data for bar chart (within request_and_generate_charts):")
    request_and_generate_charts({}, {}, pd.DataFrame(columns=MASTER_SPENDINGS_COLUMNS_TEST), output_dir=output_chart_dir)

    # Clean up test directory if needed, or leave for inspection
    # import shutil
    # if os.path.exists(output_chart_dir):
    #     shutil.rmtree(output_chart_dir)
    #     print(f"Cleaned up test directory: {output_chart_dir}")
