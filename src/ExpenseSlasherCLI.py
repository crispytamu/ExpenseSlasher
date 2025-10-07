# PROGRAM:         Expense Slasher CLI
# PURPOSE:         CLI personal finance tracker that records income and expenses, lists and removes
#                  transactions by index, and generates summary reports (income vs. expenses, expenses
#                  by category, and monthly breakdown). Computes totals and net savings and prints
#                  results in a readable table.
# INPUT:           User inputs transactions (date, description, category, amount, type) via CLI prompts.
# PROCESS:         Actions include adding, viewing, and deleting transactions, as well as calculating totals.
# OUTPUT:          Outputs are displayed in the CLI, showing transaction details, summaries, and reports.
# HONOR CODE:      On my honor, as an Aggie, I have neither given nor received unauthorized
#                  aid on this academic work.


#!/usr/bin/env python3
"""
Expense Slasher CLI Functionality

Requirements:
• Input transactions (date, description, category, amount, type: income or expense)
• Store in SQLite database
• Categorize transactions (food, rent, utilities, entertainment, etc.)
• Functions to calculate total income, total expenses, and net savings
"""
# Imports
import os
from datetime import datetime
from collections import defaultdict, Counter


# --- Normalization & validation helpers for reporting ---
def _normalize_transaction(t: dict) -> dict | None:
    """Return a cleaned transaction dict or None if unusable for reports."""
    # normalize/validate type
    typ = str(t.get("type", "")).strip().lower()
    if typ not in {"income", "expense"}:
        return None

    # normalize/validate amount
    try:
        amt = float(str(t.get("amount", "")).strip())
    except (TypeError, ValueError):
        return None

    # normalize/validate date (expect YYYY-MM-DD)
    d = str(t.get("date", "")).strip()
    try:
        d = datetime.strptime(d, "%Y-%m-%d").strftime("%Y-%m-%d")
    except Exception:
        return None

    # tidy fields
    desc = (t.get("description") or "").strip()
    cat = (t.get("category") or "").strip()
    if cat.lower() == "food":
        cat = "Food"

    return {"date": d, "description": desc, "category": cat, "amount": amt, "type": typ}


def _valid_transactions(transactions: list[dict]) -> tuple[list[dict], int]:
    """Return (cleaned_txns, skipped_count)."""
    cleaned, skipped = [], 0
    for raw in transactions:
        nt = _normalize_transaction(raw)
        if nt is None:
            skipped += 1
        else:
            cleaned.append(nt)
    return cleaned, skipped


# --- Calculation Functions ---
# Functions to compute totals for income, expenses, and net savings from a list of transactions.
def total_income(transactions):
    """Compute the total of all income transactions.

    Args:
        transactions: A list of transactions.

    Returns:
        The sum of amounts for transactions where `type == "income"`.
    """
    txns, _ = _valid_transactions(transactions)
    return sum(t["amount"] for t in txns if t["type"] == "income")


def total_expenses(transactions):
    """Compute the total of all expense transactions.

    Args:
        transactions: A list of transactions.

    Returns:
        The sum of amounts for transactions where `type == "expense"`.
    """
    txns, _ = _valid_transactions(transactions)
    return sum(t["amount"] for t in txns if t["type"] == "expense")


def net_savings(transactions):
    """Calculate net savings (income minus expenses).

    Args:
        transactions: A list of transactions.

    Returns:
        Net savings value (total income - total expenses).
    """
    txns, _ = _valid_transactions(transactions)
    inc = sum(t["amount"] for t in txns if t["type"] == "income")
    exp = sum(t["amount"] for t in txns if t["type"] == "expense")
    return inc - exp


def net_value(transactions):
    """Alias for :func:`net_savings` to support future extensions.

    Currently returns the same value as `net_savings`. Kept separate to allow
    evolving the concept of "net value" (e.g., include assets/liabilities).

    Args:
        transactions: A list of transactions.

    Returns:
        Net value computed from transactions.
    """
    return net_savings(transactions)


