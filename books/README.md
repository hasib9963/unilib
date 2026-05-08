# Books App

The books app manages the library's book catalog, including book information, categories, and availability tracking.

## Features

### Book Management
- Complete book catalog with detailed information
- ISBN-based unique identification
- Category organization
- Cover image support
- Publication details tracking
- Availability tracking (total vs. available copies)

### Category System
- Hierarchical category organization
- Category descriptions
- Book categorization for easy browsing

### Search and Filtering
- Title search
- Author search
- Category filtering
- Availability filtering
- Advanced filtering with django-filter

## Models

### Book
Main book model with the following fields:
- `title`: Book title
- `author`: Book author
- `isbn`: Unique ISBN (13 characters)
- `publisher`: Publisher name
- `category`: Foreign key to Category
- `publication_date`: Date of publication
- `total_copies`: Total number of copies
- `available_copies`: Number of available copies
- `cover_image`: Book cover image
- `description`: Book description
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

### Category
Category model for organizing books:
- `name`: Category name (unique)
- `description`: Category description

### Key Methods

#### Book Methods
- `is_borrowed_by_user(user)`: Check if book is currently borrowed by a specific user
- `save()`: Custom save method to manage available copies

## Views

### Book Management Views
- `book_list`: List all books with filtering and pagination
- `book_detail`: Detailed view of a single book
- `book_create`: Create new book (librarian/admin only)
- `book_update`: Update book information (librarian/admin only)
- `book_delete`: Delete a book (librarian/admin only)

### Category Management Views
- `category_list`: List all categories
- `category_create`: Create new category (librarian/admin only)
- `category_update`: Update category (librarian/admin only)
- `category_delete`: Delete category (librarian/admin only)

## Forms

### Book Forms
- `BookForm`: Form for creating and updating books
- `BookFilterForm`: Form for filtering books

### Category Forms
- `CategoryForm`: Form for creating and updating categories

## Filters

### BookFilter
Django-filter configuration for advanced book filtering:
- Search by title
- Search by author
- Filter by category
- Filter by availability

## URLs

```
/books/
    ''                    # Book list
    <int:pk>/            # Book detail
    create/              # Create book (librarian/admin)
    <int:pk>/update/     # Update book (librarian/admin)
    <int:pk>/delete/     # Delete book (librarian/admin)
    
/categories/
    ''                    # Category list
    create/              # Create category (librarian/admin)
    <int:pk>/update/     # Update category (librarian/admin)
    <int:pk>/delete/     # Delete category (librarian/admin)
```

## Templates

- `books/book_list.html`: Book listing page
- `books/book_detail.html`: Book detail page
- `books/book_form.html`: Book create/update form
- `books/book_confirm_delete.html`: Book deletion confirmation
- `books/category_list.html`: Category listing
- `books/category_form.html`: Category create/update form

## Availability Management

### Automatic Copy Management
- When a new book is created, `available_copies` is set to `total_copies`
- When a book is borrowed, `available_copies` decreases
- When a book is returned, `available_copies` increases
- Validation ensures `available_copies` never exceeds `total_copies`

### Book Borrowing Status
The `is_borrowed_by_user()` method checks if a specific user currently has the book borrowed:
```python
if book.is_borrowed_by_user(request.user):
    # User already has this book borrowed
    pass
```

## Usage Examples

### Creating a New Book
```python
from books.models import Book, Category

# Get or create a category
category, created = Category.objects.get_or_create(
    name='Fiction',
    defaults={'description': 'Fictional literature'}
)

# Create a new book
book = Book.objects.create(
    title='The Great Gatsby',
    author='F. Scott Fitzgerald',
    isbn='9780743273565',
    publisher='Scribner',
    category=category,
    publication_date='1925-04-10',
    total_copies=5,
    description='A classic American novel'
)
```

### Searching for Books
```python
# Search by title
books = Book.objects.filter(title__icontains='gatsby')

# Search by author
books = Book.objects.filter(author__icontains='fitzgerald')

# Filter by category
books = Book.objects.filter(category__name='Fiction')

# Get available books
available_books = Book.objects.filter(available_copies__gt=0)
```

### Updating Book Availability
```python
# Decrease available copies (when borrowed)
book.available_copies -= 1
book.save()

# Increase available copies (when returned)
book.available_copies += 1
book.save()
```

## Integration with Other Apps

- **Transactions**: Books are linked to borrow records and reservations
- **Accounts**: User borrowing history is tracked through book relationships
- **Dashboard**: Book statistics and availability reports
- **Notifications**: Book availability notifications for reservations

## Admin Configuration

The app includes Django admin configuration for:
- Book management (inline editing)
- Category management
- Search fields (title, author, ISBN)
- List filtering (category, availability)
- Custom display fields

## Security and Permissions

- Book creation, update, and deletion restricted to librarians and admins
- All users can view books
- Availability tracking prevents over-borrowing
- ISBN uniqueness enforced

## Future Enhancements

- Book rating and review system
- Book recommendation engine
- Advanced search with full-text search
- Book series management
- Multiple authors per book
- Book tags and keywords
- Import/export book data (CSV, Excel)
- Barcode/QR code generation for books
- Book location tracking (shelf, floor, section)