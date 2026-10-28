import csv
import io
import os
import sqlite3
from datetime import date, datetime
from functools import wraps

from flask import Flask, flash, make_response, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(BASE_DIR, "expense_tracker.db")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-this-development-secret")


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with get_db() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            kind TEXT NOT NULL CHECK(kind IN ('income', 'expense')),
            amount REAL NOT NULL CHECK(amount > 0),
            category TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            transaction_date TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            month TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL CHECK(amount > 0),
            UNIQUE(user_id, month, category),
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """)
        db.commit()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "info")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def current_month():
    return date.today().strftime("%Y-%m")


@app.context_processor
def inject_globals():
    return {"current_year": date.today().year}


@app.route("/")
def index():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not name or not email or len(password) < 8:
            flash("Enter your name and email, and use a password of at least 8 characters.", "error")
            return render_template("register.html")
        try:
            with get_db() as db:
                db.execute(
                    "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                    (name, email, generate_password_hash(password))
                )
                db.commit()
            flash("Account created. You can now log in.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("An account with that email already exists.", "error")
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        with get_db() as db:
            user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            flash("Welcome back!", "success")
            return redirect(url_for("dashboard"))
        flash("Invalid email or password.", "error")
    return render_template("login.html")


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


@app.route("/dashboard")
@login_required
def dashboard():
    month = request.args.get("month", current_month())
    if not valid_month(month):
        month = current_month()
    user_id = session["user_id"]
    with get_db() as db:
        totals = db.execute("""
            SELECT
              COALESCE(SUM(CASE WHEN kind='income' THEN amount ELSE 0 END), 0) AS income,
              COALESCE(SUM(CASE WHEN kind='expense' THEN amount ELSE 0 END), 0) AS expenses
            FROM transactions
            WHERE user_id=? AND substr(transaction_date, 1, 7)=?
        """, (user_id, month)).fetchone()
        recent = db.execute("""
            SELECT * FROM transactions WHERE user_id=?
            ORDER BY transaction_date DESC, id DESC LIMIT 6
        """, (user_id,)).fetchall()
        categories = db.execute("""
            SELECT category, SUM(amount) AS total FROM transactions
            WHERE user_id=? AND kind='expense' AND substr(transaction_date,1,7)=?
            GROUP BY category ORDER BY total DESC
        """, (user_id, month)).fetchall()
        monthly = db.execute("""
            SELECT substr(transaction_date,1,7) AS month,
              SUM(CASE WHEN kind='income' THEN amount ELSE 0 END) AS income,
              SUM(CASE WHEN kind='expense' THEN amount ELSE 0 END) AS expenses
            FROM transactions WHERE user_id=?
              AND transaction_date >= date(?, '-5 months', 'start of month')
              AND transaction_date < date(?, '+1 month', 'start of month')
            GROUP BY substr(transaction_date,1,7) ORDER BY month
        """, (user_id, month + "-01", month + "-01")).fetchall()
        budgets = db.execute("""
            SELECT b.category, b.amount AS budget,
              COALESCE(SUM(t.amount),0) AS spent
            FROM budgets b LEFT JOIN transactions t
              ON t.user_id=b.user_id AND t.category=b.category AND t.kind='expense'
              AND substr(t.transaction_date,1,7)=b.month
            WHERE b.user_id=? AND b.month=?
            GROUP BY b.id ORDER BY b.category
        """, (user_id, month)).fetchall()
    income = float(totals["income"])
    expenses = float(totals["expenses"])
    chart_categories = [r["category"] for r in categories]
    chart_amounts = [round(float(r["total"]), 2) for r in categories]
    month_map = {r["month"]: r for r in monthly}
    month_labels = []
    month_income = []
    month_expenses = []
    from datetime import date as dt_date
    y, m = map(int, month.split("-"))
    for offset in range(5, -1, -1):
        idx = y * 12 + (m - 1) - offset
        yy, mm = divmod(idx, 12)
        key = f"{yy:04d}-{mm+1:02d}"
        month_labels.append(key)
        row = month_map.get(key)
        month_income.append(round(float(row["income"]), 2) if row else 0)
        month_expenses.append(round(float(row["expenses"]), 2) if row else 0)
    return render_template(
        "dashboard.html", month=month, income=income, expenses=expenses,
        balance=income-expenses, recent=recent, categories=categories,
        chart_categories=chart_categories, chart_amounts=chart_amounts,
        month_labels=month_labels, month_income=month_income,
        month_expenses=month_expenses, budgets=budgets
    )


def valid_month(value):
    try:
        datetime.strptime(value, "%Y-%m")
        return True
    except (ValueError, TypeError):
        return False


def valid_date(value):
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except (ValueError, TypeError):
        return False


@app.route("/transactions")
@login_required
def transactions():
    kind = request.args.get("kind", "")
    search = request.args.get("q", "").strip()
    month = request.args.get("month", "")
    query = "SELECT * FROM transactions WHERE user_id=?"
    params = [session["user_id"]]
    if kind in ("income", "expense"):
        query += " AND kind=?"
        params.append(kind)
    if month and valid_month(month):
        query += " AND substr(transaction_date,1,7)=?"
        params.append(month)
    if search:
        query += " AND (category LIKE ? OR description LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])
    query += " ORDER BY transaction_date DESC, id DESC"
    with get_db() as db:
        rows = db.execute(query, params).fetchall()
    return render_template("transactions.html", transactions=rows, kind=kind, month=month, q=search)


@app.route("/transactions/add", methods=["GET", "POST"])
@login_required
def add_transaction():
    if request.method == "POST":
        kind = request.form.get("kind", "")
        category = request.form.get("category", "").strip()
        description = request.form.get("description", "").strip()
        amount_text = request.form.get("amount", "")
        trans_date = request.form.get("transaction_date", "")
        try:
            amount = float(amount_text)
        except ValueError:
            amount = 0
        if kind not in ("income", "expense") or not category or amount <= 0 or not valid_date(trans_date):
            flash("Check the transaction type, category, positive amount, and date.", "error")
            return render_template("transaction_form.html", transaction=None, today=date.today().isoformat())
        with get_db() as db:
            db.execute("""
                INSERT INTO transactions (user_id, kind, amount, category, description, transaction_date)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (session["user_id"], kind, amount, category, description, trans_date))
            db.commit()
        flash("Transaction added.", "success")
        return redirect(url_for("transactions"))
    return render_template("transaction_form.html", transaction=None, today=date.today().isoformat())


