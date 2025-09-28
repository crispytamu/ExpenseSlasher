# PROGRAM:         Expense Slasher Core Runnner
# PURPOSE:         This program is the entry point and orchestration layer for the Expense Slasher application.
# INPUT:           This program takes user input via the CLI for managing financial transactions.
# PROCESS:         Actions include adding, viewing, and deleting transactions, as well as calculating totals.
# OUTPUT:          Outputs are displayed in the CLI, showing transaction details and summaries.
# HONOR CODE:  On my honor, as an Aggie, I have neither given nor received unauthorized
#                               aid on this academic work.


#!/usr/bin/env python3

"""
ExspenseSlasherCore.py
- Runner and orchestration layer.
- Uses db_handler for persistence.
- Imports ExpenseSlasherCLI (UI) and overrides its data functions so all transactions go through DB.

Run:
   run python .\ExpenseSlasherCore.py
"""

from __future__ import annotations
import sys
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

# Bootstrap imports to ensure local modules are found
def _bootstrap_imports():
    """
    Ensure local modules (db_handler, ExpenseSlasherCLI) are discoverable by adding
    the current script's directory to the Python module search path.
    """
    here = Path(__file__).resolve().parent
    if str(here) not in sys.path:
        sys.path.insert(0, str(here))

_bootstrap_imports()

# Import persistence for Database handling
try:
    import db_handler as db
except ModuleNotFoundError as e:
    print("ERROR: Could not import db_handler. Ensure 'db_handler.py' is alongside this file.")
    raise e

# Import ExpenseSlasherCLI as UI
try:
    import ExpenseSlasherCLI as cli  #Must match ExpenseSlasherCLI.py and be in same folder
except ModuleNotFoundError as e:
    print("ERROR: Could not import ExpenseSlasherCLI. Ensure 'ExpenseSlasherCLI.py' is alongside this file.")
    raise e

# --------------------------- Helpers ----------------------------

def _today() -> str:
    """
    Get today's date in YYYY-MM-DD format.

    Returns:
        str: Current date as a string in YYYY-MM-DD format.
    """
    return datetime.today().strftime("%Y-%m-%d")

def _normalize_type(ttype: str) -> str:
    """
    Validate and normalize a transaction type string.

    Args:
        ttype (str): The transaction type provided by the user.

    Returns:
        str: Lowercased, validated transaction type ("income" or "expense").

    Raises:
        ValueError: If `ttype` is not "income" or "expense".
    """
    t = (ttype or "").strip().lower()
    if t not in ("income", "expense"):
        raise ValueError("Type must be 'income' or 'expense'")
    return t


def _extract_category(tags: Optional[str]) -> Optional[str]:
    """
    Extract the category value from a comma-separated tag string.

    Args:
        tags (Optional[str]): Comma-separated tags, e.g., "category:food,priority:high".

    Returns:
        Optional[str]: Extracted category if present, otherwise None.
    """
    if not tags:
        return None
    for t in tags.split(","):
        if t.startswith("category:"):
            return t.split(":", 1)[1]
    return None

def _make_tags(category: Optional[str]) -> list[str]:
    """
    Build a list of tags based on category.

    Args:
        category (Optional[str]): Category name.

    Returns:
        list[str]: A list with a single category tag, or an empty list if category is None.
    """
    return [f"category:{category}"] if category else []

# ---------------- Core DB-backed API ----------------

#Bridge between core and db_handler. Add a transaction to the DB
def add_transaction(date: str, description: str, category: str, amount, ttype: str):
    """
    Bridge to db_handler to add a transaction to the DB.

    Args:
        date (str): Transaction date in YYYY-MM-DD format. Defaults to today if empty.
        description (str): Short description of the transaction.
        category (str): Transaction category (e.g., "food", "rent").
        amount (float or str): Transaction amount.
        ttype (str): Transaction type ("income" or "expense").

    Raises:
        ValueError: If amount is not numeric, or ttype is invalid.
    """
    ttype = _normalize_type(ttype)
    try:
        amt = float(amount)
    except Exception:
        raise ValueError("Amount must be numeric.")

    d = date.strip() if date else _today()

    # convention: expenses positive, incomes negative
    if ttype == "income":
        amt = -abs(amt)
    else:
        amt = abs(amt)

    tags = _make_tags(category.strip() if category else None)

    ok = db.db_add_transaction(d, description, amt, tags)
    if not ok:
        print("DB insert failed.")

