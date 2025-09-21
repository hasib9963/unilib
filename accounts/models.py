from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

class User(AbstractUser):
    email = models.EmailField(unique=True)
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', _('Admin')
        LIBRARIAN = 'LIBRARIAN', _('Librarian')
        STUDENT = 'STUDENT', _('Student')
        FACULTY = 'FACULTY', _('Faculty')
    
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.STUDENT)
    university_id = models.CharField(max_length=20, unique=True)
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)

    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.university_id})"
    
    def is_admin(self):
        return self.role == self.Role.ADMIN
    
    def is_librarian(self):
        return self.role == self.Role.LIBRARIAN
    
    def is_student(self):
        return self.role == self.Role.STUDENT
    
    def is_faculty(self):
        return self.role == self.Role.FACULTY
    

    def get_profile_picture(self):
        if self.profile_picture and hasattr(self.profile_picture, 'url'):
            return self.profile_picture.url
        return '/static/images/default_profile.png'
    
    
    def get_total_borrows(self):
        return self.borrows.count()
    
    def get_active_borrows(self):
        return self.borrows.filter(is_returned=False).count()
    
    def get_overdue_borrows(self):
        return self.borrows.filter(
            is_returned=False,
            due_date__lt=timezone.now().date()
        ).count()
    