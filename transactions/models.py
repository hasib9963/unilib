from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from accounts.models import User
from books.models import Book
from notifications.utils import notify
from django.urls import reverse
from django.conf import settings
class Borrow(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='borrows')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='borrows')
    issued_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='issued_borrows')
    issue_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)
    is_returned = models.BooleanField(default=False)
    overdue_notification_sent = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user} borrowed {self.book}"

    def save(self, *args, **kwargs):
        is_new = not self.pk
        
        # Handle book copy count for new borrows
        if is_new:
            self.book.available_copies -= 1
            self.book.save()
        
        super().save(*args, **kwargs)

    def return_book(self):
        if not self.is_returned:
            self.is_returned = True
            self.return_date = timezone.now().date()
            self.book.available_copies += 1
            self.book.save()
            self.save()
    
    @property
    def is_overdue(self):
        return not self.is_returned and timezone.now().date() > self.due_date
    
    @property
    def overdue_days(self):
        if self.is_overdue:
            return (timezone.now().date() - self.due_date).days
        return 0
    
    @property
    def has_unpaid_fine(self):
        """Check if there's an unpaid fine associated with this borrow"""
        return hasattr(self, 'fine') and not self.fine.is_paid

    def check_and_create_fine(self, request=None):
        """Check if book is overdue and create fine if needed"""
        print(f"Checking fine for borrow: {self}, overdue: {self.is_overdue}, has_fine: {hasattr(self, 'fine')}")
        
        if self.is_overdue and not hasattr(self, 'fine'):
            # Calculate fine amount - $50 fixed fine for overdue
            fine_amount = 50
            
            # Create fine only if it doesn't exist
            fine, created = Fine.objects.get_or_create(
                borrow=self,
                defaults={
                    'user': self.user,
                    'amount': fine_amount,
                    'is_paid': False
                }
            )
            
            if created:
                print(f"Fine created for {self}")
                # Send notifications for newly created fine
                self.send_overdue_notifications(fine, request)
                return True
        return False

    def send_overdue_notifications(self, fine, request=None):
        """Send email and in-app notifications for overdue book and fine"""
        from django.contrib.sites.shortcuts import get_current_site
        
        book = self.book
        borrower = self.user
        
        print(f"Sending overdue notifications for: {book.title} to {borrower.email}")
        
        try:
            book_url = reverse('book-detail', kwargs={'pk': book.pk})
            
            # Get domain properly
            if request:
                current_site = get_current_site(request)
                domain = current_site.domain
            else:
                # Fallback to settings
                domain = getattr(settings, 'DOMAIN', '127.0.0.1:8000')
            
            absolute_book_url = f"http://{domain}{book_url}"
            
            # Notification message
            overdue_message = f"Your book '{book.title}' is overdue by {self.overdue_days} days. A fine of ${fine.amount} has been applied."
            
            # In-app notifications for both student/faculty AND staff
            notify(borrower, overdue_message, type='FINE', url=book_url)
            print(f"In-app notification sent to {borrower.email}")
            
            # Notify all staff (admin/librarian) about the overdue
            staff_users = User.objects.filter(role__in=[User.Role.ADMIN, User.Role.LIBRARIAN])
            for staff in staff_users:
                if staff != borrower:
                    staff_message = f"Book '{book.title}' borrowed by {borrower.get_full_name()} is overdue by {self.overdue_days} days. Fine applied: ${fine.amount}"
                    notify(staff, staff_message, type='FINE', url=book_url)
            
            # Email notification only for students/faculty
            if borrower.role in [User.Role.STUDENT, User.Role.FACULTY]:
                self.send_overdue_email(borrower, book, fine, absolute_book_url)
                
        except Exception as e:
            print(f"Error sending notifications: {e}")

    def send_overdue_email(self, user, book, fine, book_url):
        """Send email notification for overdue book"""
        from django.core.mail import EmailMultiAlternatives
        from django.template.loader import render_to_string
        
        subject = f"UniLib - Overdue Book: '{book.title}'"
        
        # Simple text content
        text_content = f"""
        Dear {user.get_full_name()},

        Overdue Book Notice

        Book Title: {book.title}
        Author: {book.author}
        Due Date: {self.due_date}
        Days Overdue: {self.overdue_days}
        Fine Amount: ${fine.amount}

        Please return this book to the library as soon as possible to avoid additional charges.

        You can view the book details here: {book_url}

        Thank you,
        UniLib Team
        """
        
        try:
            # Try to render HTML template
            html_content = render_to_string('emails/overdue_book.html', {
                'user': user,
                'book': book,
                'borrow': self,
                'fine': fine,
                'due_date': self.due_date,
                'overdue_days': self.overdue_days,
                'book_url': book_url,
            })
        except Exception as e:
            print(f"Error rendering email template: {e}")
            html_content = None
        
        try:
            email = EmailMultiAlternatives(
                subject, 
                text_content, 
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email]
            )
            
            if html_content:
                email.attach_alternative(html_content, "text/html")
            
            email.send()
            print(f"✓ Email sent successfully to {user.email}")
            
        except Exception as e:
            print(f"✗ Failed to send email to {user.email}: {e}")
            
class Fine(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fines')
    borrow = models.OneToOneField(Borrow, on_delete=models.CASCADE, related_name='fine')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    is_paid = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Fine of ${self.amount} for {self.borrow}"
    

    def pay_fine(self):
        if not self.is_paid:
            self.is_paid = True
            self.paid_at = timezone.now()
            self.save()
            
            # Send payment confirmation notification
            self.send_payment_notification()

    def send_payment_notification(self):
        """Send notification when fine is paid"""
        book = self.borrow.book
        book_url = reverse('book-detail', kwargs={'pk': book.pk})
        
        # Notify the user who paid
        user_message = f"Your fine of ${self.amount} for '{book.title}' has been paid successfully."
        notify(self.user, user_message, type='FINE', url=book_url)
        
        # Notify staff about the payment
        staff_users = User.objects.filter(role__in=[User.Role.ADMIN, User.Role.LIBRARIAN])
        for staff in staff_users:
            if staff != self.user:
                staff_message = f"Fine of ${self.amount} for '{book.title}' has been paid by {self.user.get_full_name()}."
                notify(staff, staff_message, type='FINE', url=book_url)

class Reservation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reservations')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reservations')
    reservation_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('PENDING', 'Pending'),
        ('AVAILABLE', 'Available'),
        ('CANCELLED', 'Cancelled'),
        ('COMPLETED', 'Completed'),
    ], default='PENDING')
    notified_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user} reserved {self.book}"
    
    class Meta:
        ordering = ['reservation_date']