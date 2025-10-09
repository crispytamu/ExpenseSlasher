# PROGRAM: Expense Slasher GUI Runner
# PURPOSE: This module launches the Tkinter-based Expense Slasher application and renders reports with Matplotlib.
# INPUT: User interactions via the GUI (form fields, table selection, menus, and keyboard shortcuts).
# PROCESS: Add, view, and delete transactions; compute totals; generate Income vs Expenses, Category, and Monthly reports with charts.
# OUTPUT: On-screen tables, labels, and embedded bar charts within Tkinter windows.
# HONOR CODE: On my honor, as an Aggie, I have neither given nor received unauthorized aid on this academic work.

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
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


# ---- Placeholders (Core overwrites these after import) ----

def add_transaction(date: str, description: str, category: str, amount, ttype: str):
    """Persist a single transaction.

    Parameters
    ----------
    date : str
        ISO date string in ``YYYY-MM-DD`` format.
    description : str
        Short label for the transaction.
    category : str
        Classification (e.g., "Groceries", "Rent", "Salary").
    amount : Any
        Numeric value; the Core should coerce/validate to ``float``.
    ttype : str
        Either ``"income"`` or ``"expense"``.

    Notes
    -----
    This function is expected to be **overwritten by the Core** after import.
    The default placeholder does nothing.
    """
    ...


def load_transactions() -> List[Dict]:
    """Return a list of transaction dictionaries.

    Each transaction dict should contain: ``date``, ``description``,
    ``category``, ``amount``, and ``type`` ("income"|"expense").

    Returns
    -------
    List[Dict]
        A list of transactions. Placeholder returns an empty list.
    """
    return []


def remove_transaction_by_index(index: int):
    """Remove a transaction by its 0‑based index.

    Parameters
    ----------
    index : int
        Index in the current transaction list/order.

    Returns
    -------
    Tuple[bool, Any]
        ``(True, info)`` on success where ``info`` may describe the item removed;
        ``(False, total)`` on failure where ``total`` is the valid item count.

    Notes
    -----
    This is a Core‑overridden function; the placeholder returns ``(False, 0)``.
    """
    return False, 0


def total_income(transactions: List[Dict]) -> float:
    """Compute the sum of amounts for transactions with type ``income``.

    Placeholder returns ``0.0`` when Core is not connected.
    """
    return 0.0


def total_expenses(transactions: List[Dict]) -> float:
    """Compute the sum of amounts for transactions with type ``expense``.

    Placeholder returns ``0.0`` when Core is not connected.
    """
    return 0.0


def net_savings(transactions: List[Dict]) -> float:
    """Compute savings metric if provided by Core (not used directly here).

    Placeholder returns ``0.0``.
    """
    return 0.0


def net_value(transactions: List[Dict]) -> float:
    """Compute net value metric if provided by Core (not used directly here).

    Placeholder returns ``0.0``.
    """
    return 0.0
# -----------------------------------------------------------


def _today() -> str:
    """Return today's date as ``YYYY-MM-DD`` string."""
    return datetime.today().strftime("%Y-%m-%d")


