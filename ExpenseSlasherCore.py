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
    import ExpenseSlasherCLI as cli  # must match your CLI filename
except ModuleNotFoundError as e:
    print("ERROR: Could not import ExpenseSlasherCLI. Ensure 'ExpenseSlasherCLI.py' is alongside this file.")
    raise e

# --------------------------- Helpers ----------------------------

#Provides today's date in YYYY-MM-DD format if date is blank
def _today() -> str:
    return datetime.today().strftime("%Y-%m-%d")

#Prevent invalid types from being added to DB
def _normalize_type(ttype: str) -> str:
    t = (ttype or "").strip().lower()
    if t not in ("income", "expense"):
        raise ValueError("Type must be 'income' or 'expense'")
    return t

#Fucntion extract catergory from tag string
def _extract_category(tags: Optional[str]) -> Optional[str]:
    if not tags:
        return None
    for t in tags.split(","):
        if t.startswith("category:"):
            return t.split(":", 1)[1]
    return None

def _make_tags(category: Optional[str]) -> list[str]:
    return [f"category:{category}"] if category else []

# ---------------- Core DB-backed API ----------------

#Bridge to db_handler, add a transaction to the DB
def add_transaction(date: str, description: str, category: str, amount, ttype: str):
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

#Fethch all transactions from DB and convert to list of dicts for CLI
def load_transactions() -> List[Dict]:
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

#Calculate total income from list of transactions
def total_income(transactions: List[Dict]) -> float:
    return sum(float(t["amount"]) for t in transactions if t["type"] == "income")

#Calculate total expenses from list of transactions
def total_expenses(transactions: List[Dict]) -> float:
    return sum(float(t["amount"]) for t in transactions if t["type"] == "expense")

#Calculate net savings from list of transactions
def net_savings(transactions: List[Dict]) -> float:
    return total_income(transactions) - total_expenses(transactions)

#Calculate net value from list of transactions
def net_value(transactions: List[Dict]) -> float:
    return net_savings(transactions)

#Remove transaction by index from list of transactions
def remove_transaction_by_index(index: int):
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
    print("=== Expense Slasher (Core Runner) ===")
    print("Using db_handler for persistence. Launching CLI...\n")
    cli.menu()

if __name__ == "__main__":
    main()
