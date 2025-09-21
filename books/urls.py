from django.urls import path
from .views import (
    BookListView, BookDetailView, BookCreateView, BookUpdateView, BookDeleteView,
    CategoryListView, CategoryDetailView, CategoryCreateView, CategoryUpdateView, CategoryDeleteView
)

urlpatterns = [
    # Book URLs
    path('', BookListView.as_view(), name='book-list'),
    path('<int:pk>/', BookDetailView.as_view(), name='book-detail'),
    path('new/', BookCreateView.as_view(), name='book-create'),
    path('<int:pk>/update/', BookUpdateView.as_view(), name='book-update'),
    path('<int:pk>/delete/', BookDeleteView.as_view(), name='book-delete'),
    
    # Category URLs
    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('categories/<int:pk>/', CategoryDetailView.as_view(), name='category-detail'),
    path('categories/new/', CategoryCreateView.as_view(), name='category-create'),
    path('categories/<int:pk>/update/', CategoryUpdateView.as_view(), name='category-update'),
    path('categories/<int:pk>/delete/', CategoryDeleteView.as_view(), name='category-delete'),
]