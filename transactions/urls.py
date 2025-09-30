from django.urls import path
from transactions.views import ReservationCancelView
from accounts import views
from .views import (
    BorrowCreateView, BorrowListView, ReturnBookView,
    FineListView, PayFineView,
    ReservationCreateView, ReservationListView
)

urlpatterns = [
    # Borrow URLs
    path('borrows/', BorrowListView.as_view(), name='borrow-list'),
    path('borrows/<int:pk>/', ReturnBookView.as_view(), name='return-book'),
    path('borrows/new/<int:pk>/', BorrowCreateView.as_view(), name='book-issue'),
    
    # Fine URLs
    path('fines/', FineListView.as_view(), name='fine-list'),
    path('fines/<int:pk>/pay/', PayFineView.as_view(), name='pay-fine'),
    
    # Reservation URLs
    path('reservations/', ReservationListView.as_view(), name='reservation-list'),
    path('reservations/new/<int:pk>/', ReservationCreateView.as_view(), name='book-reserve'),
    path('reservations/cancel/<int:pk>/', ReservationCancelView.as_view(), name='reservation-cancel'),
]