# --- Transaction Listing and Removal ---
# Functions to display transactions in a table and remove them by index.
def list_transactions_print(transactions):
    """Print a tabular view of transactions with index for removal.

    The index shown here is used by `remove_transaction_by_index`.

    Args:
        transactions: A list of transactions.

    Side Effects:
        Prints to stdout.
    """
    if not transactions:
        print("(no transactions found)")
        return
    print("\n# | date       | description                | category       | amount   | type")
    print("--+------------+----------------------------+----------------+----------+----------")
    for i, t in enumerate(transactions):
        print(
            f"{i:2d}| {t['date']:<10} | {t['description'][:26]:<26} | {t['category'][:14]:<14} | {t['amount']:<8} | {t['type']}")


def remove_transaction_by_index(index):
    """Remove a transaction by its index in the list.
    Args:
        index: The index of the transaction to remove.
    Returns:
        A tuple (success, info) where success is True if removal succeeded,
        and info is either the removed transaction (if success) or the total
        number of transactions (if failure).
    """
    txns = load_transactions()
    if index < 0 or index >= len(txns):
        return False, len(txns)
    removed = txns.pop(index)
    save_transactions(txns)
    return True, removed


# --- Reports Menu and Reporting Functions ---
# Functions to display a reports menu and generate summary reports.

def show_reports_menu():
    """Display the reports menu and handle user choices."""
    while True:
        print("\n=== Reports ===")
        print("1) Total income vs. total expenses")
        print("2) Total expenses by category")
        print("3) Monthly breakdown (income, expenses, net)")
        print("4) Back")
        choice = input("Choose: ").strip()

        if choice == "1":
            report_income_vs_expenses()
        elif choice == "2":
            report_expenses_by_category()
        elif choice == "3":
            report_monthly_breakdown()
        elif choice == "4":
            break
        else:
            print("Invalid choice. Try again.")


def report_income_vs_expenses():
    """Print totals of income, expenses, and net savings.

    Loads transactions fresh to reflect any changes before the report.

    Side Effects:
        Prints a formatted report to stdout.
    """
    txns_raw = load_transactions()
    txns, skipped = _valid_transactions(txns_raw)
    inc = sum(t["amount"] for t in txns if t["type"] == "income")
    exp = sum(t["amount"] for t in txns if t["type"] == "expense")
    net = inc - exp

    print("\n--- Total Income vs. Total Expenses ---")
    print(f"Total Income : ${inc:,.2f}")
    print(f"Total Expense: ${exp:,.2f}")
    print(f"Net          : ${net:,.2f}")
    if skipped:
        print(f"(Note: skipped {skipped} invalid transaction(s))")
    if inc > 0:
        print(f"Expense / Income: {(exp / inc) * 100:,.2f}%")
    elif exp > 0:
        print("Expense / Income: ∞ (no income yet)")
    else:
        print("No transactions yet.")


def report_expenses_by_category():
    """Print total expenses grouped by category, sorted descending.

    Rules:
        - Non-expense transactions are ignored.
        - Blank/missing categories are labeled 'Uncategorized'.

    Side Effects:
        Prints a formatted report to stdout.
    """
    txns_raw = load_transactions()
    txns, skipped = _valid_transactions(txns_raw)
    by_cat = defaultdict(float)
    for t in txns:
        if t["type"] == "expense":
            cat = t["category"] or "Uncategorized"
            by_cat[cat] += t["amount"]

    print("\n--- Total Expenses by Category ---")
    if not by_cat:
        print("(no expenses found)")
        if skipped:
            print(f"(Note: skipped {skipped} invalid transaction(s))")
        return

    rows = sorted(by_cat.items(), key=lambda kv: kv[1], reverse=True)
    cat_width = max(12, min(28, max(len(k) for k, _ in rows)))
    print(f"{'Category'.ljust(cat_width)}  Total")
    print(f"{'-'*cat_width}  {'-'*12}")
    for cat, total in rows:
        print(f"{cat.ljust(cat_width)}  ${total:,.2f}")
    if skipped:
        print(f"(Note: skipped {skipped} invalid transaction(s))")


def _ym(dstr):
    """Convert a full date string (YYYY-MM-DD) to a year-month key (YYYY-MM)."""
    return datetime.strptime(dstr, "%Y-%m-%d").strftime("%Y-%m")