def _validate_date(d: str) -> str:
    """Normalize and validate a date string.

    If ``d`` is empty or whitespace, today's date is returned. Otherwise the
    value must parse as ``YYYY-MM-DD`` or a :class:`ValueError` is raised.
    """
    d = (d or "").strip()
    if not d:
        return _today()
    try:
        return datetime.strptime(d, "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        raise ValueError("Invalid date. Use YYYY-MM-DD.")


def _parse_amount(s: str) -> float:
    """Convert a string to ``float`` or raise a user‑friendly error.

    Parameters
    ----------
    s : str
        The input amount text (commas/letters are invalid).
    """
    try:
        return float(s)
    except Exception:
        raise ValueError("Amount must be numeric.")


def _ym(dstr: str) -> str:
    """Return ``YYYY-MM`` month key from a ``YYYY-MM-DD`` date string."""
    return datetime.strptime(dstr, "%Y-%m-%d").strftime("%Y-%m")


class ExpenseSlasherGUI(tk.Tk):
    """Main application window for Expense Slasher.

    Responsibilities
    ----------------
    - Build the Tkinter UI (form, table, totals, and report buttons)
    - Dispatch add/remove actions
    - Open report windows that render tables and Matplotlib bar charts
    """

    def __init__(self):
        """Initialize and lay out the main window, then load initial data."""
        super().__init__()
        self.title("Expense Slasher")
        self.geometry("1000x740")
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
        """Create the top menubar with File and Reports menus."""
        menubar = tk.Menu(self)
        # File menu (future use)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Exit", command=self.destroy)
        menubar.add_cascade(label="File", menu=file_menu)

        # Reports menu
        reports_menu = tk.Menu(menubar, tearoff=0)
        reports_menu.add_command(
            label="Income vs. Expenses", command=self._open_report_income_vs_expenses)
        reports_menu.add_command(
            label="Expenses by Category", command=self._open_report_expenses_by_category)
        reports_menu.add_command(
            label="Monthly Breakdown", command=self._open_report_monthly_breakdown)
        menubar.add_cascade(label="Reports", menu=reports_menu)

        self.config(menu=menubar)

    # ---------- Main UI ----------
    def _build_ui(self):
        """Build the form inputs, table, action buttons, totals, and report shortcuts."""
        frm = ttk.LabelFrame(self, text="Add Transaction")
        frm.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        self.var_date = tk.StringVar(value=_today())
        self.var_desc = tk.StringVar()
        self.var_cat = tk.StringVar()
        self.var_amt = tk.StringVar()
        self.var_type = tk.StringVar(value="expense")

        # Labels
        ttk.Label(frm, text="Date (YYYY-MM-DD)").grid(row=0,
                                                      column=0, padx=6, pady=(6, 0), sticky="w")
        ttk.Label(frm, text="Description").grid(
            row=0, column=1, padx=6, pady=(6, 0), sticky="w")
        ttk.Label(frm, text="Category").grid(
            row=0, column=2, padx=6, pady=(6, 0), sticky="w")
        ttk.Label(frm, text="Amount").grid(
            row=0, column=3, padx=6, pady=(6, 0), sticky="w")
        ttk.Label(frm, text="Type").grid(
            row=0, column=4, padx=6, pady=(6, 0), sticky="w")

        # Inputs
        ttk.Entry(frm, textvariable=self.var_date, width=15).grid(
            row=1, column=0, padx=6, pady=6)
        ttk.Entry(frm, textvariable=self.var_desc, width=34).grid(
            row=1, column=1, padx=6, pady=6)
        ttk.Entry(frm, textvariable=self.var_cat,  width=20).grid(
            row=1, column=2, padx=6, pady=6)
        ttk.Entry(frm, textvariable=self.var_amt,  width=12).grid(
            row=1, column=3, padx=6, pady=6)

        cmb = ttk.Combobox(frm, textvariable=self.var_type, values=[
                           "income", "expense"], state="readonly", width=12)
        cmb.grid(row=1, column=4, padx=6, pady=6)

        ttk.Button(frm, text="Add", command=self._on_add).grid(
            row=1, column=5, padx=8, pady=6)

        # Table
        table_frame = ttk.Frame(self)
        table_frame.pack(side=tk.TOP, fill=tk.BOTH,
                         expand=True, padx=10, pady=(0, 10))

        cols = ("idx", "date", "description", "category", "amount", "type")
        self.tree = ttk.Treeview(
            table_frame, columns=cols, show="headings", height=16)
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

        vsb = ttk.Scrollbar(table_frame, orient="vertical",
                            command=self.tree.yview)
        self.tree.configure(yscroll=vsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        # Action buttons
        btns = ttk.Frame(self)
        btns.pack(side=tk.TOP, fill=tk.X, padx=10, pady=4)
        ttk.Button(btns, text="Remove Selected",
                   command=self._on_delete).pack(side=tk.LEFT, padx=4)
        ttk.Button(btns, text="Refresh", command=lambda: (
            self._refresh_table(), self._update_totals())).pack(side=tk.LEFT, padx=4)

        # Totals
        totals = ttk.LabelFrame(self, text="Totals")
        totals.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(0, 10))
        self.lbl_income = ttk.Label(totals, text="Income: $0.00")
        self.lbl_expense = ttk.Label(totals, text="Expenses: $0.00")
        self.lbl_net = ttk.Label(totals, text="Net: $0.00")
        self.lbl_income.pack(side=tk.LEFT, padx=12, pady=6)
        self.lbl_expense.pack(side=tk.LEFT, padx=12, pady=6)
        self.lbl_net.pack(side=tk.LEFT, padx=12, pady=6)

        # Reports quick buttons
        rpt = ttk.LabelFrame(self, text="Reports")
        rpt.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(0, 10))
        ttk.Button(rpt, text="Income vs. Expenses", command=self._open_report_income_vs_expenses).pack(
            side=tk.LEFT, padx=6, pady=6)
        ttk.Button(rpt, text="Expenses by Category", command=self._open_report_expenses_by_category).pack(
            side=tk.LEFT, padx=6, pady=6)
        ttk.Button(rpt, text="Monthly Breakdown", command=self._open_report_monthly_breakdown).pack(
            side=tk.LEFT, padx=6, pady=6)

    # ---------- Actions ----------
    def _on_add(self):
        """Validate form inputs, persist the transaction, and refresh the UI."""
        try:
            date = _validate_date(self.var_date.get())
            desc = (self.var_desc.get() or "").strip()
            if not desc:
                raise ValueError("Description cannot be empty.")
            cat = (self.var_cat.get() or "").strip()
            amt = _parse_amount(self.var_amt.get())
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
        """Reset the form fields to their defaults after a successful add."""
        self.var_date.set(_today())
        self.var_desc.set("")
        self.var_cat.set("")
        self.var_amt.set("")
        self.var_type.set("expense")

    def _on_delete(self):
        """Remove the currently selected row from the table and storage.

        Shows a friendly message when nothing is selected or when the index is
        out of range.
        """
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
            messagebox.showwarning(
                "Invalid index", f"Valid range is 0 to {total-1}.")
        self._refresh_table()
        self._update_totals()

    # ---------- Data/Display ----------
    def _refresh_table(self):
        """Reload the transactions from storage and repopulate the table."""
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
        """Recalculate and display Income, Expenses, and Net totals."""
        txns = load_transactions()
        inc = total_income(txns)
        exp = total_expenses(txns)
        net = inc - exp
        self.lbl_income.config(text=f"Income: ${inc:,.2f}")
        self.lbl_expense.config(text=f"Expenses: ${exp:,.2f}")
        self.lbl_net.config(text=f"Net: ${net:,.2f}")

    # ---------- Helpers (Matplotlib) ----------
    def _draw_bar_chart(self, parent: tk.Widget, xlabels: list[str], series: dict[str, list[float]], title: str, ylabel: str = ""):
        """Embed a grouped bar chart inside a Tk widget.

        Parameters
        ----------
        parent : tk.Widget
            The container where the Matplotlib canvas will be packed.
        xlabels : list[str]
            Labels for the x‑axis (e.g., months or category names).
        series : dict[str, list[float]]
            Mapping from legend label to values aligned to ``xlabels``.
        title : str
            Title displayed above the axes.
        ylabel : str, optional
            Y‑axis label, by default "".

        Notes
        -----
        Bars are slightly offset to show multiple series side‑by‑side per label.
        If no data is provided, a friendly "no data" label is shown instead.
        """
        fig = Figure(figsize=(6.8, 3.4), dpi=100)
        ax = fig.add_subplot(111)

        n = len(xlabels)
        if n == 0:
            ttk.Label(parent, text="(no data for chart)").pack()
            return

        k = max(1, len(series))
        width = 0.8 / k
        indices = list(range(n))

        # Plot each series side-by-side per x tick
        for i, (name, values) in enumerate(series.items()):
            # Pad or trim values to match xlabels length safely
            vals = list(values)[:n] + [0.0] * max(0, n - len(values))
            offs = [idx - 0.4 + width/2 + i*width for idx in indices]
            ax.bar(offs, vals, width=width, label=name)

        ax.set_title(title)
        ax.set_ylabel(ylabel)
        ax.set_xticks(indices)
        ax.set_xticklabels(xlabels, rotation=45, ha="right")
        ax.legend()
        ax.grid(True, axis='y', linestyle=':', linewidth=0.5)
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # ---------- Reports ----------
    def _open_report_income_vs_expenses(self):
        """Open a window with overall Income vs. Expense totals and a bar chart."""
        txns = load_transactions()
        inc = total_income(txns)
        exp = total_expenses(txns)
        net = inc - exp

        win = tk.Toplevel(self)
        win.title("Income vs. Expenses")
        win.geometry("600x420")
        win.resizable(True, True)

        frm = ttk.Frame(win, padding=12)
        frm.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            frm, text="--- Total Income vs. Total Expenses ---").pack(anchor="w")
        ttk.Label(frm, text=f"Total Income  : ${inc:,.2f}").pack(
            anchor="w", pady=(6, 0))
        ttk.Label(frm, text=f"Total Expense : ${exp:,.2f}").pack(anchor="w")
        ttk.Label(frm, text=f"Net           : ${net:,.2f}").pack(anchor="w")

        if inc > 0:
            ratio = (exp / inc) * 100
            ttk.Label(
                frm, text=f"Expense / Income: {ratio:,.2f}%").pack(anchor="w", pady=(6, 8))
        elif exp > 0:
            ttk.Label(
                frm, text="Expense / Income: ∞ (no income yet)").pack(anchor="w", pady=(6, 8))
        else:
            ttk.Label(frm, text="No transactions yet.").pack(
                anchor="w", pady=(6, 8))

        # --- Chart: simple bar for Income vs Expense ---
        chart_frame = ttk.LabelFrame(frm, text="Chart")
        chart_frame.pack(fill=tk.BOTH, expand=True)
        self._draw_bar_chart(
            chart_frame,
            xlabels=["Totals"],
            series={"Income": [inc], "Expense": [exp]},
            title="Income vs. Expenses",
            ylabel="Amount"
        )

        ttk.Button(frm, text="Refresh", command=lambda: (win.destroy(
        ), self._open_report_income_vs_expenses())).pack(anchor="e", pady=(12, 0))

    def _open_report_expenses_by_category(self):
        """Open a window listing expense totals by category plus a bar chart."""
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
        win.geometry("820x540")
        win.resizable(True, True)

        frm = ttk.Frame(win, padding=10)
        frm.pack(fill=tk.BOTH, expand=True)

        # Top: table
        table_frame = ttk.Frame(frm)
        table_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        cols = ("category", "total")
        tree = ttk.Treeview(table_frame, columns=cols,
                            show="headings", height=10)
        tree.heading("category", text="Category")
        tree.column("category", width=300)
        tree.heading("total", text="Total")
        tree.column("total", width=160, anchor="e")

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscroll=vsb.set)
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        for cat, total in rows:
            tree.insert("", "end", values=(cat, f"${total:,.2f}"))

        # Bottom: chart
        chart_frame = ttk.LabelFrame(frm, text="Chart")
        chart_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=(8, 0))

        if rows:
            labels = [c for c, _ in rows]
            amounts = [v for _, v in rows]
            # If too many categories, keep top 12 for readability
            if len(labels) > 12:
                labels = labels[:12]
                amounts = amounts[:12]
            self._draw_bar_chart(chart_frame, labels, {
                                 "Expense": amounts}, title="Expenses by Category", ylabel="Amount")
        else:
            ttk.Label(chart_frame, text="(no expenses found)").pack(pady=12)

        # Footer
        footer = ttk.Frame(win, padding=(10, 0, 10, 10))
        footer.pack(fill=tk.X)
        ttk.Button(footer, text="Refresh", command=lambda: (
            win.destroy(), self._open_report_expenses_by_category())).pack(side=tk.RIGHT)

        if not rows:
            messagebox.showinfo("Expenses by Category", "(no expenses found)")

    def _open_report_monthly_breakdown(self):
        """Open a window with month buckets and a grouped monthly bar chart."""
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
        win.geometry("920x600")
        win.resizable(True, True)

        frm = ttk.Frame(win, padding=10)
        frm.pack(fill=tk.BOTH, expand=True)

        # Top: table
        table_frame = ttk.Frame(frm)
        table_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        cols = ("month", "income", "expense", "net")
        tree = ttk.Treeview(table_frame, columns=cols,
                            show="headings", height=12)
        for c, txt, w, anchor in [
            ("month",  "Month",   120, "w"),
            ("income", "Income",  150, "e"),
            ("expense", "Expense", 150, "e"),
            ("net",    "Net",     150, "e"),
        ]:
            tree.heading(c, text=txt)
            tree.column(c, width=w, anchor=anchor)

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscroll=vsb.set)
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        months, incomes, expenses = [], [], []
        for ym, v in rows:
            net = v["income"] - v["expense"]
            tree.insert("", "end", values=(
                ym, f"${v['income']:,.2f}", f"${v['expense']:,.2f}", f"${net:,.2f}"))
            months.append(ym)
            incomes.append(v["income"])
            expenses.append(v["expense"])

        # Bottom: chart (bar chart per month)
        chart_frame = ttk.LabelFrame(frm, text="Monthly Bar Chart")
        chart_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=(8, 0))
        if months:
            self._draw_bar_chart(
                chart_frame,
                xlabels=months,
                series={"Income": incomes, "Expense": expenses},
                title="Monthly Income vs Expense",
                ylabel="Amount"
            )
        else:
            ttk.Label(chart_frame, text="(no transactions)").pack(pady=12)

        footer = ttk.Frame(win, padding=(10, 0, 10, 10))
        footer.pack(fill=tk.X)
        ttk.Button(footer, text="Refresh", command=lambda: (
            win.destroy(), self._open_report_monthly_breakdown())).pack(side=tk.RIGHT)

        if not rows:
            messagebox.showinfo("Monthly Breakdown", "(no transactions)")

# ---- Public entrypoint expected by the Core ----


def menu():
    """Launch the Expense Slasher GUI application."""
    app = ExpenseSlasherGUI()
    app.mainloop()
