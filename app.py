# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import subprocess
import os
from PIL import Image

app = Flask(__name__)
app.secret_key = 'dev_key'  # Simple key for local development

# Define the absolute path to the database
DB_PATH = "theatre_management.db"


theatre_credentials = {
    "manager1": "password1",
    "manager2": "password2",
    "manager3": "password3",
    "manager4": "password4",
    "manager5": "password5",
    "manager6": "password6",
    "manager7": "password7"
}

# Function to connect to the existing database
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

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
    
    conn = sqlite3.connect(DB_PATH)    
    c = conn.cursor()
    
    c.execute('SELECT * FROM User WHERE username = ?', (username,))
    existing_user = c.fetchone()

    if existing_user:
        conn.close()
        return render_template('login.html', signup_error="Username already exists", login_error=None, right_panel_active=True)
    
    c.execute('INSERT INTO User (username,password) VALUES (?, ?)',(username, hashed_password))
    conn.commit()
    conn.close()
        
    flash('Account created successfully! Please log in.', 'success')
    return redirect(url_for('login_page'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM User WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()

    if user is None or not check_password_hash(user[2], password):
        return render_template('login.html', signup_error=None, login_error="Credentials mismatch")

    session['username'] = username
    flash('Login successful!', 'success')
    return redirect(url_for('customer'))

@app.route('/theatrelogin', methods=['GET', 'POST'])
def theatre_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username in theatre_credentials and theatre_credentials[username] == password:
            session['theatre_username'] = username  # Log in as theatre user
            flash('Logged in successfully as theatre manager', 'success')
            return redirect(url_for('employee'))
            elif user['role'] == 'customer':
                return redirect(url_for('movie_display'))
        else:
            return render_template('theatre_login.html', login_error="Invalid username or password")

    return render_template('theatre_login.html', login_error=None)


@app.route('/theatre_logout')
def theatre_logout():
    session.pop('theatre_user_id', None)
    session.pop('theatre_username', None)
    flash("You have been logged out.")
    return redirect(url_for('index'))

@app.route('/employee', methods=['GET', 'POST'])
def employee():
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
