import sqlite3
import os

DB_PATH = "theatre_management.db"
# Connect to the SQLite3 database (this will create the file if it doesn't exist)
db = sqlite3.connect(DB_PATH)

# Create tables
cursor = db.cursor()

# User table with customer
cursor.execute('''
CREATE TABLE IF NOT EXISTS User (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    password TEXT NOT NULL,
    past_movie TEXT
)
''')

# Movie table
cursor.execute('''
CREATE TABLE IF NOT EXISTS Movie (
    movie_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    release_date DATE,
    language TEXT,
    genre TEXT,
    rating REAL,
    poster_image BLOB,
    description TEXT,
    duration TEXT
)
''')

# Screen table
cursor.execute('''
CREATE TABLE IF NOT EXISTS Screen (
    screen_number INTEGER PRIMARY KEY,
    capacity INTEGER
)
''')

# Seat table
cursor.execute('''
CREATE TABLE IF NOT EXISTS Seat (
    seat_id INTEGER PRIMARY KEY,
    screen_number INTEGER,
    seat_type TEXT CHECK(seat_type IN ('premier', 'normal')) NOT NULL,
    seat_price REAL NOT NULL,
    seat_number TEXT,
    is_booked BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (screen_number) REFERENCES Screen(screen_number),
    CHECK (
        (screen_number = 1 AND seat_id BETWEEN 100 AND 199) OR
        (screen_number = 2 AND seat_id BETWEEN 200 AND 299) OR
        (screen_number = 3 AND seat_id BETWEEN 300 AND 399)
    )
)
''')

# Showtime table
cursor.execute('''
CREATE TABLE IF NOT EXISTS Showtime (
    showtime_id INTEGER PRIMARY KEY AUTOINCREMENT,
    screen_number INTEGER,
    movie_id INTEGER,
    date DATE,
    time TIME,
    FOREIGN KEY (screen_number) REFERENCES Screen(screen_number),
    FOREIGN KEY (movie_id) REFERENCES Movie(movie_id)
)
''')

# Booking table
cursor.execute('''
CREATE TABLE IF NOT EXISTS Booking (
    booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    showtime_id INTEGER,
    booking_date DATE,
    FOREIGN KEY (user_id) REFERENCES User(user_id),
    FOREIGN KEY (showtime_id) REFERENCES Showtime(showtime_id)
)
''')

# BookingSeat table
cursor.execute('''
CREATE TABLE IF NOT EXISTS BookingSeat (
    booking_id INTEGER,
    seat_id INTEGER,
    PRIMARY KEY (booking_id, seat_id),
    FOREIGN KEY (booking_id) REFERENCES Booking(booking_id) ON DELETE CASCADE,
    FOREIGN KEY (seat_id) REFERENCES Seat(seat_id) ON DELETE CASCADE
)
''')

# Commit changes and close connection
db.commit()
db.close()

print("Database and tables created successfully.")
