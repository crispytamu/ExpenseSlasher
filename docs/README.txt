
####To run Expense Slasher. Navigate to root directory. 
####run python.exe .\src\ExpenseSlasherCore.py

Expense Slasher is a simple personal finance tracker. It records transactions (income and expenses)
stores them in SQLite, and offers summaries on totals and net savings.

There are 3 layers to Expense Slasher
    CLI -> ExpenseSlasherCLI.py. This is the terminal UI, it collects user input and prints output.
    CORE -> ExpenseSlasherCore.py. This holds all the business logic and a clean API for add/list/edit/remove
    and summaries
    Database -> db_handler.py: Low-level SQLite CRUD. The CORE calls the db handler so the CLI never touches
    the database directly. 

    Reasons for the split:
        This keeps UI concerns separate from the logic and data storage. 
        Makes it easy to replace the CLI with a GUI in later project phases



File by File Functionality

ExpenseSlasherCLI.py

Command‑line interface (UI only). Presents a menu and routes actions to Core functions.
Key Responsibilities
-Show menu options (Add / List / Summary / Net Value / Remove / Edit / Exit).
-Collect input (date, description, category, amount, type) and pass to Core.
-Display lists and summaries returned by Core using helpers like list_transactions_print.
-No direct DB access. All database persistance is done through the CORE


ExspenseSlasherCore.py

Entry Point. Enforces business rules and provides a stable API for the UI.
Validate & normalize input for transactions.

-Categorization via tags (ex. "category:food"). Extract category from a comma‑separated tags string with _extract_category(tags).
-Provide list/edit/remove APIs that operate by index (for CLI) while translating to actual DB ids under the hood.
-Compute totals: total_income, total_expenses, net_savings, net_value, and totals.
-All persistence is done through to db_handler


db_handler.py

Database adapter for SQLite. Thin layer that exposes CRUD functions the Core depends on

-Initialize the database (create transactions table if missing).
Provide functions such as:

    -insert_transaction(date, description, signed_amount, tags) → returns new id.
    -select_transactions(order_by=...) → returns rows ordered consistently (e.g., by date then id).
    -update_transaction(id, **fields) → returns count updated.
    -delete_transaction(id) → returns count deleted.