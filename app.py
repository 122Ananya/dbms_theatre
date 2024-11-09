# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import subprocess
import os
from PIL import Image
from datetime import datetime

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
    return redirect(url_for('login'))
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Connect to the database and check user credentials
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM User WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):  # Assuming user[2] is the password hash
            session['user_id'] = user[0]  # Set session user ID or another identifier
            return redirect(url_for('customer_page'))  # Redirect to the customer page
        else:
            return render_template('login_signup.html', login_error="Invalid username or password")

    # GET request renders the login and signup page
    return render_template('login_signup.html')


@app.route('/theatrelogin', methods=['GET', 'POST'])
def theatre_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username in theatre_credentials and theatre_credentials[username] == password:
            session['theatre_username'] = username  # Log in as theatre user
            flash('Logged in successfully as theatre manager', 'success')
            return redirect(url_for('employee'))
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


#customer page part
@app.route('/customer')
def customer_page():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Fetch all movies with movie_id as the first column
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT movie_id, name, release_date, language, genre, rating, poster_image, description FROM Movie')
    movies = cursor.fetchall()
    conn.close()

    # Pass the movies data to the template
    return render_template('customer.html', movies=movies)


@app.route('/book_ticket/<int:movie_id>')
def book_ticket(movie_id):
    # Implement booking logic or showtimes for the selected movie
    return f"Booking page for movie ID: {movie_id}"


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
@app.route('/showtime', methods=['GET', 'POST'])
def showtime():
    conn = get_db_connection()

    if request.method == 'POST':
        action_type = request.form['action_type']

        if action_type == 'add':
            movie_id = request.form['movie_id']
            screen_number = request.form['screen_number']
            date = request.form['date']
            time = request.form['time']

            show_datetime = datetime.strptime(f"{date} {time}", '%Y-%m-%d %H:%M')
            current_datetime = datetime.now()

            if show_datetime <= current_datetime:
                flash('Showtime must be scheduled for a future date and time.')
                return redirect(url_for('showtime'))

            conn.execute('''
            INSERT INTO Showtime (movie_id, screen_number, date, time)
            VALUES (?, ?, ?, ?);
            ''', (movie_id, screen_number, date, time))
            flash('New showtime added successfully!')

        elif action_type == 'edit':
            showtime_id = request.form['showtime_id']
            movie_id = request.form['movie_id']
            screen_number = request.form['screen_number']
            date = request.form['date']
            time = request.form['time']

            conn.execute('''
            UPDATE Showtime
            SET movie_id = ?, screen_number = ?, date = ?, time = ?
            WHERE showtime_id = ?;
            ''', (movie_id, screen_number, date, time, showtime_id))
            flash('Showtime updated successfully!')

        elif action_type == 'delete':
            showtime_id = request.form['showtime_id']
            conn.execute('DELETE FROM Showtime WHERE showtime_id = ?;', (showtime_id,))
            flash('Showtime deleted successfully!')

        conn.commit()
        conn.close()
        return redirect(url_for('showtime'))

    showtimes = conn.execute('''
    SELECT
    S.showtime_id,
    M.name AS Movie,
    S.date AS Show_Date,
    TIME(S.time, 'localtime') AS Start_Time,
    TIME(S.time, 'localtime', '+' || 
        (CAST(SUBSTR(M.duration, 1, 2) AS INTEGER) * 60 + 
        CAST(SUBSTR(M.duration, 4, 2) AS INTEGER)) || ' minute'
    ) AS End_Time,
    M.description AS Description,
    strftime('%Y-%m-%d', M.release_date) AS Release_Date,
    Sc.screen_number AS Screen_Number
FROM
    Showtime AS S
JOIN
    Movie AS M ON S.movie_id = M.movie_id
JOIN
    Screen AS Sc ON S.screen_number = Sc.screen_number;

    ''').fetchall()

    movies = conn.execute('SELECT movie_id, name, strftime("%Y-%m-%d", release_date) AS release_date FROM Movie').fetchall()
    screens = conn.execute('SELECT screen_number FROM Screen').fetchall()
    conn.close()

    return render_template('showtime.html', showtimes=[dict(i) for i in showtimes], movies=movies, screens=screens)



if __name__ == '__main__':
    subprocess.run(["python", os.path.join(os.path.dirname(__file__), "initialize_db.py")])
    app.run(debug=True)
