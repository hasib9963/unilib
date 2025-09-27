from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils import timezone
from datetime import timedelta

from django.db.models import Sum
from .models import Borrow, Fine, Reservation
from .forms import BorrowForm, ReturnForm, FinePaymentForm, ReservationForm
from books.models import Book
from accounts.models import User
from django.urls import reverse
from notifications.utils import notify  # adjust import to your project structure
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

class BorrowCreateView(LoginRequiredMixin, CreateView):
    model = Borrow
    form_class = BorrowForm
    template_name = 'transactions/borrow_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['book'] = get_object_or_404(Book, pk=self.kwargs['pk'])
        return context

    def get_initial(self):
        book = get_object_or_404(Book, pk=self.kwargs['pk'])
        return {
            'book': book,
            'user': self.request.user,
            'due_date': timezone.now().date() + timedelta(days=14)
        }

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        user = self.request.user
        book = get_object_or_404(Book, pk=self.kwargs['pk'])
        
        # Determine the borrower user
        if user.role in [User.Role.STUDENT, User.Role.FACULTY]:
            # Student/faculty borrowing for themselves
            borrower = user
            form.instance.user = user
            form.instance.book = book
            form.instance.due_date = timezone.now().date() + timedelta(days=7)
        else:
            # Admin/librarian borrowing for another user
            borrower = form.cleaned_data['user']
            form.instance.due_date = form.cleaned_data['due_date']
        
        # Check if user already has this book borrowed (for ALL users)
        if Borrow.objects.filter(user=borrower, book=book, is_returned=False).exists():
            messages.error(self.request, f"User '{borrower.get_full_name()}' has already borrowed '{book.title}' and hasn't returned it yet.")
            return redirect('book-detail', pk=book.pk)

        form.instance.issued_by = user
        response = super().form_valid(form)

        book_url = reverse('book-detail', kwargs={'pk': book.pk})

        # Notify borrower
        notify(borrower, f"You borrowed '{book.title}'", url=book_url)

        # Notify all staff (except the borrower if they are staff)
        staff_users = User.objects.filter(role__in=[User.Role.ADMIN, User.Role.LIBRARIAN])
        for staff in staff_users:
            if staff != borrower:
                notify(staff, f"{borrower.get_full_name()} borrowed '{book.title}'", url=book_url)

        # Email to borrower
        subject = f"You borrowed '{book.title}'"
        html_content = render_to_string('emails/borrowed_book.html', {
            'user': borrower,
            'book': book,
            'due_date': form.instance.due_date,
            'url': self.request.build_absolute_uri(book_url),
        })
        email = EmailMultiAlternatives(subject, '', to=[borrower.email])
        email.attach_alternative(html_content, "text/html")
        email.send()

        messages.success(self.request, f"'{book.title}' borrowed successfully for {borrower.get_full_name()}!")
        return response

    def get_success_url(self):
        return reverse_lazy('book-detail', kwargs={'pk': self.kwargs['pk']})

from django.db.models import Q

class BorrowListView(LoginRequiredMixin, ListView):
    model = Borrow
    template_name = 'transactions/borrow_list.html'
    context_object_name = 'borrows'
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        queryset = Borrow.objects.all().order_by('-issue_date')
        search_query = self.request.GET.get('search', '').strip()
        
        if search_query:
            queryset = queryset.filter(
                Q(book__title__icontains=search_query) |
                Q(book__author__icontains=search_query) |
                Q(user__first_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query) |
                Q(user__email__icontains=search_query) |
                Q(user__university_id__icontains=search_query)
            )
        
        if user.role in [User.Role.ADMIN, User.Role.LIBRARIAN]:
            return queryset
        return queryset.filter(user=user)


