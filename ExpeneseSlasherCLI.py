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

#Calculation Functions
def total_income(transactions):
    return sum(float(t["amount"]) for t in transactions if t["type"] == "income")

def total_expenses(transactions):
    return sum(float(t["amount"]) for t in transactions if t["type"] == "expense")

def net_savings(transactions):
    return total_income(transactions) - total_expenses(transactions)

###<-- Adding this helper
def net_value(transactions):
    return net_savings(transactions)

#For CLI
def menu():
    while True:
        print("\n=== Exspense Slasher Core ===")
        print("1) Add transaction")
        print("2) Show all transactions")
        print("3) Show summary")
        print("0) Exit")

        choice = input("Choose: ").strip()

        if choice == "1":
            date = input("Date (YYYY-MM-DD, blank=today): ").strip() or datetime.today().strftime("%Y-%m-%d")
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

        elif choice == "0":
            print("Goodbye!")
            break
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    menu()
