from django.shortcuts import get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils import timezone
from datetime import timedelta
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

        if user.role in [User.Role.STUDENT, User.Role.FACULTY]:
            form.instance.user = user
            form.instance.book = book
            form.instance.due_date = timezone.now().date() + timedelta(days=7)

        form.instance.issued_by = user
        response = super().form_valid(form)

        borrower = form.instance.user
        book_url = reverse('book-detail', kwargs={'pk': book.pk})

        # ✅ Notify borrower (always "You borrowed ...")
        notify(borrower, f"You borrowed '{book.title}'", url=book_url)

        # ✅ Notify all staff (including acting user if they're staff), "Hasib borrowed ..."
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

        messages.success(self.request, f"'{book.title}' borrowed successfully!")
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

    def form_valid(self, form):
        borrow = form.save(commit=False)
        borrow.return_book()
        response = super().form_valid(form)

        borrower = borrow.user
        book = borrow.book
        book_url = reverse('book-detail', kwargs={'pk': book.pk})

        # ✅ Notify borrower
        notify(borrower, f"You returned '{book.title}'", url=book_url)

        # ✅ Notify all staff (excluding borrower)
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

        # ✅ Notify next reserver (existing logic)
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

        messages.success(self.request, 'Book returned successfully!')
        return response

    def get_success_url(self):
        return reverse_lazy('borrow-list')
    
class FineListView(LoginRequiredMixin, ListView):
    model = Fine
    template_name = 'transactions/fine_list.html'
    context_object_name = 'fines'
    
    def get_queryset(self):
        if self.request.user.is_admin or self.request.user.is_librarian:
            return Fine.objects.all().order_by('-created_at')
        return Fine.objects.filter(borrow__user=self.request.user).order_by('-created_at')

class PayFineView(LoginRequiredMixin, UpdateView):
    model = Fine
    form_class = FinePaymentForm
    template_name = 'transactions/pay_fine.html'
    
    def form_valid(self, form):
        fine = form.save(commit=False)
        fine.pay_fine()
        messages.success(self.request, 'Fine paid successfully!')
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