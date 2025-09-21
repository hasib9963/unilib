from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db import models  # Add this import

User = get_user_model()

class EmailOrUsernameModelBackend(ModelBackend):
    """
    Authenticate against either username or email.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None
            
        try:
            # Try to fetch user by username or email (case-insensitive)
            user = User.objects.get(
                models.Q(username__iexact=username) | 
                models.Q(email__iexact=username)
            )
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            # Run the default password hasher once to reduce timing difference
            User().set_password(password)
        except User.MultipleObjectsReturned:
            # Handle case where email is not unique (shouldn't happen if you've made email unique)
            return None