
# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import sqlite3
import hashlib
import subprocess
import os
from PIL import Image

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
        elif role == 'customer':
                return redirect(url_for('movie_display'))
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
            elif user['role'] == 'customer':
                return redirect(url_for('movie_display'))
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


    # Retrieve all movies for display
    c.execute("SELECT * FROM Movie")
    movies = c.fetchall()

    conn.close()
    return render_template('employee.html', movies=movies)




@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for('index'))


# adding movie by employee
@app.route('/movies')
def show_movies():
    conn = get_db_connection()
    movies = conn.execute('SELECT * FROM Movie').fetchall()
    conn.close()
    return render_template('employee.html', movies=movies)

@app.route('/add_movie', methods=['POST'])
def add_movie():
    name = request.form['movie-name']
    release_date = request.form['release-date']
    language = request.form['language']
    genre = request.form['genre']
    rating = request.form['rating']
    description = request.form['description']
    poster = request.files['poster']
    
    # Define the path for the upload folder
    img_folder = os.path.join('static', 'img')
    
    # Check if the img folder exists, and create it if it doesn’t
    if not os.path.exists(img_folder):
        os.makedirs(img_folder)

    # Save the poster file in the img folder with resizing
    poster_path = os.path.join(img_folder, poster.filename)
    
    # Open the uploaded image and resize it
    with Image.open(poster) as img:
        resized_img = img.resize((100, 100))  
        resized_img.save(poster_path)

    # Store movie details in the database
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO Movie (name, release_date, language, genre, rating, description, poster_image) VALUES (?, ?, ?, ?, ?, ?, ?)',
        (name, release_date, language, genre, rating, description, poster.filename)
    )
    conn.commit()
    conn.close()
    
    return jsonify({"message": "Movie added successfully"}), 200

@app.route('/delete_movie/<int:movie_id>', methods=['DELETE'])
def delete_movie(movie_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Retrieve the poster image filename
    cursor.execute('SELECT poster_image FROM Movie WHERE movie_id = ?', (movie_id,))
    result = cursor.fetchone()

    # Check if an image path is found, then delete the file
    if result:
        poster_image = result['poster_image']
        image_path = os.path.join('static', 'img', poster_image)
        if os.path.exists(image_path):
            os.remove(image_path)

    # Delete the movie from the Movie table
    cursor.execute('DELETE FROM Movie WHERE movie_id = ?', (movie_id,))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Movie and poster image deleted successfully'}), 200


#show time 
@app.route('/showtime')
def showtime():
    conn = get_db_connection()  # Assuming this function connects to your database
    showtimes = conn.execute('SELECT * FROM Showtime').fetchall()  # Adjust table/field names as needed
    conn.close()

    return render_template('showtime.html', showtimes=showtimes)



if __name__ == '__main__':
    subprocess.run(["python", os.path.join(os.path.dirname(__file__), "initialize_db.py")])
    app.run(debug=True)
