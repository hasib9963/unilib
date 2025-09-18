from django.db.models import Sum, Count, Case, When, IntegerField
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from books.models import Book
from transactions.models import Borrow, Fine, Reservation

@login_required
def dashboard(request):
    user = request.user
    ITEMS_PER_PAGE = 5
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    # Get the current display count for each section from request
    recent_borrows_count = int(request.GET.get('recent_borrows', ITEMS_PER_PAGE))
    overdue_borrows_count = int(request.GET.get('overdue_borrows', ITEMS_PER_PAGE))
    popular_books_count = int(request.GET.get('popular_books', ITEMS_PER_PAGE))
    recent_reservations_count = int(request.GET.get('recent_reservations', ITEMS_PER_PAGE))
    user_borrows_count = int(request.GET.get('user_borrows', ITEMS_PER_PAGE))
    user_reservations_count = int(request.GET.get('user_reservations', ITEMS_PER_PAGE))

    # Admin & Librarian Dashboard
    if user.role in ['ADMIN', 'LIBRARIAN']:
        total_books = Book.objects.count()
        total_borrows = Borrow.objects.count()
        total_fines = Fine.objects.aggregate(total=Sum('amount'))['total'] or 0
        total_reservations = Reservation.objects.count()
        
        active_reservations_count = Reservation.objects.filter(
            status='PENDING'
        ).count()
        
        reservation_percentage = round(
            (active_reservations_count / total_reservations * 100) 
            if total_reservations > 0 else 0
        )

        recent_borrows = Borrow.objects.order_by('-issue_date')
        recent_borrows_total = recent_borrows.count()
        recent_borrows = recent_borrows[:recent_borrows_count]

        overdue_borrows = Borrow.objects.filter(
            is_returned=False,
            due_date__lt=timezone.now().date()
        ).order_by('due_date')
        overdue_borrows_total = overdue_borrows.count()
        overdue_borrows = overdue_borrows[:overdue_borrows_count]

        popular_books = Book.objects.annotate(
            borrow_count=Count('borrows')
        ).order_by('-borrow_count')
        popular_books_total = popular_books.count()
        popular_books = popular_books[:popular_books_count]

        recent_reservations = Reservation.objects.order_by('-reservation_date')
        recent_reservations_total = recent_reservations.count()
        recent_reservations = recent_reservations[:recent_reservations_count]

        context = {
            'total_books': total_books,
            'total_borrows': total_borrows,
            'total_fines': total_fines,
            'total_reservations': total_reservations,
            'active_borrows_count': Borrow.objects.filter(is_returned=False).count(),
            'active_reservations_count': active_reservations_count,
            'reservation_percentage': reservation_percentage,
            'recent_borrows': recent_borrows,
            'recent_borrows_total': recent_borrows_total,
            'recent_borrows_count': recent_borrows_count,
            'overdue_borrows': overdue_borrows,
            'overdue_borrows_total': overdue_borrows_total,
            'overdue_borrows_count': overdue_borrows_count,
            'popular_books': popular_books,
            'popular_books_total': popular_books_total,
            'popular_books_count': popular_books_count,
            'recent_reservations': recent_reservations,
            'recent_reservations_total': recent_reservations_total,
            'recent_reservations_count': recent_reservations_count,
            'ITEMS_PER_PAGE': ITEMS_PER_PAGE,
            'is_ajax': is_ajax,
        }

    # Student & Faculty Dashboard
    else:
        active_borrows = user.borrows.filter(is_returned=False).order_by('due_date')
        returned_borrows = user.borrows.filter(is_returned=True).order_by('-return_date')
        user_borrows = list(active_borrows) + list(returned_borrows)
        user_borrows_total = len(user_borrows)
        user_borrows = user_borrows[:user_borrows_count]
        
        user_reservations = user.reservations.all().order_by(
            Case(
                When(status='PENDING', then=0),
                When(status='AVAILABLE', then=1),
                When(status='COMPLETED', then=2),
                When(status='CANCELLED', then=3),
                default=4,
                output_field=IntegerField(),
            ),
            '-reservation_date'
        )
        user_reservations_total = user_reservations.count()
        user_reservations = user_reservations[:user_reservations_count]
        
        active_reservations_count = user.reservations.filter(
            status='PENDING'
        ).count()
        
        total_reservations = user_reservations_total
        reservation_percentage = round(
            (active_reservations_count / total_reservations * 100) 
            if total_reservations > 0 else 0
        )

        context = {
            'active_borrows_count': active_borrows.count(),
            'total_borrows': user.borrows.count(),
            'total_reservations': total_reservations,
            'active_reservations_count': active_reservations_count,
            'reservation_percentage': reservation_percentage,
            'user_borrows': user_borrows,
            'user_borrows_total': user_borrows_total,
            'user_borrows_count': user_borrows_count,
            'user_reservations': user_reservations,
            'user_reservations_total': user_reservations_total,
            'user_reservations_count': user_reservations_count,
            'user_fines': user.fines.filter(is_paid=False).aggregate(total=Sum('amount'))['total'] or 0,
            'ITEMS_PER_PAGE': ITEMS_PER_PAGE,
            'is_ajax': is_ajax,
        }

    return render(request, 'dashboard/dashboard.html', context)