# UniLib - Library Management System

A comprehensive Django-based library management system designed for universities to manage books, users, borrowing transactions, and library operations efficiently.

## Features

### User Management
- Multi-role authentication system (Admin, Librarian, Student, Faculty)
- User registration with university ID validation
- Profile management with custom avatars
- Email/username login authentication

### Book Management
- Complete book catalog with categories
- ISBN-based book identification
- Cover image support
- Book availability tracking
- Search and filtering capabilities

### Borrowing System
- Book borrowing and return management
- Due date tracking
- Automatic fine calculation for overdue books
- Borrow history for each user
- Book reservation system

### Notifications
- In-app notification system
- Email notifications for overdue books
- Payment confirmation notifications
- Real-time notification counter

### Dashboard
- Role-based dashboards for different user types
- Statistics and analytics
- Fine management interface
- Export reports as PDF

### Additional Features
- PDF report generation
- Responsive design with Bootstrap 5
- Email integration for notifications
- Static file optimization with WhiteNoise

## Technology Stack

- **Backend**: Django 5.2.4
- **Frontend**: Bootstrap 5, Django Templates
- **Database**: SQLite (default)
- **Email**: SMTP (Gmail)
- **Static Files**: WhiteNoise
- **Forms**: Django Crispy Forms
- **Tables**: Django Tables2
- **PDF Generation**: ReportLab, WeasyPrint

## Installation

### Prerequisites
- Python 3.8+
- pip
- Virtual environment (recommended)

### Setup Steps

1. Clone the repository:
```bash
git clone <repository-url>
cd unilib
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the project root:
```
SECRET_KEY=your-secret-key-here
DEBUG=True
EMAIL=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
```

5. Run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

6. Create a superuser:
```bash
python manage.py createsuperuser
```

7. Run the development server:
```bash
python manage.py runserver
```

8. Access the application:
- Main application: http://127.0.0.1:8000/
- Admin panel: http://127.0.0.1:8000/admin/

## Project Structure

```
unilib/
├── accounts/          # User authentication and management
├── books/            # Book and category management
├── transactions/     # Borrowing, fines, and reservations
├── dashboard/        # Dashboard views and analytics
├── notifications/    # Notification system
├── home/             # Home page
├── utils/            # Utility functions (PDF generation)
├── management/       # Django management commands
├── static/           # Static files (CSS, JS, images)
├── templates/        # HTML templates
├── media/            # User-uploaded media files
└── UniLib/           # Project settings and configuration
```

## User Roles

### Admin
- Full system access
- User management
- System configuration
- View all reports

### Librarian
- Book management
- Issue and return books
- Manage fines
- View borrowing history

### Student
- Browse and search books
- Borrow books
- View borrowing history
- Pay fines
- Reserve books

### Faculty
- All student privileges
- Extended borrowing periods (if configured)

## Key Features Explained

### Borrowing Process
1. User searches for available books
2. Librarian issues the book
3. Due date is automatically set
4. User returns the book by the due date
5. If overdue, automatic fine is generated ($50 fixed)

### Fine System
- Fixed fine amount: $50 per overdue book
- Automatic fine calculation
- Email notifications for overdue books
- Fine payment tracking
- Payment confirmation notifications

### Reservation System
- Users can reserve books that are currently unavailable
- Automatic notification when book becomes available
- Reservation status tracking (Pending, Available, Cancelled, Completed)

### Notifications
- Real-time in-app notifications
- Email notifications for important events
- Notification counter in navigation
- Notification history

## Development

### Running Tests
```bash
python manage.py test
```

### Creating Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Collecting Static Files
```bash
python manage.py collectstatic
```

## Deployment

For production deployment:

1. Set `DEBUG=False` in `.env`
2. Configure `ALLOWED_HOSTS` in settings
3. Use a production database (PostgreSQL recommended)
4. Set up proper email backend
5. Configure static file serving
6. Use a production WSGI server (Gunicorn)
7. Set up a web server (Nginx)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions, please create an issue in the repository or contact the development team.

## Recent Updates

- Added PDF export functionality for dashboard reports
- Implemented pagination for fine list
- Fixed return button restrictions for students and faculty
- Added email subject customization
- Improved user registration flow (admin/librarian roles restricted)
- Enhanced notification system