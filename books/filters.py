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
