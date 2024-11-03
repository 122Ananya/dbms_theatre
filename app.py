import sqlite3
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('tickets.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            movie TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Route to display the booking form
@app.route('/book_ticket', methods=['GET', 'POST'])
def book_ticket():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        movie = request.form['movie']

        # Insert booking data into the database
        conn = sqlite3.connect('tickets.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO tickets (name, email, movie) VALUES (?, ?, ?)", (name, email, movie))
        conn.commit()
        conn.close()

        return redirect(url_for('success'))

    return render_template('book_ticket.html')

# Success page after booking
@app.route('/success')
def success():
    return "<h1>Booking Successful!</h1><p>Your ticket has been booked successfully.</p>"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/movie_display')
def movie_disp():
    return render_template('movie_display.html')

# @app.route('/book_ticket')
# def book_ticket():
#     return render_template('book_ticket.html')

if __name__ == '__main__':
    app.run(debug=True, port=5001)