def report_monthly_breakdown():
    """Print a monthly breakdown of income, expenses, and net.

    Side Effects:
        Prints a formatted report to stdout.
    """
    txns_raw = load_transactions()
    txns, skipped = _valid_transactions(txns_raw)
    buckets = defaultdict(lambda: {"income": 0.0, "expense": 0.0})
    for t in txns:
        ym = _ym(t["date"])
        buckets[ym][t["type"]] += t["amount"]

    rows = sorted(buckets.items())
    print("\n------ Monthly Breakdown (Income | Expense | Net) ------")
    if not rows:
        print("(no transactions)")
        if skipped:
            print(f"(Note: skipped {skipped} invalid transaction(s))")
        return

    print(" Month          Income           Expense          Net")
    print("---------------------------------------------------------")
    for ym, v in rows:
        net = v["income"] - v["expense"]
        print(
            f"{ym}  ${v['income']:>13,.2f}  ${v['expense']:>13,.2f}  ${net:>13,.2f}")
    if skipped:
        print(f"(Note: skipped {skipped} invalid transaction(s))")


# --- CLI Menu ---
# Main interactive menu for adding, viewing, and removing transactions, and accessing reports.

def menu():
    """Interactive CLI menu for Expense Slasher."""
    while True:
        print("\n=== Expense Slasher Core ===")
        print("1) Add transaction")
        print("2) Show all transactions")
        print("3) Remove a transaction")
        print("4) Reports Menu")
        print("0) Exit")

        choice = input("Choose: ").strip()

        if choice == "1":  # Add Transaction
            # Date must be YYYY-MM-DD or blank for today
            while True:
                date = input(
                    "Date (YYYY-MM-DD, blank=today): ").strip() or datetime.today().strftime("%Y-%m-%d")
                try:
                    parsed_date = datetime.strptime(date, "%Y-%m-%d")
                    date = parsed_date.strftime("%Y-%m-%d")  # normalize
                    break
                except ValueError:
                    print(
                        "Invalid date format or date. Please use YYYY-MM-DD and real calendar date.")

            # Description: cannot be blank
            while True:
                description = input("Description: ").strip()
                if description:
                    break
                print("Description cannot be blank.")

            # Category: cannot be blank; normalize 'food'/'Food' -> 'Food'
            while True:
                category = input(
                    "Category (e.g. food, rent, utilities): ").strip()
                if not category:
                    print("Category cannot be blank.")
                    continue
                if category.lower() == "food":
                    category = "Food"
                break

            # Amount: cannot be blank and must be numeric
            while True:
                raw_amount = input("Amount: ").strip()
                if raw_amount == "":
                    print("Amount cannot be blank.")
                    continue
                try:
                    amount = float(raw_amount)
                    break
                except ValueError:
                    print("Amount must be numeric.")

            # Type: selection (1 = Income, 2 = Expense)
            while True:
                t_choice = input("Type (1 = Income, 2 = Expense): ").strip()
                if t_choice == "1":
                    ttype = "income"
                    break
                elif t_choice == "2":
                    ttype = "expense"
                    break
                else:
                    print("Invalid selection. Enter 1 for Income or 2 for Expense.")

            try:
                add_transaction(date, description, category, amount, ttype)
                print("Transaction added.")
            except ValueError:
                print("Amount must be numeric.")

        elif choice == "2":  # Displays list of all transactions
            txns = load_transactions()
            for t in txns:
                print(t)

        elif choice == "3":  # Add Modifications
            txns = load_transactions()
            list_transactions_print(txns)
            if not txns:
                continue
            try:
                idx = int(input("Enter the index to remove: ").strip())
            except ValueError:
                print("Index must be a number.")
                continue
            ok, info = remove_transaction_by_index(idx)
            if ok:
                print(f"Removed: {info}")
            else:
                total = info
                print(f"Invalid index. Must be between 0 and {total-1}.")

        elif choice == "4":  # Reports Menu
            show_reports_menu()

        elif choice == "0":
            print("Goodbye!")
            break
        else:
            print("Invalid choice.")


# --- Program Entry Point ---
# Starts the CLI menu when the script is run directly.

if __name__ == "__main__":
    menu()
