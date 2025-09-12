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

# For CLI


def menu():
    while True:
        print("\n=== Exspense Slasher Core ===")
        print("1) Add transaction")
        print("2) Show all transactions")
        print("3) Show summary")
        print("4) Show net value")  # Curtis
        print("5) Remove a transaction")  # Pablo Adding
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

        elif choice == "3":
            txns = load_transactions()
            print(f"Total Income : ${total_income(txns):.2f}")
            print(f"Total Expense: ${total_expenses(txns):.2f}")
            print(f"Net Savings  : ${net_savings(txns):.2f}")

        elif choice == "4":
            txns = load_transactions()
            print(f"Net Value :${net_value(txns):.2f}")

        elif choice == "5":  # Add Modifications
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

        elif choice == "0":
            print("Goodbye!")
            break
        else:
            print("Invalid choice.")


if __name__ == "__main__":
    menu()
