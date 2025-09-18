# # books/filters.py

# import django_filters
# from .models import Book

# class BookFilter(django_filters.FilterSet):
#     title = django_filters.CharFilter(lookup_expr='icontains')
#     author = django_filters.CharFilter(lookup_expr='icontains')
#     isbn = django_filters.CharFilter(lookup_expr='exact')
#     category = django_filters.CharFilter(field_name='category__name', lookup_expr='icontains')

#     class Meta:
#         model = Book
#         fields = ['title', 'author', 'isbn', 'category']


import django_filters
from .models import Book
from django.db.models import Q

class BookFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method='filter_by_all', label='Search')

    class Meta:
        model = Book
        fields = ['q', 'category']

    def filter_by_all(self, queryset, name, value):
        return queryset.filter(
            Q(title__icontains=value) |
            Q(author__icontains=value) |
            Q(isbn__icontains=value)
        )
