# Personal Expense Tracking and Analysis System

A responsive Flask website for managing personal income, expenses, category budgets, and spending insights.

## Features
- Account registration and login with hashed passwords
- Personal dashboard showing monthly income, expenses, and balance
- Add, edit, delete, search, and filter transactions
- Six-month income/expense chart and category expense chart
- Monthly category budgets with spent-versus-budget progress
- Export transactions to CSV
- SQLite database created automatically
- Responsive desktop and mobile layout

## Technology
Python 3.10+, Flask, SQLite, HTML, CSS, JavaScript, Chart.js (CDN).

## Folder structure
```text
personal-expense-tracker/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── .env.example
├── expense_tracker.db       # generated on first run; ignored by Git
├── static/
│   ├── css/style.css
│   └── js/charts.js
└── templates/
    ├── base.html
    ├── index.html
    ├── login.html
    ├── register.html
    ├── dashboard.html
    ├── transactions.html
    ├── transaction_form.html
    ├── budgets.html
    └── 404.html
```

## Run on Windows
1. Install Python 3.10+ from python.org and select **Add Python to PATH** during setup.
2. Open PowerShell in this folder.
3. Create a virtual environment:
   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
   If PowerShell blocks activation, use Command Prompt and run `.venv\Scripts\activate.bat`, or run `\.venv\Scripts\python.exe -m pip install -r requirements.txt` without activating.
4. Install Flask:
   ```powershell
   python -m pip install -r requirements.txt
   ```
5. Start the website:
   ```powershell
   python app.py
   ```
   If `python` is not recognized, try `py app.py`.
6. Open **http://127.0.0.1:5000**, register an account, and add a transaction.

SQLite is created automatically when the app starts. Chart.js is loaded from a CDN, so charts require internet access; the rest of the application runs locally.

## Quick test checklist
- Register with a new email and a password of at least 8 characters.
- Log in and check that the dashboard opens.
- Add an income and an expense; confirm the totals and recent transactions update.
- Edit and delete a transaction.
- Create a budget for the same category as an expense and check the progress bar.
- Filter transactions and export the CSV.
- Log out and confirm protected pages redirect to login.

## Push to GitHub
Create an empty repository on GitHub, then run these commands from this folder:
```powershell
git init
git add .
git commit -m "Build personal expense tracker website"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/personal-expense-tracker.git
git push -u origin main
```
Replace the remote URL with your own repository URL. Never commit `.env`, real secrets, or `expense_tracker.db`.

## Before public deployment
This is a local/college project starter. Before hosting publicly, configure a strong random `SECRET_KEY`, disable Flask debug mode, add CSRF protection and secure cookie settings, use HTTPS, and configure production hosting. Do not store real financial data in a public demo.
"# personal-expense-tracking-and-analysis-system" 
