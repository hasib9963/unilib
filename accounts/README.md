# Accounts App

The accounts app handles user authentication, registration, and profile management for the UniLib library management system.

## Features

### User Authentication
- Custom user model extending Django's AbstractUser
- Email and username-based login authentication
- Password reset functionality
- Session management

### User Roles
The system supports four user roles:
- **ADMIN**: Full system access and configuration
- **LIBRARIAN**: Book management and circulation operations
- **STUDENT**: Standard borrowing privileges
- **FACULTY**: Extended borrowing privileges

### User Profile
- University ID (unique identifier)
- Email address (unique)
- Phone number
- Address
- Profile picture upload
- Borrowing statistics

## Models

### User
Custom user model with the following fields:
- `username`: Django default username
- `email`: Unique email address
- `role`: User role (ADMIN, LIBRARIAN, STUDENT, FACULTY)
- `university_id`: Unique university identifier
- `phone`: Contact phone number
- `address`: Physical address
- `profile_picture`: User avatar image

### Key Methods
- `is_admin()`: Check if user is admin
- `is_librarian()`: Check if user is librarian
- `is_student()`: Check if user is student
- `is_faculty()`: Check if user is faculty
- `get_total_borrows()`: Get total number of borrows
- `get_active_borrows()`: Get currently borrowed books count
- `get_overdue_borrows()`: Get overdue books count

## Views

### Authentication Views
- `register`: User registration (restricted to STUDENT and FACULTY roles)
- `login`: User login with email or username
- `logout`: User logout
- `profile`: User profile view and editing

### Password Management
- `password_reset`: Initiate password reset
- `password_reset_done`: Confirmation after reset request
- `password_reset_confirm`: Confirm password reset with token
- `password_reset_complete`: Success message after reset

## Forms

### User Forms
- `UserRegistrationForm`: Registration form with role selection
- `UserUpdateForm`: Profile update form
- `ProfileUpdateForm`: Additional profile information

## Authentication Backend

### EmailOrUsernameModelBackend
Custom authentication backend that allows users to login with either:
- Email address
- Username

This provides flexibility for users who may not remember their username.

## URLs

```
/accounts/
    register/          # User registration
    login/             # User login
    logout/            # User logout
    profile/           # User profile
    password_reset/    # Password reset flow
```

## Templates

- `accounts/register.html`: Registration page
- `accounts/login.html`: Login page
- `accounts/profile.html`: User profile page
- `accounts/password_reset.html`: Password reset form
- `accounts/password_reset_email.html`: Password reset email template

## Security Features

- Password validation using Django's built-in validators
- Email verification (can be extended)
- University ID uniqueness validation
- Role-based access control
- Session security middleware

## Registration Restrictions

New user registrations are restricted to:
- STUDENT role
- FACULTY role

ADMIN and LIBRARIAN roles can only be created by existing admins through the Django admin panel or management commands.

## Usage Examples

### Creating a New User
```python
from accounts.models import User

# Create a student user
student = User.objects.create_user(
    username='student123',
    email='student@university.edu',
    password='securepassword',
    university_id='STU001',
    role=User.Role.STUDENT
)
```

### Checking User Role
```python
if user.is_student():
    # Grant student privileges
    pass
elif user.is_librarian():
    # Grant librarian privileges
    pass
```

### Getting User Statistics
```python
total_borrows = user.get_total_borrows()
active_borrows = user.get_active_borrows()
overdue_borrows = user.get_overdue_borrows()
```

## Integration with Other Apps

- **Transactions**: User borrows and fines are tracked through related models
- **Books**: User borrowing history is linked to book models
- **Notifications**: Users receive notifications about their account activities
- **Dashboard**: User-specific dashboards based on role

## Future Enhancements

- Email verification for registration
- Two-factor authentication
- Social login integration
- User activity logging
- Bulk user import functionality
- Advanced user search and filtering