from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)

@app.context_processor
def inject_datetime():
    return {'datetime': datetime}

# Database configuration
DATABASE = 'finance.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with app.app_context():
        db = get_db()
        # Create transactions table
        db.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                date TEXT NOT NULL,
                description TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create budgets table
        db.execute('''
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                limit_amount REAL NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        db.commit()

# Get categories for dropdowns
def get_categories():
    return {
        'income': ['Salary', 'Freelance', 'Investments', 'Gifts', 'Other Income'],
        'expense': ['Food', 'Transportation', 'Housing', 'Utilities', 'Entertainment', 
                   'Healthcare', 'Education', 'Shopping', 'Other Expenses']
    }

# Routes
@app.route('/')
def index():
    db = get_db()
    
    # Get recent transactions
    transactions = db.execute('''
        SELECT * FROM transactions 
        ORDER BY date DESC, created_at DESC
        LIMIT 5
    ''').fetchall()
    
    # Get financial summary
    summary = db.execute('''
        SELECT 
            SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as income,
            SUM(CASE WHEN amount < 0 THEN amount ELSE 0 END) as expenses
        FROM transactions
    ''').fetchone()
    
    income = summary['income'] or 0
    expenses = summary['expenses'] or 0
    
    return render_template('index.html',
                         transactions=transactions,
                         income=income,
                         expenses=expenses,
                         active_page='dashboard')

@app.route('/transactions', methods=['GET', 'POST'])
def transactions():
    db = get_db()
    categories = get_categories()
    
    if request.method == 'POST':
        try:
            amount = float(request.form['amount'])
            if request.form['type'] == 'expense':
                amount = -abs(amount)
            category = request.form['category']
            description = request.form.get('description', '').strip()
            date = request.form.get('date', datetime.now().strftime('%Y-%m-%d'))
            
            db.execute('''
                INSERT INTO transactions (amount, category, date, description)
                VALUES (?, ?, ?, ?)
            ''', (amount, category, date, description))
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"Error adding transaction: {e}")
        
        return redirect(url_for('transactions'))
    
    # Get all transactions
    transactions = db.execute('''
        SELECT * FROM transactions 
        ORDER BY date DESC, created_at DESC
    ''').fetchall()
    
    return render_template('transactions.html',
                         transactions=transactions,
                         categories=categories,
                         active_page='transactions')

@app.route('/transactions/<int:transaction_id>/delete', methods=['POST'])
def delete_transaction(transaction_id):
    db = get_db()
    
    # First get the transaction before deleting
    transaction = db.execute(
        'SELECT * FROM transactions WHERE id = ?', 
        (transaction_id,)
    ).fetchone()
    
    if transaction:
        # Delete the transaction
        db.execute(
            'DELETE FROM transactions WHERE id = ?',
            (transaction_id,)
        )
        db.commit()
        flash('Transaction deleted successfully', 'success')
    else:
        flash('Transaction not found', 'error')
    
    return redirect(url_for('transactions'))

@app.route('/budgets', methods=['GET', 'POST'])
def budgets():
    db = get_db()
    categories = get_categories()
    
    if request.method == 'POST':
        try:
            category = request.form['category']
            limit_amount = float(request.form['limit_amount'])
            
            db.execute('''
                INSERT INTO budgets (category, limit_amount)
                VALUES (?, ?)
            ''', (category, limit_amount))
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"Error creating budget: {e}")
        
        return redirect(url_for('budgets'))
    
    # Get budgets with spending data
    budgets = db.execute('''
        SELECT b.*, 
               COALESCE(SUM(ABS(t.amount)), 0) as spent
        FROM budgets b
        LEFT JOIN transactions t ON b.category = t.category AND t.amount < 0
        GROUP BY b.id
        ORDER BY b.category
    ''').fetchall()
    
    return render_template('budgets.html',
                         budgets=budgets,
                         categories=categories['expense'],
                         active_page='budgets')

# @app.route('/budgets/<int:id>/delete', methods=['POST'])
# def delete_budget(id):
#    db = get_db()
#    db.execute('DELETE FROM budgets WHERE id = ?', (id,))
#    db.commit()
#    return redirect(url_for('budgets'))

@app.route('/budgets/<int:budget_id>/delete', methods=['POST'])
def delete_budget(budget_id):
    db = get_db()
    try:
        # Check if budget exists
        budget = db.execute('SELECT * FROM budgets WHERE id = ?', (budget_id,)).fetchone()
        if not budget:
            return jsonify({'success': False, 'error': 'Budget not found'}), 404
        
        # Delete the budget
        db.execute('DELETE FROM budgets WHERE id = ?', (budget_id,))
        db.commit()
        return jsonify({'success': True, 'budget_id': budget_id})
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/reports')
def reports():
    return render_template('reports.html', active_page='reports')

@app.route('/api/reports/data')
def reports_data():
    db = get_db()
    report_type = request.args.get('type', 'monthly')
    
    if report_type == 'monthly':
        data = db.execute('''
            SELECT strftime('%Y-%m', date) as period,
                   SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as income,
                   SUM(CASE WHEN amount < 0 THEN amount ELSE 0 END) as expenses
            FROM transactions
            GROUP BY period
            ORDER BY period
        ''').fetchall()
    elif report_type == 'category':
        data = db.execute('''
            SELECT category,
                   SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as income,
                   SUM(CASE WHEN amount < 0 THEN amount ELSE 0 END) as expenses
            FROM transactions
            GROUP BY category
            ORDER BY category
        ''').fetchall()
    else:  # income-vs-expense
        data = db.execute('''
            SELECT strftime('%Y-%m', date) as period,
                   SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as income,
                   SUM(CASE WHEN amount < 0 THEN amount ELSE 0 END) as expenses
            FROM transactions
            GROUP BY period
            ORDER BY period
        ''').fetchall()
    
    return jsonify([dict(row) for row in data])

@app.route('/analytics')
def analytics_redirect():
    """Redirect to the Streamlit Cloud analytics app"""
    return redirect("https://financeanalytics.streamlit.app")

@app.route('/api/finance-data')
def finance_data():
    db = get_db()
    
    # Get transactions with error handling
    try:
        transactions = db.execute('''
            SELECT date, amount, category, description
            FROM transactions
            ORDER BY date DESC
        ''').fetchall()
    except Exception as e:
        transactions = []
        print(f"Transaction query error: {e}")

    # Get budgets with error handling
    try:
        budgets = db.execute('''
            SELECT category, limit_amount
            FROM budgets
        ''').fetchall()
    except Exception as e:
        budgets = []
        print(f"Budget query error: {e}")

    # Return proper JSON response
    return jsonify({
        'transactions': [dict(t) for t in transactions],
        'budgets': [dict(b) for b in budgets],
        'status': 'success'
    })

if __name__ == '__main__':
    init_db()
    app.run(debug=True)