from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from accounts.models import User
from books.models import Book

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
    
    def save(self, *args, **kwargs):
        if not self.pk:  # New borrow
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