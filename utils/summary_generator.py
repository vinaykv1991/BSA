import calendar # To get month names

def generate_monthly_summary_text(monthly_earnings: dict, monthly_spendings: dict) -> str:
    """
    Generates a formatted text summary of monthly earnings, spendings, and net savings.

    Args:
        monthly_earnings (dict): Dictionary in the format {'YYYY-MM': {'Category': Amount}}.
        monthly_spendings (dict): Dictionary in the format {'YYYY-MM': {'Category': Amount}}.

    Returns:
        str: A multi-line string containing the formatted financial summary.
    """
    if not monthly_earnings and not monthly_spendings:
        return "No monthly data available to generate a summary."

    all_periods = sorted(list(set(list(monthly_earnings.keys()) + list(monthly_spendings.keys()))))

    summary_lines = ["--- Monthly Financial Overview ---"]

    for period_str in all_periods:
        year, month_num = map(int, period_str.split('-'))
        month_name = calendar.month_name[month_num]

        summary_lines.append(f"\n    **{month_name} {year}**")

        # Earnings
        total_monthly_earnings = 0.0
        earnings_by_category = monthly_earnings.get(period_str, {})
        # Correctly sum total earnings for the period
        current_period_total_earnings = sum(earnings_by_category.values())
        summary_lines.append(f"        * **Total Earnings:** ${current_period_total_earnings:.2f}")

        if earnings_by_category:
            for category, amount in sorted(earnings_by_category.items()):
                summary_lines.append(f"            * {category}: ${amount:.2f}")
                total_monthly_earnings += amount # This is fine for re-accumulation if needed, but sum() is more direct
        else:
            summary_lines.append("            * No earnings this month.")

        # Spendings
        total_monthly_spendings = 0.0
        spendings_by_category = monthly_spendings.get(period_str, {})
        # Correctly sum total spendings for the period
        current_period_total_spendings = sum(spendings_by_category.values())
        summary_lines.append(f"        * **Total Spendings:** ${current_period_total_spendings:.2f}")

        if spendings_by_category:
            for category, amount in sorted(spendings_by_category.items()):
                summary_lines.append(f"            * {category}: ${amount:.2f}")
                total_monthly_spendings += amount # Similar to earnings, sum() is more direct
        else:
            summary_lines.append("            * No spendings this month.")

        # Net Savings/Loss - use the directly summed totals
        net_amount = current_period_total_earnings - current_period_total_spendings
        summary_lines.append(f"        * **Net Savings/Loss:** ${net_amount:.2f}")
        summary_lines.append("    ---")

    return "\n".join(summary_lines)

if __name__ == '__main__':
    # Test cases
    sample_earnings = {
        '2023-01': {'Salary': 5000.00, 'Freelance': 1000.00},
        '2023-02': {'Salary': 5000.00, 'Interest': 50.00}
    }
    sample_spendings = {
        '2023-01': {'Groceries': 300.50, 'Rent': 1500.00, 'Utilities': 150.00},
        '2023-02': {'Groceries': 250.00, 'Travel': 200.00},
        '2023-03': {'Unexpected Expense': 500.00} # Month with only spendings
    }

    print("--- Testing Monthly Summary Generator ---")
    summary_output = generate_monthly_summary_text(sample_earnings, sample_spendings)
    print(summary_output)

    print("\n--- Test with No Data ---")
    summary_output_no_data = generate_monthly_summary_text({}, {})
    print(summary_output_no_data)

    print("\n--- Test with Only Earnings ---")
    summary_output_only_earnings = generate_monthly_summary_text(sample_earnings, {})
    print(summary_output_only_earnings)

    print("\n--- Test with Only Spendings ---")
    summary_output_only_spendings = generate_monthly_summary_text({}, sample_spendings)
    print(summary_output_only_spendings)
