# Transactions App

The transactions app manages all library circulation operations including book borrowing, returns, fines, and reservations.

## Features

### Borrowing System
- Book borrowing with due date tracking
- Librarian-controlled book issuance
- Automatic book availability updates
- Borrow history tracking
- Overdue detection

### Fine Management
- Automatic fine calculation for overdue books
- Fixed fine amount ($50 per overdue book)
- Fine payment tracking
- Payment confirmation notifications
- Fine history and reporting

### Reservation System
- Book reservation for unavailable items
- Automatic status updates
- Notification when reserved books become available
- Reservation cancellation
- Reservation completion tracking

## Models

### Borrow
Tracks book borrowing transactions with the following fields:
- `user`: Foreign key to User (borrower)
- `book`: Foreign key to Book
- `issued_by`: Foreign key to User (librarian who issued)
- `issue_date`: Date when book was issued
- `due_date`: Date when book is due
- `return_date`: Date when book was returned
- `is_returned`: Return status flag
- `overdue_notification_sent`: Track if overdue notification was sent

### Fine
Tracks fines for overdue books:
- `user`: Foreign key to User (who owes the fine)
- `borrow`: One-to-one relationship with Borrow
- `amount`: Fine amount (decimal)
- `created_at`: Fine creation timestamp
- `paid_at`: Payment timestamp
- `is_paid`: Payment status flag

### Reservation
Manages book reservations:
- `user`: Foreign key to User (who reserved)
- `book`: Foreign key to Book
- `reservation_date`: Reservation timestamp
- `status`: Reservation status (PENDING, AVAILABLE, CANCELLED, COMPLETED)
- `notified_at`: When user was notified of availability
- `cancelled_at`: When reservation was cancelled

## Key Methods

### Borrow Methods
- `return_book()`: Process book return and update availability
- `is_overdue`: Property to check if book is overdue
- `overdue_days`: Property to calculate days overdue
- `has_unpaid_fine`: Property to check for unpaid fines
- `check_and_create_fine()`: Automatically create fine if overdue
- `send_overdue_notifications()`: Send notifications for overdue books
- `send_overdue_email()`: Send email notification

### Fine Methods
- `pay_fine()`: Process fine payment
- `send_payment_notification()`: Send payment confirmation

## Views

### Borrow Management Views
- `borrow_list`: List all borrows (with filtering)
- `borrow_create`: Create new borrow record (librarian only)
- `borrow_detail`: View borrow details
- `borrow_return`: Process book return (librarian only)
- `user_borrows`: View specific user's borrow history

### Fine Management Views
- `fine_list`: List all fines (with filtering)
- `fine_detail`: View fine details
- `fine_pay`: Process fine payment
- `user_fines`: View specific user's fines

### Reservation Management Views
- `reservation_list`: List all reservations
- `reservation_create`: Create new reservation
- `reservation_cancel`: Cancel reservation
- `user_reservations`: View user's reservations

## Forms

### Borrow Forms
- `BorrowForm`: Form for creating borrow records
- `BorrowFilterForm`: Form for filtering borrows

### Fine Forms
- `FinePaymentForm`: Form for processing fine payments

### Reservation Forms
- `ReservationForm`: Form for creating reservations

## URLs

```
/transactions/
    borrows/
        ''                    # Borrow list
        create/              # Create borrow (librarian)
        <int:pk>/            # Borrow detail
        <int:pk>/return/     # Return book (librarian)
        user/<int:user_id>/  # User's borrow history
    
    fines/
        ''                    # Fine list
        <int:pk>/            # Fine detail
        <int:pk>/pay/        # Pay fine
        user/<int:user_id>/  # User's fines
    
    reservations/
        ''                    # Reservation list
        create/              # Create reservation
        <int:pk>/cancel/     # Cancel reservation
        user/<int:user_id>/  # User's reservations
```

## Templates

- `transactions/borrow_list.html`: Borrow listing page
- `transactions/borrow_form.html`: Borrow creation form
- `transactions/borrow_detail.html`: Borrow details
- `transactions/fine_list.html`: Fine listing page
- `transactions/fine_detail.html`: Fine details
- `transactions/reservation_list.html`: Reservation listing
- `transactions/reservation_form.html`: Reservation creation form

## Fine System

### Automatic Fine Calculation
- Fine amount: $50 fixed per overdue book
- Automatic creation when book becomes overdue
- One fine per borrow record
- Fine created only once per overdue book

### Fine Payment Process
1. User views their fines
2. User initiates payment
3. System processes payment
4. Fine marked as paid with timestamp
5. Payment confirmation sent via notifications

### Overdue Notifications
- In-app notifications to borrower
- Email notifications to students/faculty
- Notifications to all staff (admin/librarian)
- Includes overdue days and fine amount

## Borrowing Workflow

### Book Issuance
1. Librarian selects user and book
2. System validates book availability
3. Due date is automatically calculated
4. Borrow record is created
5. Book availability is decreased
6. User and librarian are notified

### Book Return
1. Librarian processes return
2. System checks for overdue status
3. If overdue, fine is automatically created
4. Book availability is increased
5. Return date is recorded
6. User is notified of return confirmation

## Reservation Workflow

### Creating a Reservation
1. User requests reservation for unavailable book
2. System creates reservation with PENDING status
3. User receives confirmation

### Reservation Fulfillment
1. When book becomes available
2. System updates reservation to AVAILABLE
3. User is notified via email and in-app
4. User can borrow the book
5. Reservation marked as COMPLETED

### Cancellation
1. User or librarian can cancel reservation
2. Status updated to CANCELLED
3. Cancellation timestamp recorded
4. Other users can reserve the book

## Usage Examples

### Creating a Borrow Record
```python
from transactions.models import Borrow
from books.models import Book
from accounts.models import User
from django.utils import timezone
from datetime import timedelta

user = User.objects.get(username='student123')
book = Book.objects.get(isbn='9780743273565')
librarian = User.objects.get(username='librarian1')

borrow = Borrow.objects.create(
    user=user,
    book=book,
    issued_by=librarian,
    due_date=timezone.now().date() + timedelta(days=14)
)
```

### Processing a Return
```python
borrow = Borrow.objects.get(pk=1)
borrow.return_book()  # Handles availability and fine check
```

### Checking and Creating Fines
```python
borrow = Borrow.objects.get(pk=1)
if borrow.check_and_create_fine():
    print("Fine created for overdue book")
```

### Paying a Fine
```python
fine = Fine.objects.get(pk=1)
fine.pay_fine()  # Marks as paid and sends notification
```

### Creating a Reservation
```python
from transactions.models import Reservation

reservation = Reservation.objects.create(
    user=user,
    book=book,
    status='PENDING'
)
```

## Management Commands

The app includes custom management commands for:
- Checking overdue books and creating fines
- Updating reservation statuses
- Sending daily overdue notifications
- Generating circulation reports

## Integration with Other Apps

- **Accounts**: User relationships for borrows, fines, and reservations
- **Books**: Book relationships and availability updates
- **Notifications**: Automatic notifications for all transaction events
- **Dashboard**: Statistics and reporting on circulation data

## Security and Permissions

- Borrow creation restricted to librarians
- Fine payment can be done by users or librarians
- Reservations can be created by users
- Cancellation permissions vary by role
- Fine creation is automatic and system-controlled

## Future Enhancements

- Configurable fine amounts based on book category
- Fine payment integration with payment gateways
- Renewal system for borrowed books
- Hold queue system for popular books
- Advanced circulation reports
- Barcode scanning integration
- Email reminder system before due dates
- Fine waiver system for special circumstances
- Borrowing limit enforcement per user role