class ReturnBookView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Borrow
    form_class = ReturnForm
    template_name = 'transactions/return_book.html'
    
    def test_func(self):
        borrow = self.get_object()
        return (self.request.user.is_admin or 
                self.request.user.is_librarian or
                self.request.user == borrow.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        borrow = self.get_object()
        
        # Get fine information
        fine_exists = hasattr(borrow, 'fine')
        fine_amount = borrow.fine.amount if fine_exists else 0
        fine_paid = borrow.fine.is_paid if fine_exists else True  # True if no fine
        
        context.update({
            'fine_exists': fine_exists,
            'fine_amount': fine_amount,
            'fine_paid': fine_paid,
            'has_unpaid_fine': borrow.has_unpaid_fine,
        })
        return context

    def form_valid(self, form):
        borrow = form.save(commit=False)
        borrow.return_book()
        response = super().form_valid(form)

        borrower = borrow.user
        book = borrow.book
        book_url = reverse('book-detail', kwargs={'pk': book.pk})

        # Check fine status and set appropriate messages
        if hasattr(borrow, 'fine'):
            if borrow.fine.is_paid:
                if self.request.user == borrower:
                    messages.success(self.request, "Your fine has been paid and book returned successfully!")
                else:
                    messages.success(self.request, f"User {borrower.get_full_name()} has paid the fine and book returned successfully!")
            else:
                if self.request.user == borrower:
                    messages.warning(self.request, "Book returned successfully, but you haven't paid the fine yet!")
                else:
                    messages.warning(self.request, f"Book returned successfully, but user {borrower.get_full_name()} hasn't paid the fine yet!")
        else:
            messages.success(self.request, 'Book returned successfully!')

        # Notify borrower
        notify(borrower, f"You returned '{book.title}'", url=book_url)

        # Notify all staff
        staff_users = User.objects.filter(role__in=[User.Role.ADMIN, User.Role.LIBRARIAN])
        for staff in staff_users:
            if staff != borrower:
                notify(staff, f"{borrower.get_full_name()} returned '{book.title}'", url=book_url)

        # Email to borrower
        subject = f"You returned '{book.title}'"
        html_content = render_to_string('emails/returned_book.html', {
            'user': borrower,
            'book': book,
            'url': self.request.build_absolute_uri(book_url),
        })
        email = EmailMultiAlternatives(subject, '', to=[borrower.email])
        email.attach_alternative(html_content, "text/html")
        email.send()

        # Notify next reserver
        next_reservation = Reservation.objects.filter(book=book, status='PENDING').order_by('reservation_date').first()
        if next_reservation:
            next_reservation.status = 'AVAILABLE'
            next_reservation.notified_at = timezone.now()
            next_reservation.save()

            notify(next_reservation.user,
                f"Your reserved book '{book.title}' is now available",
                type='RES',
                url=book_url)
            
            # Email to next reserver
            subject = f"'{book.title}' is now available"
            html_content = render_to_string('emails/book_available.html', {
                'user': next_reservation.user,
                'book': book,
                'url': self.request.build_absolute_uri(book_url),
            })
            email = EmailMultiAlternatives(subject, '', to=[next_reservation.user.email])
            email.attach_alternative(html_content, "text/html")
            email.send()

        return response

    def get_success_url(self):
        return reverse_lazy('borrow-list')
    

class FineListView(LoginRequiredMixin, ListView):
    model = Fine
    template_name = 'transactions/fine_list.html'
    context_object_name = 'fines'
    
    def get_queryset(self):
        # First, check for any overdue books that need fines
        overdue_borrows = Borrow.objects.filter(
            is_returned=False,
            due_date__lt=timezone.now().date()
        )
        for borrow in overdue_borrows:
            borrow.check_and_create_fine()
        
        if self.request.user.is_admin or self.request.user.is_librarian:
            return Fine.objects.all().order_by('-created_at')
        return Fine.objects.filter(user=self.request.user).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        
        total_pending_fines = queryset.filter(is_paid=False).aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        total_paid_fines = queryset.filter(is_paid=True).aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        context['total_pending_fines'] = total_pending_fines
        context['total_paid_fines'] = total_paid_fines
        
        return context
    
class PayFineView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Fine
    form_class = FinePaymentForm
    template_name = 'transactions/pay_fine.html'
    
    def test_func(self):
        # Only admin/librarian can mark fines as paid
        return self.request.user.is_admin or self.request.user.is_librarian
    
    def form_valid(self, form):
        fine = form.save(commit=False)
        fine.pay_fine()
        
        # Set appropriate success message
        if self.request.user == fine.user:
            messages.success(self.request, 'Your fine has been paid successfully!')
        else:
            messages.success(self.request, f"Fine for {fine.user.get_full_name()} has been paid successfully!")
        
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('fine-list')


class ReservationCreateView(LoginRequiredMixin, CreateView):
    model = Reservation
    form_class = ReservationForm
    template_name = 'transactions/reservation_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['book'] = get_object_or_404(Book, pk=self.kwargs['pk'])
        return context

    def get_initial(self):
        book = get_object_or_404(Book, pk=self.kwargs['pk'])
        return {
            'book': book,
            'user': self.request.user
        }

    def form_valid(self, form):
        user = self.request.user
        book = get_object_or_404(Book, pk=self.kwargs['pk'])

        if user.role in [User.Role.STUDENT, User.Role.FACULTY]:
            form.instance.user = user
            form.instance.book = book

        response = super().form_valid(form)

        reserver = form.instance.user
        book_url = reverse('book-detail', kwargs={'pk': book.pk})

        # ✅ Notify reserver
        notify(reserver,
            f"You reserved '{book.title}'. You'll be notified when it becomes available.",
            type='RES',
            url=book_url)

        # ✅ Notify staff (excluding reserver)
        staff_users = User.objects.filter(role__in=[User.Role.ADMIN, User.Role.LIBRARIAN])
        for staff in staff_users:
            if staff != reserver:
                notify(staff,
                    f"{reserver.get_full_name()} reserved '{book.title}'",
                    type='RES',
                    url=book_url)
        # Email to reserver
        subject = f"You reserved '{book.title}'"
        html_content = render_to_string('emails/reserved_book.html', {
            'user': reserver,
            'book': book,
            'url': self.request.build_absolute_uri(book_url),
        })
        email = EmailMultiAlternatives(subject, '', to=[reserver.email])
        email.attach_alternative(html_content, "text/html")
        email.send()

        messages.success(self.request, 'Book reserved successfully! You will be notified when available.')
        return response

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs


    def get_success_url(self):
        return reverse_lazy('book-detail', kwargs={'pk': self.kwargs['pk']})
    
class ReservationListView(LoginRequiredMixin, ListView):
    model = Reservation
    template_name = 'transactions/reservation_list.html'
    context_object_name = 'reservations'
    
    def get_queryset(self):
        if self.request.user.is_admin or self.request.user.is_librarian:
            return Reservation.objects.all().order_by('-reservation_date')
        return self.request.user.reservations.all().order_by('-reservation_date')