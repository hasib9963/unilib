from django.shortcuts import render, redirect, get_object_or_404
from transactions.models import Borrow 
from datetime import date
from django.views.generic import CreateView
from .forms import UserRegisterForm, UserUpdateForm
from .models import User
from django.contrib.auth.decorators import login_required, user_passes_test

from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.contrib import messages
from django.urls import reverse

from django.views import View
from django.http import HttpResponse
from django.contrib.auth import get_user_model

from django.db import IntegrityError

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # Require email verification
            user.save()

            # Generate token and link
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            confirm_link = request.build_absolute_uri(
                reverse('confirm-email', kwargs={'uidb64': uid, 'token': token})
            )

            # Send email
            email_subject = "Activate Your Library Account"
            email_body = render_to_string('accounts/activation_email.html', {
                'user': user,
                'confirm_link': confirm_link
            })

            email = EmailMultiAlternatives(email_subject, '', to=[user.email])
            email.attach_alternative(email_body, "text/html")
            email.send()

            messages.success(request, 'Check your email to confirm your account.')
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'accounts/register.html', {'form': form})



class ConfirmEmailView(View):
    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = get_object_or_404(get_user_model(), pk=uid)
        except (TypeError, ValueError, OverflowError, get_user_model().DoesNotExist):
            user = None

        if user and default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            return HttpResponse("Your account has been activated. You can now <a href='/accounts/login'>login</a>.")
        else:
            return HttpResponse("Activation link is invalid or expired.")

class UserCreateView(CreateView):
    model = User
    form_class = UserRegisterForm
    template_name = 'accounts/user_create.html'
    
    def form_valid(self, form):
        try:
            user = form.save()
            messages.success(self.request, f'User {user.username} created successfully!')
            return redirect('user-list')
        except IntegrityError:
            form.add_error('email', 'This email address is already in use.')
            return self.form_invalid(form)
        
@login_required
def profile(request):
    user = request.user

    # Check if we're in edit mode (from query parameter)
    edit_mode = request.GET.get('edit') == 'true'

    if request.method == 'POST':
        form = UserUpdateForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile')
    else:
        form = UserUpdateForm(instance=user)

    # Query borrow data
    active_borrows = Borrow.objects.filter(user=user, return_date__isnull=True).count()
    total_borrows = Borrow.objects.filter(user=user).count()
    fines_count = Borrow.objects.filter(user=user, due_date__lt=date.today(), return_date__isnull=True).count()

    context = {
        'form': form,
        'active_borrows': active_borrows,
        'total_borrows': total_borrows,
        'fines_count': fines_count,
        'edit_mode': edit_mode,  # Pass edit mode to template
    }
    return render(request, 'accounts/profile.html', context)


from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q

@login_required
@user_passes_test(lambda u: u.is_admin)
def user_list(request):
    user_list = User.objects.all().order_by('-date_joined')  # or any other ordering you prefer

    search_query = request.GET.get('search', '')
    if search_query:
        user_list = user_list.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(role__icontains=search_query) |
            Q(university_id__icontains=search_query)
        )

    paginator = Paginator(user_list, 10)  # Show 10 users per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'accounts/user_list.html', {
        'users': page_obj,
        'page_obj': page_obj,  # This is needed for the pagination template tags
        'is_paginated': paginator.num_pages > 1,  # This helps in template to check if pagination is needed
        'search_query': search_query
    })

from django.utils import timezone

@login_required
@user_passes_test(lambda u: u.is_admin)
def user_detail(request, pk):
    viewed_user = get_object_or_404(User, pk=pk)  # Changed variable name
    
    # Get borrow counts
    total_borrows = Borrow.objects.filter(user=viewed_user).count()
    active_borrows = Borrow.objects.filter(user=viewed_user, is_returned=False).count()
    overdue = Borrow.objects.filter(
        user=viewed_user, 
        is_returned=False,
        due_date__lt=timezone.now().date()
    ).count()
    
    context = {
        'viewed_user': viewed_user,  # Changed key name
        'total_borrows': total_borrows,
        'active_borrows': active_borrows,
        'overdue': overdue,
    }
    return render(request, 'accounts/user_detail.html', context)

@login_required
@user_passes_test(lambda u: u.is_admin)
def user_update(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'User updated successfully!')
            return redirect('user-detail', pk=user.pk)
    else:
        form = UserUpdateForm(instance=user)
    return render(request, 'accounts/user_form.html', {'form': form})


@login_required
@user_passes_test(lambda u: u.is_admin)
def user_delete(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        user.delete()
        messages.success(request, 'User deleted successfully!')
        return redirect('user-list')
    return render(request, 'accounts/user_confirm_delete.html', {'user': user})