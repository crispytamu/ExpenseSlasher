#!/usr/bin/env python3
"""
Expense Slasher - Tkinter GUI layer

This module exposes a `menu()` function so the Core can import it and
rebind its data functions (add/load/remove/total_*). The GUI simply calls
those injected functions—so the Core remains your entry point.

Expected to be overwritten by the Core after import:
- add_transaction(date, description, category, amount, ttype)
- load_transactions() -> list[dict]
- remove_transaction_by_index(index: int) -> tuple[bool, dict|int]
- total_income(transactions) -> float
- total_expenses(transactions) -> float
- net_savings(transactions) -> float
- net_value(transactions) -> float
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from typing import List, Dict

# ---- Placeholders (Core overwrites these after import) ----
def add_transaction(date: str, description: str, category: str, amount, ttype: str): ...
def load_transactions() -> List[Dict]: return []
def remove_transaction_by_index(index: int): return False, 0
def total_income(transactions: List[Dict]) -> float: return 0.0
def total_expenses(transactions: List[Dict]) -> float: return 0.0
def net_savings(transactions: List[Dict]) -> float: return 0.0
def net_value(transactions: List[Dict]) -> float: return 0.0
# -----------------------------------------------------------

def _today() -> str:
    return datetime.today().strftime("%Y-%m-%d")

def _validate_date(d: str) -> str:
    d = (d or "").strip()
    if not d:
        return _today()
    try:
        return datetime.strptime(d, "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        raise ValueError("Invalid date. Use YYYY-MM-DD.")

def _parse_amount(s: str) -> float:
    try:
        return float(s)
    except Exception:
        raise ValueError("Amount must be numeric.")

def _ym(dstr: str) -> str:
    # YYYY-MM from YYYY-MM-DD
    return datetime.strptime(dstr, "%Y-%m-%d").strftime("%Y-%m")

class ExpenseSlasherGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Expense Slasher")
        self.geometry("1000x640")
        self.minsize(880, 580)

        self._build_menubar()
        self._build_ui()
        self._refresh_table()
        self._update_totals()

        # Shortcuts
        self.bind("<Return>", lambda e: self._on_add())
        self.bind("<Delete>", lambda e: self._on_delete())

    # ---------- Menubar ----------
    def _build_menubar(self):
        menubar = tk.Menu(self)
        # File menu (future use)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Exit", command=self.destroy)
        menubar.add_cascade(label="File", menu=file_menu)

        # Reports menu
        reports_menu = tk.Menu(menubar, tearoff=0)
        reports_menu.add_command(label="Income vs. Expenses", command=self._open_report_income_vs_expenses)
        reports_menu.add_command(label="Expenses by Category", command=self._open_report_expenses_by_category)
        reports_menu.add_command(label="Monthly Breakdown", command=self._open_report_monthly_breakdown)
        menubar.add_cascade(label="Reports", menu=reports_menu)

        self.config(menu=menubar)

    # ---------- Main UI ----------
    def _build_ui(self):
        frm = ttk.LabelFrame(self, text="Add Transaction")
        frm.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        self.var_date = tk.StringVar(value=_today())
        self.var_desc = tk.StringVar()
        self.var_cat  = tk.StringVar()
        self.var_amt  = tk.StringVar()
        self.var_type = tk.StringVar(value="expense")

        # Labels
        ttk.Label(frm, text="Date (YYYY-MM-DD)").grid(row=0, column=0, padx=6, pady=(6, 0), sticky="w")
        ttk.Label(frm, text="Description").grid(row=0, column=1, padx=6, pady=(6, 0), sticky="w")
        ttk.Label(frm, text="Category").grid(row=0, column=2, padx=6, pady=(6, 0), sticky="w")
        ttk.Label(frm, text="Amount").grid(row=0, column=3, padx=6, pady=(6, 0), sticky="w")
        ttk.Label(frm, text="Type").grid(row=0, column=4, padx=6, pady=(6, 0), sticky="w")

        # Inputs
        ttk.Entry(frm, textvariable=self.var_date, width=15).grid(row=1, column=0, padx=6, pady=6)
        ttk.Entry(frm, textvariable=self.var_desc, width=34).grid(row=1, column=1, padx=6, pady=6)
        ttk.Entry(frm, textvariable=self.var_cat,  width=20).grid(row=1, column=2, padx=6, pady=6)
        ttk.Entry(frm, textvariable=self.var_amt,  width=12).grid(row=1, column=3, padx=6, pady=6)

        cmb = ttk.Combobox(frm, textvariable=self.var_type, values=["income", "expense"], state="readonly", width=12)
        cmb.grid(row=1, column=4, padx=6, pady=6)

        ttk.Button(frm, text="Add", command=self._on_add).grid(row=1, column=5, padx=8, pady=6)

        # Table
        table_frame = ttk.Frame(self)
        table_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        cols = ("idx","date","description","category","amount","type")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=16)
        self.tree.heading("idx", text="#")
        self.tree.column("idx", width=40, anchor="e")
        self.tree.heading("date", text="Date")
        self.tree.column("date", width=110)
        self.tree.heading("description", text="Description")
        self.tree.column("description", width=400)
        self.tree.heading("category", text="Category")
        self.tree.column("category", width=160)
        self.tree.heading("amount", text="Amount")
        self.tree.column("amount", width=120, anchor="e")
        self.tree.heading("type", text="Type")
        self.tree.column("type", width=100)

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=vsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        # Action buttons
        btns = ttk.Frame(self)
        btns.pack(side=tk.TOP, fill=tk.X, padx=10, pady=4)
        ttk.Button(btns, text="Remove Selected", command=self._on_delete).pack(side=tk.LEFT, padx=4)
        ttk.Button(btns, text="Refresh", command=lambda: (self._refresh_table(), self._update_totals())).pack(side=tk.LEFT, padx=4)

        # Totals
        totals = ttk.LabelFrame(self, text="Totals")
        totals.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(0, 10))
        self.lbl_income  = ttk.Label(totals, text="Income: $0.00")
        self.lbl_expense = ttk.Label(totals, text="Expenses: $0.00")
        self.lbl_net     = ttk.Label(totals, text="Net: $0.00")
        self.lbl_income.pack(side=tk.LEFT, padx=12, pady=6)
        self.lbl_expense.pack(side=tk.LEFT, padx=12, pady=6)
        self.lbl_net.pack(side=tk.LEFT, padx=12, pady=6)

        # Reports quick buttons
        rpt = ttk.LabelFrame(self, text="Reports")
        rpt.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(0, 10))
        ttk.Button(rpt, text="Income vs. Expenses", command=self._open_report_income_vs_expenses).pack(side=tk.LEFT, padx=6, pady=6)
        ttk.Button(rpt, text="Expenses by Category", command=self._open_report_expenses_by_category).pack(side=tk.LEFT, padx=6, pady=6)
        ttk.Button(rpt, text="Monthly Breakdown", command=self._open_report_monthly_breakdown).pack(side=tk.LEFT, padx=6, pady=6)

    # ---------- Actions ----------
    def _on_add(self):
        try:
            date = _validate_date(self.var_date.get())
            desc = (self.var_desc.get() or "").strip()
            if not desc:
                raise ValueError("Description cannot be empty.")
            cat  = (self.var_cat.get() or "").strip()
            amt  = _parse_amount(self.var_amt.get())
            ttype = (self.var_type.get() or "").strip().lower()

            add_transaction(date, desc, cat, amt, ttype)
            self._clear_inputs()
            self._refresh_table()
            self._update_totals()
        except ValueError as e:
            messagebox.showerror("Invalid input", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Could not add transaction:\n{e}")

    def _clear_inputs(self):
        self.var_date.set(_today())
        self.var_desc.set("")
        self.var_cat.set("")
        self.var_amt.set("")
        self.var_type.set("expense")

    def _on_delete(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Remove", "Select a row to remove.")
            return
        idx = int(self.tree.set(sel[0], "idx"))  # 0-based index
        ok, info = remove_transaction_by_index(idx)
        if ok:
            messagebox.showinfo("Removed", f"Removed: {info}")
        else:
            total = info
            messagebox.showwarning("Invalid index", f"Valid range is 0 to {total-1}.")
        self._refresh_table()
        self._update_totals()

    # ---------- Data/Display ----------
    def _refresh_table(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        txns = load_transactions()
        for i, t in enumerate(txns):
            self.tree.insert("", "end", values=(
                i,
                t["date"],
                t["description"],
                t["category"],
                f"{float(t['amount']):,.2f}",
                t["type"],
            ))

    def _update_totals(self):
        txns = load_transactions()
        inc = total_income(txns)
        exp = total_expenses(txns)
        net = inc - exp
        self.lbl_income.config(text=f"Income: ${inc:,.2f}")
        self.lbl_expense.config(text=f"Expenses: ${exp:,.2f}")
        self.lbl_net.config(text=f"Net: ${net:,.2f}")

    # ---------- Reports ----------
    def _open_report_income_vs_expenses(self):
        txns = load_transactions()
        inc = total_income(txns)
        exp = total_expenses(txns)
        net = inc - exp

        win = tk.Toplevel(self)
        win.title("Income vs. Expenses")
        win.geometry("420x200")
        win.resizable(False, False)

        frm = ttk.Frame(win, padding=12)
        frm.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frm, text="--- Total Income vs. Total Expenses ---").pack(anchor="w")
        ttk.Label(frm, text=f"Total Income  : ${inc:,.2f}").pack(anchor="w", pady=(6,0))
        ttk.Label(frm, text=f"Total Expense : ${exp:,.2f}").pack(anchor="w")
        ttk.Label(frm, text=f"Net           : ${net:,.2f}").pack(anchor="w")

        if inc > 0:
            ratio = (exp / inc) * 100
            ttk.Label(frm, text=f"Expense / Income: {ratio:,.2f}%").pack(anchor="w", pady=(6,0))
        elif exp > 0:
            ttk.Label(frm, text="Expense / Income: ∞ (no income yet)").pack(anchor="w", pady=(6,0))
        else:
            ttk.Label(frm, text="No transactions yet.").pack(anchor="w", pady=(6,0))

        ttk.Button(frm, text="Refresh", command=lambda: (win.destroy(), self._open_report_income_vs_expenses())).pack(anchor="e", pady=(12,0))

    def _open_report_expenses_by_category(self):
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

        rows = sorted(by_cat.items(), key=lambda kv: kv[1], reverse=True)

        win = tk.Toplevel(self)
        win.title("Expenses by Category")
        win.geometry("520x420")

        frm = ttk.Frame(win, padding=10)
        frm.pack(fill=tk.BOTH, expand=True)

        cols = ("category", "total")
        tree = ttk.Treeview(frm, columns=cols, show="headings", height=14)
        tree.heading("category", text="Category")
        tree.column("category", width=300)
        tree.heading("total", text="Total")
        tree.column("total", width=160, anchor="e")

        vsb = ttk.Scrollbar(frm, orient="vertical", command=tree.yview)
        tree.configure(yscroll=vsb.set)
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        frm.rowconfigure(0, weight=1)
        frm.columnconfigure(0, weight=1)

        for cat, total in rows:
            tree.insert("", "end", values=(cat, f"${total:,.2f}"))

        # Footer
        footer = ttk.Frame(win, padding=(10, 0, 10, 10))
        footer.pack(fill=tk.X)
        ttk.Button(footer, text="Refresh", command=lambda: (win.destroy(), self._open_report_expenses_by_category())).pack(side=tk.RIGHT)

        if not rows:
            messagebox.showinfo("Expenses by Category", "(no expenses found)")

    def _open_report_monthly_breakdown(self):
        from collections import defaultdict
        txns = load_transactions()
        buckets = defaultdict(lambda: {"income": 0.0, "expense": 0.0})

        for t in txns:
            try:
                ym = _ym(t["date"])
            except Exception:
                # Skip malformed dates silently in the report
                continue
            amt = float(t.get("amount", 0) or 0)
            if t.get("type") == "income":
                buckets[ym]["income"] += amt
            elif t.get("type") == "expense":
                buckets[ym]["expense"] += amt

        rows = sorted(buckets.items())  # (ym, dict)

        win = tk.Toplevel(self)
        win.title("Monthly Breakdown (Income | Expense | Net)")
        win.geometry("640x420")

        frm = ttk.Frame(win, padding=10)
        frm.pack(fill=tk.BOTH, expand=True)

        cols = ("month", "income", "expense", "net")
        tree = ttk.Treeview(frm, columns=cols, show="headings", height=14)
        for c, txt, w, anchor in [
            ("month",  "Month",   120, "w"),
            ("income", "Income",  150, "e"),
            ("expense","Expense", 150, "e"),
            ("net",    "Net",     150, "e"),
        ]:
            tree.heading(c, text=txt)
            tree.column(c, width=w, anchor=anchor)

        vsb = ttk.Scrollbar(frm, orient="vertical", command=tree.yview)
        tree.configure(yscroll=vsb.set)
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        frm.rowconfigure(0, weight=1)
        frm.columnconfigure(0, weight=1)

        for ym, v in rows:
            net = v["income"] - v["expense"]
            tree.insert("", "end", values=(ym, f"${v['income']:,.2f}", f"${v['expense']:,.2f}", f"${net:,.2f}"))

        footer = ttk.Frame(win, padding=(10, 0, 10, 10))
        footer.pack(fill=tk.X)
        ttk.Button(footer, text="Refresh", command=lambda: (win.destroy(), self._open_report_monthly_breakdown())).pack(side=tk.RIGHT)

        if not rows:
            messagebox.showinfo("Monthly Breakdown", "(no transactions)")

# ---- Public entrypoint expected by the Core ----
def menu():
    app = ExpenseSlasherGUI()
    app.mainloop()
