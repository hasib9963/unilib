from django.views.generic import TemplateView
from books.models import Book
from django.db.models import Count

class HomePageView(TemplateView):
    template_name = 'home/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['featured_books'] = Book.objects.filter(available_copies__gt=0)[:6]
        context['popular_books'] = Book.objects.annotate(
            borrow_count=Count('borrows')
        ).order_by('-borrow_count')[:4]
        return context