from django.urls import path
from .views import register, profile, UserCreateView, user_list, user_detail, user_update, user_delete, ConfirmEmailView
from django.contrib.auth.views import  LoginView, LogoutView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy

urlpatterns = [
    path('register/', register, name='register'),
     path('activate/<uidb64>/<token>/', ConfirmEmailView.as_view(), name='confirm-email'),
    path('login/', LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', profile, name='profile'),
    
    # Password change

     path('password-change/',
     auth_views.PasswordChangeView.as_view(
          template_name='password/password_change.html',
          success_url=reverse_lazy('password_change_done')
     ),
     name='password_change'),
     path('password-change/done/',
     auth_views.PasswordChangeDoneView.as_view(
          template_name='password/password_change_done.html'
     ),
     name='password_change_done'),

     path('password-reset/', 
          auth_views.PasswordResetView.as_view(
          template_name='password/password_reset.html',
          html_email_template_name='password/password_reset_email.html',  # Note the 'html_' prefix
          subject_template_name='password/password_reset_subject.txt',
          extra_email_context=None,
          ),
          name='password_reset'),

    path('password-reset/done/', 
         PasswordResetDoneView.as_view(template_name='password/password_reset_done.html'),
         name='password_reset_done'),

    path('password-reset-confirm/<uidb64>/<token>/', 
         PasswordResetConfirmView.as_view(template_name='password/password_reset_confirm.html'),
         name='password_reset_confirm'),
         
    path('password-reset-complete/', 
         PasswordResetCompleteView.as_view(template_name='password/password_reset_complete.html'),
         name='password_reset_complete'),
    
    # User management (for admin)
    path('users/', user_list, name='user-list'),
    path('users/new/', UserCreateView.as_view(), name='user-create'),
    path('users/<int:pk>/', user_detail, name='user-detail'),
    path('users/<int:pk>/update/', user_update, name='user-update'),
    path('users/<int:pk>/delete/', user_delete, name='user-delete'),
]