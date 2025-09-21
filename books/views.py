# books/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django_filters.views import FilterView
from .models import Book, Category
from .forms import BookForm, CategoryForm, BookSearchForm
from .filters import BookFilter
from transactions.models import Borrow

from django_filters.views import FilterView
from django.db.models import Count, Q
from .models import Book, Category
from .filters import BookFilter
from .forms import BookSearchForm

class BookListView(FilterView):
    model = Book
    template_name = 'books/book_list.html'
    context_object_name = 'books'
    filterset_class = BookFilter
    paginate_by = 12

    def get_queryset(self):
        qs = super().get_queryset().select_related('category')

        # Filter by availability
        availability = self.request.GET.get('availability')
        if availability == 'available':
            qs = qs.filter(available_copies__gt=0)
        elif availability == 'unavailable':
            qs = qs.filter(available_copies=0)

        # Apply sorting
        sort = self.request.GET.get('sort')
        if sort == 'popular':
            qs = qs.annotate(num_borrows=Count('borrows')).order_by('-num_borrows')
        elif sort in ['title', '-title', '-created_at']:
            qs = qs.order_by(sort)
        else:
            qs = qs.order_by('-created_at')

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = BookSearchForm(self.request.GET or None)
        context['categories'] = Category.objects.all()
        context['current_view'] = self.request.GET.get('view', 'grid')  # Default to grid
        
        # Add user's borrowed books information if user is authenticated
        if self.request.user.is_authenticated:
            borrowed_book_ids = Borrow.objects.filter(
                user=self.request.user, 
                is_returned=False
            ).values_list('book_id', flat=True)
            context['borrowed_book_ids'] = list(borrowed_book_ids)
        
        return context

class BookDetailView(DetailView):
    model = Book
    template_name = 'books/book_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['is_borrowed'] = self.object.is_borrowed_by_user(self.request.user)
        return context
class BookCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Book
    form_class = BookForm
    template_name = 'books/book_form.html'
    success_url = reverse_lazy('book-list')

    def test_func(self):
        return self.request.user.is_admin or self.request.user.is_librarian
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['is_create'] = True  # Pass flag to form to indicate creation
        return kwargs
    
    def form_valid(self, form):
        form.instance.added_by = self.request.user
        messages.success(self.request, 'Book added successfully!')
        return super().form_valid(form)
class BookUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Book
    form_class = BookForm
    template_name = 'books/book_form.html'

    def test_func(self):
        return self.request.user.is_admin or self.request.user.is_librarian

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['is_create'] = False  # Pass flag to form to indicate update
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Book updated successfully!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('book-detail', kwargs={'pk': self.object.pk})
class BookDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Book
    template_name = 'books/book_confirm_delete.html'
    success_url = reverse_lazy('book-list')
    
    def test_func(self):
        return self.request.user.is_admin or self.request.user.is_librarian
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Book deleted successfully!')
        return super().delete(request, *args, **kwargs)


class CategoryListView(ListView):
    model = Category
    template_name = 'books/category_list.html'
    context_object_name = 'categories'

class CategoryDetailView(DetailView):
    model = Category
    template_name = 'books/category_detail.html'

class CategoryCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'books/category_form.html'
    success_url = reverse_lazy('category-list')
    def test_func(self):
        return self.request.user.is_admin or self.request.user.is_librarian
    
    def form_valid(self, form):
        messages.success(self.request, 'Category created successfully!')
        return super().form_valid(form)

class CategoryUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'books/category_form.html'
    success_url = reverse_lazy('category-list')
    
    def test_func(self):
        return self.request.user.is_admin or self.request.user.is_librarian
    
    def form_valid(self, form):
        messages.success(self.request, 'Category updated successfully!')
        return super().form_valid(form)
    


class CategoryDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Category
    template_name = 'books/category_confirm_delete.html'
    success_url = reverse_lazy('category-list')
    
    def test_func(self):
        return self.request.user.is_admin or self.request.user.is_librarian
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Category deleted successfully!')
        return super().delete(request, *args, **kwargs)