#Fetch all transactions from DB and convert to list of dicts for CLI
def load_transactions() -> List[Dict]:
    """
    Fetch all transactions from the DB and convert to a list of dictionaries.
    Returns:
        List[Dict]: A list of transaction dictionaries, each containing:
            - id (int): Transaction ID.
            - date (str): Transaction date.
            - description (str): Description text.
            - category (str): Category string or empty.
            - amount (float): Transaction amount (always positive).
            - type (str): "income" or "expense".
    """
    rows = db.db_fetch_all()  # list of tuples (rowid, date, desc, amnt, tags)
    out: List[Dict] = []
    for rid, date, desc, amnt, tags in rows:
        ttype = "expense" if amnt >= 0 else "income"
        category = _extract_category(tags)
        out.append({
            "id": rid,
            "date": date,
            "description": desc,
            "category": category or "",
            "amount": abs(amnt),
            "type": ttype
        })
    return out

#Functions to computer total income, expenses, net savings, net value from list of transactions
#Includes remote_transaction_by_index to delete a transaction by its index in the list
def total_income(transactions: List[Dict]) -> float:
    """
    Calculate the total income from a list of transactions.

    Args:
        transactions (List[Dict]): List of transaction dictionaries.

    Returns:
        float: Sum of all income transaction amounts.
    """
    return sum(float(t["amount"]) for t in transactions if t["type"] == "income")

def total_expenses(transactions: List[Dict]) -> float:
    """
    Calculate the total expenses from a list of transactions.

    Args:
        transactions (List[Dict]): List of transaction dictionaries.

    Returns:
        float: Sum of all expense transaction amounts.
    """
    return sum(float(t["amount"]) for t in transactions if t["type"] == "expense")

def net_savings(transactions: List[Dict]) -> float:
    """
    Calculate the net savings from a list of transactions.

    Net savings = income - expenses.

    Args:
        transactions (List[Dict]): List of transaction dictionaries.

    Returns:
        float: Net savings value.
    """
    return total_income(transactions) - total_expenses(transactions)

def net_value(transactions: List[Dict]) -> float:
    """
    Calculate the net financial value from a list of transactions.

    Alias for net_savings().

    Args:
        transactions (List[Dict]): List of transaction dictionaries.

    Returns:
        float: Net financial value.
    """
    return net_savings(transactions)

def remove_transaction_by_index(index: int):
    """
    Remove a transaction by its index in the transaction list.

    Args:
        index (int): Zero-based index of the transaction in the list.

    Returns:
        tuple:
            - (bool): True if removal was successful, False otherwise.
            - (dict or int): Removed transaction dict if successful,
              or the number of transactions if removal failed.
    """
    txns = load_transactions()
    if index < 0 or index >= len(txns):
        return False, len(txns)

    target = txns[index]
    tid = target.get("id")
    if tid is None:
        # return the number of transactions so CLI can show range
        return False, len(txns)

    if hasattr(db, "db_delete_transaction") and callable(db.db_delete_transaction):
        ok = db.db_delete_transaction(tid)
        if ok:
            return True, target
        else:
            # deletion failed, but return count so CLI doesn’t break
            return False, len(txns)
    else:
        # deletion not implemented, return count
        return False, len(txns)


# ---------------- Bind Core into CLI ----------------
#This overwrites CLI CSV based functions with CORE DB functions
cli.add_transaction = add_transaction
cli.load_transactions = load_transactions
cli.total_income = total_income
cli.total_expenses = total_expenses
cli.net_savings = net_savings
cli.net_value = net_value
cli.remove_transaction_by_index = remove_transaction_by_index

# ---------------- Runner ----------------

def main():
    """
    Main entry point for the Expense Slasher Core Runner.

    Launches the CLI after binding the core DB-backed functions to it.
    """
    print("=== Expense Slasher (Core Runner) ===")
    print("Using db_handler for persistence. Launching CLI...\n")
    cli.menu()

if __name__ == "__main__":
    main()
