# Dashboard App

The dashboard app provides role-based dashboards and analytics for different user types in the UniLib library management system.

## Features

### Role-Based Dashboards
- **Admin Dashboard**: System-wide statistics and management
- **Librarian Dashboard**: Circulation operations and user management
- **Student Dashboard**: Personal borrowing history and account info
- **Faculty Dashboard**: Enhanced borrowing privileges and history

### Statistics and Analytics
- Total books and categories
- Active borrows and returns
- Overdue books tracking
- Fine collection statistics
- User activity metrics
- Popular books analysis

### Reporting
- PDF report generation
- Export functionality
- Custom date range filtering
- Summary statistics

### Template Tags
- Custom template tags for dashboard data display
- Role-based content rendering
- Statistics calculation helpers

## Views

### Dashboard Views
- `dashboard`: Main dashboard view (routes based on user role)
- `admin_dashboard`: Admin-specific dashboard
- `librarian_dashboard`: Librarian-specific dashboard
- `student_dashboard`: Student-specific dashboard
- `faculty_dashboard`: Faculty-specific dashboard

### Report Views
- `export_report`: Generate and export PDF reports
- `statistics_view`: Detailed statistics view

## URL Patterns

```
/dashboard/
    ''                    # Main dashboard (role-based)
    admin/               # Admin dashboard
    librarian/           # Librarian dashboard
    student/             # Student dashboard
    faculty/             # Faculty dashboard
    export/              # Export reports as PDF
```

## Templates

- `dashboard/admin_dashboard.html`: Admin dashboard template
- `dashboard/librarian_dashboard.html`: Librarian dashboard template
- `dashboard/student_dashboard.html`: Student dashboard template
- `dashboard/faculty_dashboard.html`: Faculty dashboard template
- `dashboard/dashboard.html`: Generic dashboard template

## Dashboard Components

### Admin Dashboard Features
- Total users count by role
- Total books and categories
- Total borrows and active borrows
- Overdue books count
- Total fines collected
- Recent activity log
- System health indicators
- Quick action links

### Librarian Dashboard Features
- Today's issued books
- Today's returned books
- Current overdue books
- Pending reservations
- Unpaid fines
- Popular books
- Recent borrows list
- Quick action buttons

### Student/Faculty Dashboard Features
- Current borrowed books
- Borrowing history
- Overdue books
- Unpaid fines
- Active reservations
- Account statistics
- Quick links to search and profile

## Template Tags

### Custom Template Tags
Located in `dashboard/templatetags/`:
- `dashboard_extras`: Custom filters and tags for dashboard data

### Available Tags/Filters
- Statistics calculation helpers
- Role-based content display
- Date formatting utilities
- Number formatting for statistics

## Statistics Calculation

### Key Metrics
- **Total Books**: Count of all books in catalog
- **Total Categories**: Count of book categories
- **Total Users**: Count of registered users
- **Active Borrows**: Currently borrowed books
- **Overdue Books**: Books past due date
- **Total Fines**: Sum of all fines
- **Collected Fines**: Sum of paid fines
- **Pending Reservations**: Active reservations

### Data Sources
Statistics are calculated from:
- `books.models.Book` for book statistics
- `accounts.models.User` for user statistics
- `transactions.models.Borrow` for circulation data
- `transactions.models.Fine` for financial data
- `transactions.models.Reservation` for reservation data

## PDF Report Generation

### Report Types
- **Circulation Report**: Borrowing and return statistics
- **Fine Report**: Fine collection and payment data
- **User Activity Report**: User engagement metrics
- **Book Inventory Report**: Book catalog statistics

### Export Features
- Date range filtering
- Role-based report access
- PDF format with professional styling
- Download capability
- Email report option (can be extended)

## Usage Examples

### Accessing Dashboard
```python
# In views, redirect to appropriate dashboard
from django.shortcuts import redirect

def dashboard_view(request):
    if request.user.is_admin():
        return redirect('admin_dashboard')
    elif request.user.is_librarian():
        return redirect('librarian_dashboard')
    elif request.user.is_student():
        return redirect('student_dashboard')
    elif request.user.is_faculty():
        return redirect('faculty_dashboard')
```

### Calculating Statistics
```python
from books.models import Book
from transactions.models import Borrow, Fine

# Total books
total_books = Book.objects.count()

# Active borrows
active_borrows = Borrow.objects.filter(is_returned=False).count()

# Total fines collected
collected_fines = Fine.objects.filter(is_paid=True).aggregate(
    total=models.Sum('amount')
)['total'] or 0
```

### Generating Reports
```python
from django.http import HttpResponse
from utils.pdf_generator import generate_dashboard_report

def export_report(request):
    report_type = request.GET.get('type', 'circulation')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    pdf = generate_dashboard_report(
        report_type=report_type,
        start_date=start_date,
        end_date=end_date
    )
    
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="report.pdf"'
    return response
```

## Integration with Other Apps

- **Accounts**: User role determination and user statistics
- **Books**: Book inventory statistics
- **Transactions**: Circulation data, fines, and reservations
- **Utils**: PDF generation functionality
- **Notifications**: Dashboard notification display

## Security and Permissions

- Dashboard access restricted to authenticated users
- Role-based dashboard routing
- Sensitive statistics restricted to appropriate roles
- Report export permissions based on user role

## Performance Considerations

- Statistics calculated on-the-fly (can be cached)
- Database queries optimized with select_related/prefetch_related
- Pagination for large data sets
- Lazy loading for heavy computations

## Future Enhancements

- Real-time dashboard updates with WebSockets
- Interactive charts and graphs
- Customizable dashboard layouts
- Scheduled report generation
- Email report delivery
- Advanced filtering and search
- Data export in multiple formats (Excel, CSV)
- Performance metrics and monitoring
- Predictive analytics for book demand
- Comparison reports (period-over-period)