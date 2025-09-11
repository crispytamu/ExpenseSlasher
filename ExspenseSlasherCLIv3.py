#!/usr/bin/env python3
# HONOR CODE: On my honor, as an Aggie, I have neither given nor received unauthorized
# aid on this academic work.

"""
ExpeneseSlasherCLI.py
CLI only — persistence handled by ExspenseSlasherCore (SQLite via db_handler).

Menu:
1) Add transaction
2) Show all transactions
3) Show summary
4) Show net value
5) Remove a transaction
6) Edit a transaction
0) Exit
"""

from datetime import datetime

#Import the runner functions from ExspenseSlasherCore
from ExspenseSlasherCore import (
    add_transaction,
    list_transactions,
    list_transactions_print,
    remove_transaction_by_index,
    edit_transaction_by_index,
    total_income,
    total_expenses,
    net_savings,
    net_value,
    totals,
)

def menu():
    while True:
        print("\n=== Expense Slasher (CLI) ===")
        print("1) Add transaction")
        print("2) Show all transactions")
        print("3) Show summary")
        print("4) Show net value")
        print("5) Remove a transaction")
        print("6) Edit a transaction")
        print("0) Exit")

        choice = input("Choose: ").strip()

        if choice == "1":
            date = input("Date (YYYY-MM-DD, blank=today): ").strip() or datetime.today().strftime("%Y-%m-%d")
            description = input("Description: ").strip()
            category = input("Category (e.g. food, rent, utilities): ").strip()
            amount = input("Amount (positive number): ").strip()
            ttype = input("Type (income/expense): ").strip().lower()

            try:
                ok = add_transaction(date, description, category, float(amount), ttype)
                print("Transaction added." if ok else "Failed to add transaction.")
            except ValueError:
                print("Amount must be numeric.")

        elif choice == "2":
            # Pretty table print (fetches from DB under the hood)
            list_transactions_print()

        elif choice == "3":
            # Show totals using DB-backed computations
            t = totals()
            print(f"Total Income : ${t['total_income']:.2f}")
            print(f"Total Expense: ${t['total_expenses']:.2f}")
            print(f"Net Savings  : ${t['net_savings']:.2f}")

        elif choice == "4":
            # For parity with old CLI
            print(f"Net Value: ${net_value():.2f}")

        elif choice == "5":
            # Show with indices, then remove by chosen index
            txns = list_transactions()
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

        elif choice == "6":
            # Edit via index (blank to keep current; empty category "" removes it)
            txns = list_transactions()
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
            new_date = input(f"New date (YYYY-MM-DD) [{current['date']}]: ").strip()
            new_desc = input(f"New description [{current['description']}]: ").strip()
            new_cat  = input(f"New category [{current['category']}]: ").strip()

            # Amount with validation loop
            while True:
                new_amt = input(f"New amount [{current['amount']}]: ").strip()
                if new_amt == "":
                    new_amt_val = None
                    break
                try:
                    new_amt_val = float(new_amt)
                    break
                except ValueError:
                    print("Amount must be numeric.")

            new_type = input(f"New type (income/expense) [{current['type']}]: ").strip()

            ok, info = edit_transaction_by_index(
                idx,
                date=(new_date or None),
                description=(new_desc or None),
                category=(new_cat if new_cat != "" else ""),   # empty string removes category
                amount=new_amt_val,
                ttype=(new_type or None)
            )

            if ok:
                print(f"Updated: {info}")
            else:
                if isinstance(info, int):
                    print(f"Invalid index. Must be between 0 and {info-1}.")
                else:
                    print(info)  # error string

        elif choice == "0":
            print("Goodbye!")
            break
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    menu()
