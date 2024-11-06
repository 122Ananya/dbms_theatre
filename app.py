
# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import hashlib
import subprocess
import os

app = Flask(__name__)
app.secret_key = 'dev_key'  # Simple key for local development

# Define the absolute path to the database
DB_PATH = "theatre_management.db"

# Function to connect to the existing database
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    """Hashes the password with SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/register', methods=['POST'])
def register():
    name = request.form['name']
    email = request.form['email']
    phone_number = request.form['phone_number']
    password = request.form['password']
    role = request.form['role']
    password_hash = hash_password(password)

    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO User (name, email, phone_number, password_hash, role) VALUES (?, ?, ?, ?, ?)",
            (name, email, phone_number, password_hash, role)
        )
        conn.commit()
        flash('User registered successfully!')
        
        # Redirect based on role
        if role == 'employee':
            return redirect(url_for('employee'))
        return redirect(url_for('index'))
    
    except sqlite3.IntegrityError:
        flash('Error: Email already exists.')
        return redirect(url_for('signup'))
    finally:
        conn.close()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['username']
        password = request.form['password']
        password_hash = hash_password(password)

        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM User WHERE email = ? AND password_hash = ?", (email, password_hash))
        user = c.fetchone()
        conn.close()

        if user:
            session['user_id'] = user['user_id']
            session['username'] = user['name']
            session['role'] = user['role']
            flash("Login successful!")
            # Redirect to employee dashboard if the role is 'employee'
            if user['role'] == 'employee':
                return redirect(url_for('employee'))
            return redirect(url_for('index'))
        else:
            flash("Invalid email or password. Please try again.")
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/employee', methods=['GET', 'POST'])
def employee():
    # Check if the user is logged in and is an employee
    if 'role' not in session or session['role'] != 'employee':
        flash("You do not have access to this page.")
        return redirect(url_for('index'))

    conn = get_db_connection()
    c = conn.cursor()

    if request.method == 'POST':
        # Form submission to add a new movie and showtime
        name = request.form['name']
        release_date = request.form['release_date']
        language = request.form['language']
        genre = request.form['genre']
        rating = request.form['rating']
        poster_image = request.form['poster_image']

        # Insert the new movie into the Movie table
        c.execute("INSERT INTO Movie (name, release_date, language, genre, rating, poster_image) VALUES (?, ?, ?, ?, ?, ?)",
                  (name, release_date, language, genre, rating, poster_image))
        conn.commit()

        # Retrieve the movie ID of the newly added movie
        movie_id = c.lastrowid

        # Insert showtime details
        show_date = request.form['show_date']
        show_time = request.form['show_time']
        c.execute("INSERT INTO Showtime (movie_id, date, time) VALUES (?, ?, ?)", (movie_id, show_date, show_time))
        conn.commit()

        flash('Movie and showtime added successfully!')

    # Retrieve all movies for display
    c.execute("SELECT * FROM Movie")
    movies = c.fetchall()

    # Retrieve all showtimes for display
    c.execute("SELECT Showtime.showtime_id, Movie.name, Showtime.date, Showtime.time FROM Showtime JOIN Movie ON Showtime.movie_id = Movie.movie_id")
    showtimes = c.fetchall()

    conn.close()
    return render_template('employee.html', movies=movies, showtimes=showtimes)

@app.route('/edit_showtime/<int:showtime_id>', methods=['GET', 'POST'])
def edit_showtime(showtime_id):
    conn = get_db_connection()
    c = conn.cursor()

    if request.method == 'POST':
        # Update showtime details
        new_date = request.form['date']
        new_time = request.form['time']
        c.execute("UPDATE Showtime SET date = ?, time = ? WHERE showtime_id = ?", (new_date, new_time, showtime_id))
        conn.commit()
        conn.close()
        flash('Showtime updated successfully!')
        return redirect(url_for('employee'))

    # For GET request, retrieve current showtime details
    c.execute("SELECT * FROM Showtime WHERE showtime_id = ?", (showtime_id,))
    showtime = c.fetchone()
    conn.close()

    return render_template('edit_showtime.html', showtime=showtime)


@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for('index'))

if __name__ == '__main__':
    subprocess.run(["python", os.path.join(os.path.dirname(__file__), "initialize_db.py")])
    app.run(debug=True)
