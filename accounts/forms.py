from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()
    
    class Meta:
        model = User
        fields = ['username', 'university_id', 'email', 'first_name', 'last_name', 
                  'role', 'phone', 'address', 'password1', 'password2', 'profile_picture']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].widget.attrs.update({'class': 'form-select'})
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email address is already in use.")
        return email
class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'address', 'profile_picture', 'university_id', 'role']  # Removed 'role'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['profile_picture'].widget.attrs.update({'class': 'form-control'})
