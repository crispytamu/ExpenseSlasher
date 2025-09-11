#!/usr/bin/env python3
"""
ExspenseSlasherCore.py
- No CSV. All persistence is through db_handler.py.
- Provides a clean, CLI-friendly API: add/list/edit/remove + totals.
- Keeps category as a tag "category:<value>" in the DB.
- Amount sign convention in DB:
    * expense  => +amount
    * income   => -amount
- When showing to CLI, we return the magnitude (positive) and a 'type' field
  derived from the sign.

Intended CLI usage:
    from ExspenseSlasherCore import (
        add_transaction,
        list_transactions,
        list_transactions_print,
        edit_transaction_by_id,
        edit_transaction_by_index,
        remove_transaction_by_id,
        remove_transaction_by_index,
        total_income,
        total_expenses,
        net_savings,
        net_value,
        totals,
    )
"""

from typing import List, Dict, Tuple, Optional
from datetime import datetime
import db_handler as db


# ---------------------- Internal helpers ----------------------

def _signed_from(amount: float, ttype: Optional[str]) -> float:
    """
    Convert CLI magnitude + type into signed DB amount.
      - 'income'  -> negative
      - 'expense' -> positive (default)
    """
    t = (ttype or "").strip().lower()
    if t == "income":
        return -abs(float(amount))
    return abs(float(amount))

def _category_from_tags(tag_blob: Optional[str]) -> str:
    """Extract 'category:<name>' from GROUP_CONCAT tag string."""
    if not tag_blob:
        return ""
    for raw in tag_blob.split(","):
        tag = raw.strip()
        if tag.lower().startswith("category:"):
            return tag.split(":", 1)[1]
    return ""

def _replace_category_tag(transaction_id: int, current_tag_blob: Optional[str], new_category: Optional[str]) -> None:
    """Replace existing category:<...> tag with new one (or remove if empty)."""
    old = _category_from_tags(current_tag_blob)
    if old:
        db.db_delete_transaction_tags(transaction_id, [f"category:{old}"])
    if new_category:
        db.db_add_transaction_tags(transaction_id, [f"category:{new_category}"])

def _fetch_rows() -> List[Tuple[int, str, str, float, Optional[str]]]:
    """
    rows: (ROWID, date, desc, amnt, tags_blob)
    Note: db.db_fetch_all() returns GROUP_CONCAT(tags) aggregated by ROWID.
    """
    return db.db_fetch_all()

def _rows_to_dicts(rows: List[Tuple[int, str, str, float, Optional[str]]]) -> List[Dict]:
    """
    Convert DB rows into CLI-shaped dicts with friendly fields.
    - amount: magnitude (positive)
    - type: 'income' or 'expense' derived from sign
    """
    out: List[Dict] = []
    for rid, date, desc, amnt, tags_blob in rows:
        out.append({
            "id": rid,
            "date": date or "",
            "description": desc or "",
            "category": _category_from_tags(tags_blob),
            "amount": abs(float(amnt)),
            "type": _type_from_amount(float(amnt)),
            "_tags": tags_blob or "",
        })
    return out

def _index_to_id(index: int) -> Tuple[bool, Optional[int], int]:
    rows = _fetch_rows()
    total = len(rows)
    if index < 0 or index >= total:
        return (False, None, total)
    return (True, rows[index][0], total)  # (ok, transaction_id, total)


# ---------------------- Public functions (for the CLI) ----------------------

def add_transaction(date: Optional[str],
                    description: str,
                    category: Optional[str],
                    amount: float,
                    ttype: str) -> bool:
    """
    Add a transaction.
      - date: 'YYYY-MM-DD' (if None/empty -> today)
      - description: text
      - category: optional; stored as tag "category:<category>"
      - amount: positive magnitude entered by user
      - ttype: 'income' or 'expense'
    """
    if not date:
        date = datetime.today().strftime("%Y-%m-%d")
    signed = _signed_from(float(amount), ttype)
    tags = [f"category:{category}"] if category else []
    return db.db_add_transaction(date, description, signed, tags)


def list_transactions() -> List[Dict]:
    """
    Return all transactions as list of dicts:
    [
      {"id": int, "date": str, "description": str, "category": str,
       "amount": float, "type": "income|expense"}
    ]
    """
    return _rows_to_dicts(_fetch_rows())


def list_transactions_print(transactions: Optional[List[Dict]] = None) -> None:
    """
    Pretty-print the transaction list for CLI display.
    """
    txns = transactions or list_transactions()
    if not txns:
        print("(no transactions found)")
        return
    print("\n# | id   | date       | description                | category       | amount   | type")
    print("--+------+------------+----------------------------+----------------+----------+----------")
    for i, t in enumerate(txns):
        print(f"{i:2d}| {t['id']:<5d}| {t['date']:<10} | {t['description'][:26]:<26} | {t['category'][:14]:<14} | {t['amount']:<8.2f} | {t['type']}")


def remove_transaction_by_id(transaction_id: int) -> bool:
    """
    Remove a transaction by its database ID and prune orphaned tags.
    (Implements delete here; db_handler's delete is a TODO.)
    """
    try:
        # Delete join links
        db.CURSOR.execute("DELETE FROM transactions_tags WHERE transaction_id = ?", (transaction_id,))
        # Delete the transaction
        db.CURSOR.execute("DELETE FROM transactions WHERE ROWID = ?", (transaction_id,))
        # Prune tags with no links
        db.CURSOR.execute("""
            DELETE FROM tags
            WHERE ROWID IN (
                SELECT Tag.ROWID
                FROM tags AS Tag
                LEFT JOIN transactions_tags AS JT ON Tag.ROWID = JT.tag_id
                WHERE JT.tag_id IS NULL
            )
        """)
        db.DB.commit()
        return True
    except Exception as e:
        print("Error removing transaction:", e)
        db.DB.rollback()
        return False


