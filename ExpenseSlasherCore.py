#!/usr/bin/env python3
"""
Expense Slasher (SQLite-backed)

Requirements:
• Input transactions (date, description, category, amount, type: income or expense)
• Store in SQLite database
• Categorize transactions (food, rent, utilities, entertainment, etc.)
• Functions to calculate total income, total expenses, and net savings
"""

# OS for file checks, sqlite3 for DB, datetime for dates
import os
import sqlite3
from datetime import datetime

DB_FILE = "expenses.db"
FIELDS = ["date", "description", "category", "amount", "type"]

#DB Bootstrap

def _db_connect():
    return sqlite3.connect(DB_FILE)

def _db_init():
    """Create the transactions table if it doesn't exist."""
    with _db_connect() as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                description TEXT NOT NULL,
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                type TEXT NOT NULL CHECK (type IN ('income', 'expense'))
            );
        """)
        conn.commit()

def ensure_file():
    """Ensure the DB file and table exist."""
    _db_init()

#CSV-like API for SQLite

def add_transaction(date, description, category, amount, ttype):
    """Insert a row into SQLite (compatible signature)."""
    ensure_file()
    if not date:
        date = datetime.today().strftime("%Y-%m-%d")
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Date must be YYYY-MM-DD")

    try:
        amt = float(amount)
    except ValueError:
        raise ValueError("Amount must be numeric")

    ttype = (ttype or "").strip().lower()
    if ttype not in ("income", "expense"):
        raise ValueError("Type must be 'income' or 'expense'")

    with _db_connect() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO transactions (date, description, category, amount, type)
            VALUES (?, ?, ?, ?, ?)
        """, (date, description.strip(), category.strip(), amt, ttype))
        conn.commit()

def load_transactions():
    """Return a list of dictionaries from the SQLite DB."""
    ensure_file()
    with _db_connect() as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("""
            SELECT date, description, category, amount, type
            FROM transactions
            ORDER BY date, rowid
        """)
        rows = cur.fetchall()
        return [{k: row[k] for k in FIELDS} for row in rows]

#Calculations

def total_income(transactions):
    return sum(float(t["amount"]) for t in transactions if t["type"] == "income")

def total_expenses(transactions):
    return sum(float(t["amount"]) for t in transactions if t["type"] == "expense")

def net_savings(transactions):
    return total_income(transactions) - total_expenses(transactions)

#Same CLI as before, but updated to reflect DB backend

def menu():
    while True:
        print("\n=== Expense Slasher===")
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
            except ValueError as e:
                print(f"Error: {e}")
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