@app.route("/transactions/<int:transaction_id>/edit", methods=["GET", "POST"])
@login_required
def edit_transaction(transaction_id):
    with get_db() as db:
        row = db.execute("SELECT * FROM transactions WHERE id=? AND user_id=?",
                         (transaction_id, session["user_id"])).fetchone()
        if not row:
            flash("Transaction not found.", "error")
            return redirect(url_for("transactions"))
        if request.method == "POST":
            kind = request.form.get("kind", "")
            category = request.form.get("category", "").strip()
            description = request.form.get("description", "").strip()
            try:
                amount = float(request.form.get("amount", ""))
            except ValueError:
                amount = 0
            trans_date = request.form.get("transaction_date", "")
            if kind not in ("income", "expense") or not category or amount <= 0 or not valid_date(trans_date):
                flash("Check the transaction type, category, positive amount, and date.", "error")
            else:
                db.execute("""
                    UPDATE transactions SET kind=?, amount=?, category=?, description=?, transaction_date=?
                    WHERE id=? AND user_id=?
                """, (kind, amount, category, description, trans_date, transaction_id, session["user_id"]))
                db.commit()
                flash("Transaction updated.", "success")
                return redirect(url_for("transactions"))
    return render_template("transaction_form.html", transaction=row, today=date.today().isoformat())


@app.route("/transactions/<int:transaction_id>/delete", methods=["POST"])
@login_required
def delete_transaction(transaction_id):
    with get_db() as db:
        db.execute("DELETE FROM transactions WHERE id=? AND user_id=?",
                   (transaction_id, session["user_id"]))
        db.commit()
    flash("Transaction deleted if it existed.", "info")
    return redirect(url_for("transactions"))


@app.route("/budgets", methods=["GET", "POST"])
@login_required
def budgets():
    month = request.values.get("month", current_month())
    if not valid_month(month):
        month = current_month()
    if request.method == "POST":
        category = request.form.get("category", "").strip()
        try:
            amount = float(request.form.get("amount", ""))
        except ValueError:
            amount = 0
        if not category or amount <= 0:
            flash("Enter a category and a budget greater than zero.", "error")
        else:
            with get_db() as db:
                db.execute("""
                    INSERT INTO budgets (user_id, month, category, amount) VALUES (?, ?, ?, ?)
                    ON CONFLICT(user_id, month, category) DO UPDATE SET amount=excluded.amount
                """, (session["user_id"], month, category, amount))
                db.commit()
            flash("Budget saved.", "success")
            return redirect(url_for("budgets", month=month))
    with get_db() as db:
        rows = db.execute("""
            SELECT b.*, COALESCE(SUM(t.amount),0) AS spent
            FROM budgets b LEFT JOIN transactions t
              ON t.user_id=b.user_id AND t.category=b.category AND t.kind='expense'
              AND substr(t.transaction_date,1,7)=b.month
            WHERE b.user_id=? AND b.month=?
            GROUP BY b.id ORDER BY b.category
        """, (session["user_id"], month)).fetchall()
    return render_template("budgets.html", budgets=rows, month=month)


@app.route("/budgets/<int:budget_id>/delete", methods=["POST"])
@login_required
def delete_budget(budget_id):
    with get_db() as db:
        db.execute("DELETE FROM budgets WHERE id=? AND user_id=?", (budget_id, session["user_id"]))
        db.commit()
    flash("Budget deleted.", "info")
    return redirect(url_for("budgets"))


@app.route("/export.csv")
@login_required
def export_csv():
    with get_db() as db:
        rows = db.execute("""
            SELECT transaction_date, kind, category, description, amount
            FROM transactions WHERE user_id=? ORDER BY transaction_date DESC, id DESC
        """, (session["user_id"],)).fetchall()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Type", "Category", "Description", "Amount"])
    for row in rows:
        writer.writerow([row["transaction_date"], row["kind"], row["category"], row["description"], row["amount"]])
    response = make_response(output.getvalue())
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = "attachment; filename=expense_transactions.csv"
    return response


@app.errorhandler(404)
def not_found(_error):
    return render_template("404.html"), 404


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