def remove_transaction_by_index(index: int):
    """
    Remove a transaction by its list index.
    Returns (ok, removed_or_total)
      - ok=True  -> removed_or_total is the removed dict
      - ok=False -> removed_or_total is total count (for bounds message)
    """
    rows = _fetch_rows()
    total = len(rows)
    if index < 0 or index >= total:
        return (False, total)

    rid, date, desc, amnt, tags_blob = rows[index]
    removed_dict = _rows_to_dicts([rows[index]])[0]

    if remove_transaction_by_id(rid):
        return (True, removed_dict)
    return (False, total)


def edit_transaction_by_id(transaction_id: int,
                           *,
                           date: Optional[str] = None,
                           description: Optional[str] = None,
                           category: Optional[str] = None,
                           amount: Optional[float] = None,
                           ttype: Optional[str] = None):
    """
    Edit a transaction by DB id. Returns (ok, updated_dict | error_msg).
      - date/description/category: pass empty string "" to clear category
        (or leave None to keep existing)
      - amount: positive magnitude; final sign determined by ttype
        (if ttype None, preserves current direction)
      - ttype: 'income' | 'expense' | None (preserve)
    """
    # Grab current row to preserve sign/category if needed
    db.CURSOR.execute("""
        SELECT T.ROWID, T.date, T.desc, T.amnt, GROUP_CONCAT(Tag.name) as tags
        FROM transactions AS T
        LEFT JOIN transactions_tags AS JT ON T.ROWID = JT.transaction_id
        LEFT JOIN tags AS Tag ON JT.tag_id = Tag.ROWID
        WHERE T.ROWID = ?
        GROUP BY T.ROWID
    """, (transaction_id,))
    current = db.CURSOR.fetchone()
    if not current:
        return (False, "Transaction not found.")
    _, cur_date, cur_desc, cur_amnt, cur_tags = current

    # Determine new signed amount (if amount specified)
    signed_amount = None
    if amount is not None:
        if ttype is None:
            # preserve current direction
            direction = _type_from_amount(cur_amnt)
            signed_amount = _signed_from(float(amount), direction)
        else:
            signed_amount = _signed_from(float(amount), ttype)

    ok = db.db_edit_transaction(
        transactionID=transaction_id,
        date=(date if (date or "") != "" else None),
        desc=(description if (description or "") != "" else None),
        amnt=signed_amount
    )
    if not ok:
        return (False, "Edit failed.")

    # Category update (explicitly passed; empty string means remove)
    if category is not None:
        _replace_category_tag(transaction_id, cur_tags, category if category != "" else None)

    # Return refreshed record
    db.CURSOR.execute("""
        SELECT T.ROWID, T.date, T.desc, T.amnt, GROUP_CONCAT(Tag.name) as tags
        FROM transactions AS T
        LEFT JOIN transactions_tags AS JT ON T.ROWID = JT.transaction_id
        LEFT JOIN tags AS Tag ON JT.tag_id = Tag.ROWID
        WHERE T.ROWID = ?
        GROUP BY T.ROWID
    """, (transaction_id,))
    refreshed = db.CURSOR.fetchone()
    updated = _rows_to_dicts([refreshed])[0] if refreshed else None
    return (True, updated)


def edit_transaction_by_index(index: int,
                              *,
                              date: Optional[str] = None,
                              description: Optional[str] = None,
                              category: Optional[str] = None,
                              amount: Optional[float] = None,
                              ttype: Optional[str] = None):
    """
    Edit a transaction by its list index. Returns (ok, updated_dict | error/total).
    """
    rows = _fetch_rows()
    total = len(rows)
    if index < 0 or index >= total:
        return (False, total)
    rid = rows[index][0]
    return edit_transaction_by_id(
        rid,
        date=date,
        description=description,
        category=category,
        amount=amount,
        ttype=ttype,
    )


def total_income(transactions: Optional[List[Dict]] = None) -> float:
    """
    Sum of income as positive number.
    If not provided, reads from DB.
    """
    if transactions is None:
        rows = _fetch_rows()
        return sum((-float(amnt)) for _, _, _, amnt, _ in rows if float(amnt) < 0)
    return sum(float(t["amount"]) for t in transactions if t.get("type") == "income")


def total_expenses(transactions: Optional[List[Dict]] = None) -> float:
    """
    Sum of expenses as positive number.
    If not provided, reads from DB.
    """
    if transactions is None:
        rows = _fetch_rows()
        return sum((float(amnt)) for _, _, _, amnt, _ in rows if float(amnt) > 0)
    return sum(float(t["amount"]) for t in transactions if t.get("type") == "expense")


def net_savings(transactions: Optional[List[Dict]] = None) -> float:
    """
    Net = total_income - total_expenses (CLI semantics).
    """
    return total_income(transactions) - total_expenses(transactions)


def net_value(transactions: Optional[List[Dict]] = None) -> float:
    """Alias for menu parity."""
    return net_savings(transactions)


def totals() -> Dict[str, float]:
    """
    Compute all three at once directly from DB.
    """
    rows = _fetch_rows()
    inc = sum((-float(amnt)) for _, _, _, amnt, _ in rows if float(amnt) < 0)
    exp = sum((float(amnt)) for _, _, _, amnt, _ in rows if float(amnt) > 0)
    return {
        "total_income": inc,
        "total_expenses": exp,
        "net_savings": inc - exp,
    }

if __name__ == "__main__":
    import sys
    # Allow running the core as a module for quick inspection
    if len(sys.argv) > 1 and sys.argv[1] == "--list":
        from pprint import pprint
        pprint(list_transactions())
    else:
        print("ExspenseSlasherCore module loaded. Import it from the CLI.")
