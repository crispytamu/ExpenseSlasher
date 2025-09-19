#!/usr/bin/env python3
"""
Expense Slasher CLI Functionality

Requirements:
• Input transactions (date, description, category, amount, type: income or expense)
• Store in SQLite database
• Categorize transactions (food, rent, utilities, entertainment, etc.)
• Functions to calculate total income, total expenses, and net savings
"""

import os
from datetime import datetime


# Calculation Functions
def total_income(transactions):
    return sum(float(t["amount"]) for t in transactions if t["type"] == "income")


def total_expenses(transactions):
    return sum(float(t["amount"]) for t in transactions if t["type"] == "expense")


def net_savings(transactions):
    return total_income(transactions) - total_expenses(transactions)

# <-- Adding this helper


def net_value(transactions):
    return net_savings(transactions)

# List with index for remove flow "Curtis and Pablo"


def list_transactions_print(transactions):
    if not transactions:
        print("(no transactions found)")
        return
    print("\n# | date       | description                | category       | amount   | type")
    print("--+------------+----------------------------+----------------+----------+----------")
    for i, t in enumerate(transactions):
        print(
            f"{i:2d}| {t['date']:<10} | {t['description'][:26]:<26} | {t['category'][:14]:<14} | {t['amount']:<8} | {t['type']}")

# NEW remove by index (shown on list) "Curtis and Pablo"


def remove_transaction_by_index(index):
    txns = load_transactions()
    if index < 0 or index >= len(txns):
        return False, len(txns)
    removed = txns.pop(index)
    save_transactions(txns)
    return True, removed


# ---------------- Reports Menu ---------------
def show_reports_menu():
    while True:
        print("\n=== Reports ===")
        print("1) Total income vs. total expenses")
        print("2) Total expenses by category")
        print("3) Back")
        choice = input("Choose: ").strip()

        if choice == "1":
            report_income_vs_expenses()
        elif choice == "2":
            report_expenses_by_category()
        elif choice == "3":
            break
        else:
            print("Invalid choice. Try again.")


def report_income_vs_expenses():
    # Load fresh each time in case data changed
    txns = load_transactions()
    inc = total_income(txns)
    exp = total_expenses(txns)
    net = inc - exp

    print("\n--- Total Income vs. Total Expenses ---")
    print(f"Total Income : ${inc:,.2f}")
    print(f"Total Expense: ${exp:,.2f}")
    print(f"Net          : ${net:,.2f}")
    if inc > 0:
        print(f"Expense / Income: {(exp / inc) * 100:,.2f}%")
    elif exp > 0:
        print("Expense / Income: ∞ (no income yet)")
    else:
        print("No transactions yet.")


def report_expenses_by_category():
    from collections import defaultdict

    txns = load_transactions()
    by_cat = defaultdict(float)

    for t in txns:
        if str(t.get("type", "")).lower() == "expense":
            cat = (t.get("category") or "").strip() or "Uncategorized"
            try:
                amt = float(t.get("amount", 0))
            except (TypeError, ValueError):
                amt = 0.0
            by_cat[cat] += amt

    print("\n--- Total Expenses by Category ---")
    if not by_cat:
        print("(no expenses found)")
        return

    # sorted largest first
    rows = sorted(by_cat.items(), key=lambda kv: kv[1], reverse=True)
    cat_width = max(12, min(28, max(len(k) for k, _ in rows)))
    print(f"{'Category'.ljust(cat_width)}  Total")
    print(f"{'-'*cat_width}  {'-'*12}")
    for cat, total in rows:
        print(f"{cat.ljust(cat_width)}  ${total:,.2f}")

# ---------------- CLI Menu ----------------


def menu():
    while True:
        print("\n=== Expense Slasher Core ===")
        print("1) Add transaction")
        print("2) Show all transactions")
        print("3) Remove a transaction")  # Pablo Adding
        print("4) Reports Menu")
        print("0) Exit")

        choice = input("Choose: ").strip()

        if choice == "1":
            date = input(
                "Date (YYYY-MM-DD, blank=today): ").strip() or datetime.today().strftime("%Y-%m-%d")
            description = input("Description: ").strip()
            category = input("Category (e.g. food, rent, utilities): ").strip()
            amount = input("Amount: ").strip()
            ttype = input("Type (income/expense): ").strip().lower()
            try:
                add_transaction(date, description, category, amount, ttype)
                print("Transaction added.")
            except ValueError:
                print("Amount must be numeric.")

        elif choice == "2":
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


if __name__ == "__main__":
    menu()
