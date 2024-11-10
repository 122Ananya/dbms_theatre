# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import subprocess
import os
from PIL import Image
from datetime import datetime, timedelta


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
    duration = request.form['duration']
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
        'INSERT INTO Movie (name, release_date, language, genre, rating, description, duration, poster_image) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
        (name, release_date, language, genre, rating, description, duration, poster.filename)
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
    cursor = conn.cursor()

    if request.method == 'POST':
        action_type = request.form.get('action_type')
        movie_id = request.form.get('movie_id')
        screen_number = request.form.get('screen_number')
        date = request.form.get('date')
        time = request.form.get('time')

        if movie_id and screen_number and date and time:
            # Format the time to ensure only HH:MM is stored
            time = datetime.strptime(time, '%H:%M').strftime('%H:%M')
            show_datetime = datetime.strptime(f"{date} {time}", '%Y-%m-%d %H:%M')
            current_datetime = datetime.now()

            # Get the release date of the selected movie
            movie = conn.execute('SELECT release_date, duration FROM Movie WHERE movie_id = ?', (movie_id,)).fetchone()
            if movie:
                release_date = datetime.strptime(movie['release_date'], '%Y-%m-%d')
                release_datetime = datetime.combine(release_date, datetime.min.time())  # Movie release time at 00:00:00

                # Constraint 1: Check if the show date and time is after the movie release
                if show_datetime < release_datetime:
                    flash('Showtime must be after the movie release date.', 'showtime-error')
                    return redirect(url_for('showtime'))

            # Constraint 2: Ensure showtime is today or later but not in the past
            if show_datetime <= current_datetime:
                flash('Showtime must be scheduled for a future date and time.', 'showtime-error')
                return redirect(url_for('showtime'))

            # Constraint 3: Check for schedule overlap on the same screen
            overlapping_showtimes = conn.execute('''
                SELECT S.date, S.time, M.duration
                FROM Showtime AS S
                JOIN Movie AS M ON S.movie_id = M.movie_id
                WHERE S.screen_number = ? AND (S.date = ? OR S.date = DATE(?, '-1 day'))
            ''', (screen_number, date, date)).fetchall()

            for show in overlapping_showtimes:
                existing_start_time = datetime.strptime(f"{show['date']} {show['time']}", '%Y-%m-%d %H:%M')
                duration_hours, duration_minutes = map(int, show['duration'].split(':'))
                existing_end_time = existing_start_time + timedelta(hours=duration_hours, minutes=duration_minutes + 15)

                # Check if the new showtime conflicts with an existing showtime plus a 15-minute break
                if (existing_start_time <= show_datetime < existing_end_time) or (show_datetime < existing_end_time):
                    flash('The selected time conflicts with an existing showtime on the same screen.', 'showtime-error')
                    return redirect(url_for('showtime'))

        try:
            if action_type == 'add':
                conn.execute('''
                    INSERT INTO Showtime (movie_id, screen_number, date, time)
                    VALUES (?, ?, ?, ?);
                ''', (movie_id, screen_number, date, time))
                conn.commit()
                flash('New showtime added successfully!', 'showtime-success')

            elif action_type == 'edit':
                showtime_id = request.form.get('showtime_id')
                conn.execute('''
                    UPDATE Showtime
                    SET movie_id = ?, screen_number = ?, date = ?, time = ?
                    WHERE showtime_id = ?;
                ''', (movie_id, screen_number, date, time, showtime_id))
                conn.commit()
                flash('Showtime updated successfully!', 'showtime-success')

            elif action_type == 'delete':
                showtime_id = request.form.get('showtime_id')
                conn.execute('DELETE FROM Showtime WHERE showtime_id = ?;', (showtime_id,))
                conn.commit()
                flash('Showtime deleted successfully!', 'showtime-success')
        
        except sqlite3.Error as e:
            conn.rollback()
            flash(f"Database error: {e}", 'showtime-error')

    # Query existing showtimes, movies, and screens after handling POST request
    showtimes = cursor.execute('''
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
            Screen AS Sc ON S.screen_number = Sc.screen_number
    ''').fetchall()

    # Query the list of available movies and screens to populate the dropdowns in the showtime form
    movies = cursor.execute('SELECT movie_id, name FROM Movie').fetchall()
    screens = cursor.execute('SELECT screen_number FROM Screen').fetchall()

    # Close the connection after all operations are completed
    conn.close()

    return render_template('showtime.html', showtimes=showtimes, movies=movies, screens=screens)


