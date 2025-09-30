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
    
    def __str__(self):
        return f"{self.user} borrowed {self.book}"
    
    # def save(self, *args, **kwargs):
    #     if not self.pk:  # New borrow
    #         self.book.available_copies -= 1
    #         self.book.save()

    def save(self, *args, **kwargs):
        if not self.pk:  # New borrow
            self.book.available_copies -= 1
            self.book.save()
        
        super().save(*args, **kwargs)
        
        # Check for overdue and create fine if needed (after saving)
        if not self.is_returned and self.due_date < timezone.now().date():
            self.check_and_create_fine()

        else:
            # Check if this is an update and book was returned
            old_instance = Borrow.objects.get(pk=self.pk) if self.pk else None
            if old_instance and not old_instance.is_returned and self.is_returned:
                # Book is being returned, but don't delete fine - just handle in return logic
                pass
        
        super().save(*args, **kwargs)
        
        # Check for overdue and create fine if needed (after saving)
        if not self.is_returned and self.due_date < timezone.now().date():
            self.check_and_create_fine()
    
    def return_book(self):
        if not self.is_returned:
            self.is_returned = True
            self.return_date = timezone.now().date()
            self.book.available_copies += 1
            self.book.save()
            # Don't delete fine when book is returned - keep for record
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
    
    # def check_and_create_fine(self):
    #     """Check if book is overdue and create fine if needed"""
    #     if self.is_overdue and not hasattr(self, 'fine'):
    #         # Calculate fine amount - $50 fixed fine for overdue
    #         fine_amount = 50
            
    #         # Create fine only if it doesn't exist
    #         Fine.objects.get_or_create(
    #             borrow=self,
    #             defaults={
    #                 'user': self.user,
    #                 'amount': fine_amount,
    #                 'is_paid': False
    #             }
    #         )

    def check_and_create_fine(self):
        """Check if book is overdue and create fine if needed"""
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
                # Send notifications for newly created fine
                self.send_overdue_notifications(fine)

    def send_overdue_notifications(self, fine):
        """Send email and in-app notifications for overdue book and fine"""
        book = self.book
        borrower = self.user
        book_url = reverse('book-detail', kwargs={'pk': book.pk})
        absolute_book_url = f"http://{settings.DOMAIN}{book_url}"  # Adjust based on your domain
        
        # Notification message
        overdue_message = f"Your book '{book.title}' is overdue by {self.overdue_days} days. A fine of ${fine.amount} has been applied."
        fine_message = f"A fine of ${fine.amount} has been applied for overdue book '{book.title}'"
        
        # In-app notifications for both student/faculty AND staff
        notify(borrower, overdue_message, type='FINE', url=book_url)
        
        # Notify all staff (admin/librarian) about the overdue
        staff_users = User.objects.filter(role__in=[User.Role.ADMIN, User.Role.LIBRARIAN])
        for staff in staff_users:
            if staff != borrower:  # Don't notify staff if they are the borrower
                staff_message = f"Book '{book.title}' borrowed by {borrower.get_full_name()} is overdue by {self.overdue_days} days. Fine applied: ${fine.amount}"
                notify(staff, staff_message, type='FINE', url=book_url)
        
        # Email notification only for students/faculty
        if borrower.role in [User.Role.STUDENT, User.Role.FACULTY]:
            self.send_overdue_email(borrower, book, fine, absolute_book_url)

    def send_overdue_email(self, user, book, fine, book_url):
        """Send email notification for overdue book"""
        from django.core.mail import EmailMultiAlternatives
        from django.template.loader import render_to_string
        
        subject = f"Overdue Book: '{book.title}'"
        
        html_content = render_to_string('emails/overdue_book.html', {
            'user': user,
            'book': book,
            'borrow': self,
            'fine': fine,
            'due_date': self.due_date,
            'overdue_days': self.overdue_days,
            'book_url': book_url,
        })
        
        email = EmailMultiAlternatives(subject, '', to=[user.email])
        email.attach_alternative(html_content, "text/html")
        email.send()
class Fine(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fines')
    borrow = models.OneToOneField(Borrow, on_delete=models.CASCADE, related_name='fine')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    is_paid = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Fine of ${self.amount} for {self.borrow}"
    
    # def pay_fine(self):
    #     if not self.is_paid:
    #         self.is_paid = True
    #         self.paid_at = timezone.now()
    #         self.save()

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
    
    def __str__(self):
        return f"{self.user} reserved {self.book}"
    
    class Meta:
        ordering = ['reservation_date']