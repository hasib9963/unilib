from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils import timezone
from datetime import timedelta
from django.views.generic import View

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
            'due_date': timezone.now().date() + timedelta(days=7)
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
        notify(borrower, f"You borrowed '{book.title}'", type='Borrowed Book', url=book_url)

        # Notify all staff (except the borrower if they are staff)
        staff_users = User.objects.filter(role__in=[User.Role.ADMIN, User.Role.LIBRARIAN])
        for staff in staff_users:
            if staff != borrower:
                notify(staff, f"{borrower.get_full_name()} borrowed '{book.title}'",  type='Borrowed Book', url=book_url)

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
        
        # Apply status filter
        status_filter = self.request.GET.get('status', '')
        if status_filter == 'active':
            queryset = queryset.filter(is_returned=False)
        elif status_filter == 'overdue':
            queryset = queryset.filter(is_returned=False, due_date__lt=timezone.now().date())
        elif status_filter == 'returned':
            queryset = queryset.filter(is_returned=True)
        
        if user.role in [User.Role.ADMIN, User.Role.LIBRARIAN]:
            return queryset
        return queryset.filter(user=user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get base queryset for statistics (considering user role)
        if user.role in [User.Role.ADMIN, User.Role.LIBRARIAN]:
            base_queryset = Borrow.objects.all()
        else:
            base_queryset = Borrow.objects.filter(user=user)
        
        # Calculate statistics based on user role
        total_borrows_count = base_queryset.count()
        active_borrows_count = base_queryset.filter(is_returned=False).count()
        overdue_borrows_count = base_queryset.filter(is_returned=False, due_date__lt=timezone.now().date()).count()
        returned_borrows_count = base_queryset.filter(is_returned=True).count()
        
        # Add statistics to context
        context.update({
            'total_borrows_count': total_borrows_count,
            'active_borrows_count': active_borrows_count,
            'overdue_borrows_count': overdue_borrows_count,
            'returned_borrows_count': returned_borrows_count,
        })
        
        return context

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
        user = self.request.user
        
        # Get fine information
        fine_exists = hasattr(borrow, 'fine')
        fine_amount = borrow.fine.amount if fine_exists else 0
        fine_paid = borrow.fine.is_paid if fine_exists else True  # True if no fine
        

        if user.role in [User.Role.ADMIN, User.Role.LIBRARIAN]:
            base_queryset = Borrow.objects.all()
        else:
            base_queryset = Borrow.objects.filter(user=user)
        
        total_borrows_count = base_queryset.count()
        active_borrows_count = base_queryset.filter(is_returned=False).count()
        overdue_borrows_count = base_queryset.filter(is_returned=False, due_date__lt=timezone.now().date()).count()
        returned_borrows_count = base_queryset.filter(is_returned=True).count()
        
        context.update({
            'fine_exists': fine_exists,
            'fine_amount': fine_amount,
            'fine_paid': fine_paid,
            'has_unpaid_fine': borrow.has_unpaid_fine,

            'total_borrows_count': total_borrows_count,
            'active_borrows_count': active_borrows_count,
            'overdue_borrows_count': overdue_borrows_count,
            'returned_borrows_count': returned_borrows_count,
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
        notify(borrower, f"You returned '{book.title}'", type='Returned Book', url=book_url)

        # Notify all staff
        staff_users = User.objects.filter(role__in=[User.Role.ADMIN, User.Role.LIBRARIAN])
        for staff in staff_users:
            if staff != borrower:
                notify(staff, f"{borrower.get_full_name()} returned '{book.title}'",  type='Returned Book', url=book_url)

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
    paginate_by = 10  # Add this line
    
    def get_queryset(self):
        # Check for overdue books that need fines when someone visits the fine list
        overdue_borrows = Borrow.objects.filter(
            is_returned=False,
            due_date__lt=timezone.now().date(),
            overdue_notification_sent=False
        )
        
        print(f"Found {overdue_borrows.count()} overdue borrows needing fines")
        
        for borrow in overdue_borrows:
            # Pass the request to the method
            fine_created = borrow.check_and_create_fine(self.request)
            if fine_created:
                borrow.overdue_notification_sent = True
                borrow.save(update_fields=['overdue_notification_sent'])
                print(f"✓ Created fine for {borrow}")
        
        # Return appropriate fines based on user role
        if hasattr(self.request.user, 'role'):
            if self.request.user.role in [User.Role.ADMIN, User.Role.LIBRARIAN]:
                return Fine.objects.all().order_by('-created_at')
        elif self.request.user.is_staff:
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
        
        if hasattr(self.request.user, 'role'):
            context['is_staff_user'] = self.request.user.role in [User.Role.ADMIN, User.Role.LIBRARIAN]
        else:
            context['is_staff_user'] = self.request.user.is_staff
        
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
        
        # Send email notification
        self.send_payment_email(fine)
        
        # Set appropriate success message
        if self.request.user == fine.user:
            messages.success(self.request, 'Your fine has been paid successfully!')
        else:
            messages.success(self.request, f"Fine for {fine.user.get_full_name()} has been paid successfully!")
        
        return super().form_valid(form)
    
    def send_payment_email(self, fine):
        """Send email notification for fine payment"""
        user = fine.user
        book = fine.borrow.book
        book_url = self.request.build_absolute_uri(reverse('book-detail', kwargs={'pk': book.pk}))
        book_list_url = self.request.build_absolute_uri(reverse('book-list'))
        
        subject = f"Fine Payment Confirmation - {book.title}"
        html_content = render_to_string('emails/fine_payment_confirmation.html', {
            'user': user,
            'book': book,
            'fine': fine,
            'url': book_url,
            'book_list_url': book_list_url,  # Add this line
            'library_name': 'UniLib',
            'payment_date': timezone.now().date(),
        })
        
        try:
            email = EmailMultiAlternatives(subject, '', to=[user.email])
            email.attach_alternative(html_content, "text/html")
            email.send()
        except Exception as e:
            # Log the error but don't break the payment process
            print(f"Failed to send payment confirmation email: {e}")
    
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
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        reservations = self.get_queryset()
        
        context['pending_count'] = reservations.filter(status='PENDING').count()
        context['available_count'] = reservations.filter(status='AVAILABLE').count()
        context['completed_count'] = reservations.filter(status='COMPLETED').count()
        context['cancelled_count'] = reservations.filter(status='CANCELLED').count()
        
        return context
class ReservationCancelView(LoginRequiredMixin, View):
    def post(self, request, pk):
        reservation = get_object_or_404(Reservation, pk=pk)
        
        # Check if user has permission to cancel this reservation
        if not (request.user.is_admin or request.user.is_librarian or reservation.user == request.user):
            messages.error(request, "You don't have permission to cancel this reservation.")
            return redirect('reservation-list')
        
        if reservation.status in ['COMPLETED', 'CANCELLED']:
            messages.warning(request, "This reservation cannot be cancelled.")
            return redirect('reservation-list')
        
        # Store old status for notification
        old_status = reservation.status
        reservation.status = 'CANCELLED'
        reservation.save()
        
        # Create notifications
        book_url = reverse('book-detail', kwargs={'pk': reservation.book.pk})
        reservation_url = reverse('reservation-list')
        
        # Notify the user who made the reservation
        notify(reservation.user,
            f"Your reservation for '{reservation.book.title}' has been cancelled.",
            type='RES_CANCEL',
            url=reservation_url)
        
        # Notify staff (excluding the user who cancelled if they're staff)
        staff_users = User.objects.filter(role__in=[User.Role.ADMIN, User.Role.LIBRARIAN])
        for staff in staff_users:
            if staff != request.user:
                notify(staff,
                    f"Reservation for '{reservation.book.title}' by {reservation.user.get_full_name()} was cancelled.",
                    type='RES_CANCEL',
                    url=reservation_url)
        
        # Send email notification to the user
        subject = f"Reservation Cancelled: {reservation.book.title}"
        html_content = render_to_string('emails/reservation_cancelled.html', {
            'user': reservation.user,
            'book': reservation.book,
            'reservation': reservation,
            'cancelled_by': request.user.get_full_name(),
            'reservation_url': request.build_absolute_uri(reservation_url),
            'book_url': request.build_absolute_uri(book_url),
        })
        
        try:
            email = EmailMultiAlternatives(subject, '', to=[reservation.user.email])
            email.attach_alternative(html_content, "text/html")
            email.send()
        except Exception as e:
            # Log email error but don't break the flow
            print(f"Email sending failed: {e}")
        
        messages.success(request, 'Reservation cancelled successfully.')
        return redirect('reservation-list')