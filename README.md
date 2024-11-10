
# Theater Management System

This project is a theater management web application that allows customers to book movie tickets and enables theater employees to manage movies and bookings.

## Project Structure

- **app.py**: Main Flask application file.
- **initialize_db.py**: Script to set up the SQLite database with necessary tables.
- **static/**: Contains JavaScript, CSS, and image assets.
- **templates/**: HTML templates for rendering pages.

## Features

### Customer

- Register and log in to the platform.
- Browse movies, view showtimes, and book tickets.
- View and manage bookings.

### Employee

- Log in to access management tools.
- Add new movies, update showtimes, and manage bookings.
- Access employee-specific pages for streamlined operations.

## Setup Instructions

### Requirements

- Python 3.x
- Flask
- SQLite3

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/122Ananya/dbms_theatre.git
   cd dbms_theatre
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:

   ```bash
   python app.py
   ```

4. Access the application at `http://localhost:5000`.

## Usage

1. **Register** as a new user (customer or employee).
2. **Log in** to access your dashboard.
3. **Browse** movies and **book tickets** as a customer.
4. **Add or manage movies** as an employee.

## Database Schema

- **User Table**: Stores user information with roles (`customer` or `employee`).
- **Movie Table**: Stores movie details like name, release date, language, and genre.
- **Screen Table**: Manages screens with their capacities.
- **Seat Table**: Tracks seats per screen, including type, price, and availability.
- **Showtime Table**: Links movies to screens with showtimes.
- **Booking Table**: Records bookings with associated users and showtimes.
- **BookingSeat Table**: Links bookings to individual seats for detailed seat selection.

## Contributing

Please follow the contributing guidelines when submitting pull requests.
