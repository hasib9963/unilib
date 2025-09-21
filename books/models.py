# books/models.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.urls import reverse_lazy

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name

class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=100)
    isbn = models.CharField('ISBN', max_length=13, unique=True)
    publisher = models.CharField(max_length=100, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    publication_date = models.DateField(null=True, blank=True)
    total_copies = models.PositiveIntegerField(default=1)
    available_copies = models.PositiveIntegerField(default=1)
    cover_image = models.ImageField(upload_to='book_covers/', blank=True, null=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} by {self.author}"

    def is_borrowed_by_user(self, user):
        """Check if this book is currently borrowed by the given user"""
        if not user.is_authenticated:
            return False
        return self.borrows.filter(user=user, is_returned=False).exists()
        
    def save(self, *args, **kwargs):
        if not self.pk:  # Only when creating a new book
            self.available_copies = self.total_copies
        elif self.available_copies > self.total_copies:
            self.available_copies = self.total_copies
        super().save(*args, **kwargs)
  
    class Meta:
        ordering = ['title']