#!/usr/bin/env python3
"""
Expense Slasher Core Functionality

Requirements:
• Input transactions (date, description, category, amount, type: income or expense)
• Store in CSV
• Categorize transactions (food, rent, utilities, entertainment, etc.)
• Functions to calculate total income, total expenses, and net savings
"""

import csv
import os
from datetime import datetime

CSV_FILE = "transactions.csv"
FIELDS = ["date", "description", "category", "amount", "type"]


def ensure_file():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()


def add_transaction(date, description, category, amount, ttype):
    ensure_file()
    with open(CSV_FILE, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writerow({
            "date": date,
            "description": description,
            "category": category,
            "amount": float(amount),
            "type": ttype.lower()
        })


def load_transactions():
    ensure_file()
    with open(CSV_FILE, newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)

# This is used after removing --new


def save_transactions(transactions):
    ensure_file()
    with open(CSV_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for t in transactions:
            writer.writerow({
                "date": t["date"],
                "description": t["description"],
                "category": t["category"],
                "amount": t["amount"],
                "type": t["type"]
            })

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

# NEW: Edit transaction by index


def edit_transaction_by_index(index, date=None, description=None, category=None, amount=None, ttype=None):
    txns = load_transactions()
    if index < 0 or index >= len(txns):
        return False, len(txns)

    tx = txns[index]

    if date is not None and date != "":
        tx["date"] = date

    if description is not None and description != "":
        tx["description"] = description

    if category is not None and category != "":
        tx["category"] = category

    if amount is not None and amount != "":
        try:
            tx["amount"] = float(amount)
        except ValueError:
            return False, "Amount must be numeric."

    if ttype is not None and ttype != "":
        tx["type"] = ttype.lower()

    save_transactions(txns)
    return True, tx

# For CLI


def menu():
    while True:
        print("\n=== Exspense Slasher Core ===")
        print("1) Add transaction")
        print("2) Show all transactions")
        print("3) Show summary")
        print("4) Show net value")  # Curtis
        print("5) Remove a transaction")  # Pablo Adding
        print("6) Edit a transaction")
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

        elif choice == "6":  # NEW: Edit flow
            txns = load_transactions()
            list_transactions_print(txns)
            if not txns:
                continue
            try:
                idx = int(input("Enter the index to edit: ").strip())
            except ValueError:
                print("Index must be a number.")
                continue

            if idx < 0 or idx >= len(txns):
                print(f"Invalid index. Must be between 0 and {len(txns)-1}.")
                continue

            current = txns[idx]

            # Prompt new values (blank = keep existing)
            new_date = input(
                f"New date (YYYY-MM-DD) [{current['date']}]: ").strip()
            new_desc = input(
                f"New description [{current['description']}]: ").strip()
            new_cat = input(f"New category [{current['category']}]: ").strip()

            # Amount with validation loop
            while True:
                new_amt = input(f"New amount [{current['amount']}]: ").strip()
                if new_amt == "":
                    break
                try:
                    float(new_amt)
                    break
                except ValueError:
                    print("Amount must be numeric.")

            new_type = input(
                f"New type (income/expense) [{current['type']}]: ").strip()

            ok, info = edit_transaction_by_index(
                idx,
                date=new_date or None,
                description=new_desc or None,
                category=new_cat or None,
                amount=new_amt or None,
                ttype=new_type or None
            )
            if ok:
                print(f"Updated: {info}")
            else:
                if isinstance(info, int):
                    print(f"Invalid index. Must be between 0 and {info-1}.")
                else:
                    print(info)  # error string (e.g., amount not numeric)

        elif choice == "0":
            print("Goodbye!")
            break
        else:
            print("Invalid choice.")


if __name__ == "__main__":
    menu()
