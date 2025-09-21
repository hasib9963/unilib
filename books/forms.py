from django import forms
from .models import Book, Category

class BookForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.is_create = kwargs.pop('is_create', False)
        super().__init__(*args, **kwargs)
        
        # For creation, exclude available_copies field as it's set automatically by the model
        if self.is_create:
            self.fields.pop('available_copies', None)
    class Meta:
        model = Book
        fields = ['title', 'author', 'isbn', 'publisher', 'category', 
                  'publication_date', 'total_copies', 'available_copies', 'cover_image', 'description']
        widgets = {
            'publication_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Only validate available_copies if it exists in the form (for updates)
        if 'available_copies' in cleaned_data and 'total_copies' in cleaned_data:
            available_copies = cleaned_data.get('available_copies')
            total_copies = cleaned_data.get('total_copies')
            
            if available_copies > total_copies:
                self.add_error('available_copies', "Available copies cannot exceed total copies.")
        
        return cleaned_data
class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class BookSearchForm(forms.Form):
    query = forms.CharField(label='Search', max_length=100, required=False)
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(), 
        required=False,
        empty_label="All Categories"
    )