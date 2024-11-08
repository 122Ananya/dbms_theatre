from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__,template_folder='templates')
app.secret_key = 'your_secret_key'  


DATABASE = 'database.db'


theatre_credentials = {
    "manager1": "password1",
    "manager2": "password2",
    "manager3": "password3",
    "manager4": "password4",
    "manager5": "password5",
    "manager6": "password6",
    "manager7": "password7"
}


def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login_page():
    return render_template('login.html', signup_error=None, login_error=None)

@app.route('/signup', methods=['POST'])
def signup():
    username = request.form['username']
    password = request.form['password']
    confirm_password = request.form['confirm_password']

    if password != confirm_password:
        return render_template('login.html', signup_error="Password mismatch", login_error=None, right_panel_active=True)

    hashed_password = generate_password_hash(password)

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    existing_user = cursor.fetchone()

    if existing_user:
        conn.close()
        return render_template('login.html', signup_error="Username already exists", login_error=None, right_panel_active=True)

    cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
    conn.commit()
    conn.close()

    flash('Account created successfully! Please log in.', 'success')
    return redirect(url_for('login_page'))

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()

    if user is None or not check_password_hash(user[2], password):
        return render_template('login.html', signup_error=None, login_error="Credentials mismatch")

    session['username'] = username
    flash('Login successful!', 'success')
    return redirect(url_for('index'))

@app.route('/theatrelogin', methods=['GET', 'POST'])
def theatre_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username in theatre_credentials and theatre_credentials[username] == password:
            session['theatre_username'] = username  # Log in as theatre user
            flash('Logged in successfully as theatre manager', 'success')
            return redirect(url_for('theatre_dashboard'))
        else:
            return render_template('theatre_login.html', login_error="Invalid username or password")

    return render_template('theatre_login.html', login_error=None)

@app.route('/theatre_dashboard')
def theatre_dashboard():
    if 'theatre_username' not in session:
        flash("Please log in to access the theatre dashboard", "error")
        return redirect(url_for('theatre_login'))
    return render_template('theatre_dashboard.html')  

@app.route('/theatre_logout')
def theatre_logout():
    session.pop('theatre_username', None)
    flash("Logged out successfully", "success")
    return redirect(url_for('theatre_login'))

if __name__ == '__main__':
    app.run(debug=True,port=5001)
