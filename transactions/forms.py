from django import forms
from django.utils import timezone
from datetime import timedelta
from .models import Borrow, Fine, Reservation
from books.models import Book
from accounts.models import User

class BorrowForm(forms.ModelForm):
    class Meta:
        model = Borrow
        fields = ['user', 'book', 'due_date']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        # Limit options for user and book
        self.fields['user'].queryset = User.objects.filter(role__in=[User.Role.STUDENT, User.Role.FACULTY])
        self.fields['book'].queryset = Book.objects.filter(available_copies__gt=0)

        if self.request:
            user = self.request.user
            if user.role in [User.Role.STUDENT, User.Role.FACULTY]:
                # Make fields read-only (disabled)
                self.fields['user'].disabled = True
                self.fields['book'].disabled = True
                self.fields['due_date'].disabled = True

                # Set due date to 7 days from today
                self.initial['due_date'] = timezone.now().date() + timedelta(days=7)

class ReturnForm(forms.ModelForm):
    class Meta:
        model = Borrow
        fields = []  # No fields needed for simple return
        
    def clean(self):
        cleaned_data = super().clean()
        if self.instance.is_returned:
            raise forms.ValidationError("This book has already been returned")
        return cleaned_data

class FinePaymentForm(forms.ModelForm):
    class Meta:
        model = Fine
        fields = []  # No fields needed, just marking as paid
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make the form read-only for display purposes
        for field in self.fields:
            self.fields[field].disabled = True


class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ['user', 'book']

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        # Limit the queryset
        self.fields['user'].queryset = User.objects.filter(role__in=[User.Role.STUDENT, User.Role.FACULTY])
        self.fields['book'].queryset = Book.objects.filter(available_copies=0)

        if self.request:
            user = self.request.user
            if user.role in [User.Role.STUDENT, User.Role.FACULTY]:
                self.fields['user'].initial = user
                self.fields['user'].disabled = True

                book_id = self.request.resolver_match.kwargs.get('pk')
                if book_id:
                    self.fields['book'].initial = Book.objects.filter(pk=book_id).first()
                    self.fields['book'].disabled = True