@app.route('/get_available_showtimes/<int:movie_id>')
def get_available_showtimes(movie_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get the current datetime to filter only upcoming showtimes
    current_datetime = datetime.now()

    # Query the showtimes for a specific movie_id that haven't started yet
    cursor.execute('''
        SELECT showtime_id, date, time, screen_number 
        FROM Showtime 
        WHERE movie_id = ? 
        AND datetime(date || ' ' || time) > ?
    ''', (movie_id, current_datetime))
    showtimes = cursor.fetchall()
    conn.close()
    
    # Convert to list of dictionaries for JSON response, including the screen number
    showtimes_list = [
        {
            "showtime_id": row["showtime_id"],
            "date": row["date"],
            "time": row["time"],
            "screen_number": row["screen_number"]
        }
        for row in showtimes
    ]
    return jsonify(showtimes_list)

#booking tckets by user

@app.route('/book_ticket/<int:movie_id>', methods=['GET', 'POST'])
def book_ticket(movie_id):
    conn = get_db_connection()

    # Retrieve unique dates for showtimes of the selected movie
    dates = conn.execute('''
        SELECT DISTINCT date 
        FROM Showtime 
        WHERE movie_id = ? AND date >= date('now')
        ORDER BY date
    ''', (movie_id,)).fetchall()

    # Fetch all showtime details for the selected movie
    showtime_data = conn.execute('''
        SELECT showtime_id, date, time, screen_number
        FROM Showtime
        WHERE movie_id = ?
        ORDER BY date, time
    ''', (movie_id,)).fetchall()

    conn.close()

    # Render the template with available dates and showtime data
    return render_template('book_ticket.html', movie_id=movie_id, dates=dates, showtime_data=showtime_data)





@app.route('/get_times/<int:movie_id>/<date>', methods=['GET'])
def get_times(movie_id, date):
    conn = get_db_connection()

    # Retrieve available times for the selected date and movie
    times = conn.execute('''
        SELECT showtime_id, time, screen_number 
        FROM Showtime 
        WHERE movie_id = ? AND date = ?
    ''', (movie_id, date)).fetchall()

    conn.close()

    # Return times as JSON
    return jsonify([dict(time) for time in times])


# Route to display showtimes for a specific movie
@app.route('/movie_ticket/<int:movie_id>', methods=['GET', 'POST'])
def book_movie_ticket(movie_id):    
    conn = get_db_connection()

    # Retrieve available showtimes for the selected movie
    showtimes = conn.execute('''
        SELECT S.showtime_id, S.date, S.time, Sc.screen_number
        FROM Showtime S
        JOIN Screen Sc ON S.screen_number = Sc.screen_number
        WHERE S.movie_id = ? AND date >= date('now')
    ''', (movie_id,)).fetchall()

    conn.close()

    # Process POST request to select a specific showtime
    if request.method == 'POST':
        showtime_id = request.form['showtime_id']
        return redirect(url_for('select_seats', showtime_id=showtime_id))

    # Render showtimes for selection
    return render_template('book_ticket.html', showtimes=showtimes, movie_id=movie_id)

def unbook_seats_for_past_showtimes():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Retrieve all showtimes where the show end time is past the current time
    cursor.execute('''
        SELECT S.showtime_id
        FROM Showtime AS S
        JOIN Movie AS M ON S.movie_id = M.movie_id
        WHERE datetime(S.date || ' ' || S.time) < datetime('now', 'localtime')
    ''')
    past_showtimes = cursor.fetchall()

    # Unbook seats for each past showtime
    for showtime in past_showtimes:
        showtime_id = showtime['showtime_id']
        cursor.execute('''
            UPDATE Seat
            SET is_booked = 0
            WHERE seat_id IN (
                SELECT seat_id
                FROM Seat
                WHERE screen_number = (SELECT screen_number FROM Showtime WHERE showtime_id = ?)
            )
        ''', (showtime_id,))

    # Commit changes and close the connection
    conn.commit()
    conn.close()

# Route to select seats for a specific showtime
@app.route('/select_seats/<int:showtime_id>')
def select_seats(showtime_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch total available seats for the specific showtime, excluding already booked seats
    cursor.execute('''
        SELECT COUNT(*) AS available_seats
        FROM Seat
        WHERE screen_number = (SELECT screen_number FROM Showtime WHERE showtime_id = ?)
        AND seat_id NOT IN (
            SELECT seat_id FROM BookingSeat WHERE booking_id IN (
                SELECT booking_id FROM Booking WHERE showtime_id = ?
            )
        )
    ''', (showtime_id, showtime_id))
    available_seats_row = cursor.fetchone()
    available_seats = available_seats_row["available_seats"] if available_seats_row else 0

    # Fetch screen capacity
    cursor.execute("SELECT capacity FROM Screen WHERE screen_number = (SELECT screen_number FROM Showtime WHERE showtime_id = ?)", (showtime_id,))
    capacity_row = cursor.fetchone()
    capacity = capacity_row["capacity"] if capacity_row else 0


    conn.close()
    return render_template('select_seat.html', showtime_id=showtime_id, screen_capacity=capacity, total_available_seats=available_seats)



@app.route('/confirm_seats', methods=['POST'])
def confirm_seats():
    showtime_id = request.form.get('showtime_id')
    num_seats = int(request.form.get('num_seats', 0))
    user_id = session.get('user_id')

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT seat_id FROM Seat
        WHERE screen_number = (SELECT screen_number FROM Showtime WHERE showtime_id = ?)
        AND seat_id NOT IN (
            SELECT seat_id FROM BookingSeat WHERE booking_id IN (
                SELECT booking_id FROM Booking WHERE showtime_id = ?
            )
        )
        LIMIT ?
    ''', (showtime_id, showtime_id, num_seats))
    available_seats = cursor.fetchall()

    if len(available_seats) < num_seats:
        conn.close()
        return "Not enough seats available", 400

    booking_date = datetime.now().strftime('%Y-%m-%d')
    cursor.execute("INSERT INTO Booking (user_id, showtime_id, booking_date) VALUES (?, ?, ?)", (user_id, showtime_id, booking_date))
    booking_id = cursor.lastrowid

    seat_ids = [seat['seat_id'] for seat in available_seats]
    cursor.executemany("INSERT INTO BookingSeat (booking_id, seat_id) VALUES (?, ?)", [(booking_id, seat_id) for seat_id in seat_ids])

    conn.commit()
    conn.close()

    return redirect(url_for('ticket', booking_id=booking_id))

# Route to show ticket confirmation after booking
@app.route('/ticket/<int:booking_id>')
def ticket(booking_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    booking_details = cursor.execute('''
        SELECT 
            B.booking_id,
            U.username AS user_name,
            M.name AS movie_name,
            M.poster_image AS movie_image,
            S.screen_number,
            ST.date AS show_date,
            ST.time AS show_time,
            GROUP_CONCAT(SE.seat_number, ', ') AS seat_numbers
        FROM 
            Booking B
        JOIN Showtime ST ON B.showtime_id = ST.showtime_id
        JOIN Movie M ON ST.movie_id = M.movie_id
        JOIN Screen S ON ST.screen_number = S.screen_number
        JOIN BookingSeat BS ON B.booking_id = BS.booking_id
        JOIN Seat SE ON BS.seat_id = SE.seat_id
        JOIN User U ON B.user_id = U.user_id
        WHERE B.booking_id = ?
        GROUP BY B.booking_id
    ''', (booking_id,)).fetchone()

    conn.close()
    return render_template('ticket.html', booking_details=booking_details)

    
    
if __name__ == '__main__':
    subprocess.run(["python", os.path.join(os.path.dirname(__file__), "initialize_db.py")])
    app.run(debug=True)
