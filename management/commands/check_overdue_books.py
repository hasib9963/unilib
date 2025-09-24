from django.core.management.base import BaseCommand
from django.utils import timezone
from books.models import Borrow

class Command(BaseCommand):
    help = 'Check for overdue books and create fines'
    
    def handle(self, *args, **options):
        overdue_borrows = Borrow.objects.filter(
            is_returned=False,
            due_date__lt=timezone.now().date()
        )
        
        for borrow in overdue_borrows:
            borrow.check_and_create_fine()
        
        self.stdout.write(
            self.style.SUCCESS(f'Checked {overdue_borrows.count()} overdue borrows')
        )