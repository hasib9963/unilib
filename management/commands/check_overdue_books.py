# from django.core.management.base import BaseCommand
# from django.utils import timezone
# from books.models import Borrow

# class Command(BaseCommand):
#     help = 'Check for overdue books and create fines'
    
#     def handle(self, *args, **options):
#         overdue_borrows = Borrow.objects.filter(
#             is_returned=False,
#             due_date__lt=timezone.now().date()
#         )
        
#         for borrow in overdue_borrows:
#             borrow.check_and_create_fine()
        
#         self.stdout.write(
#             self.style.SUCCESS(f'Checked {overdue_borrows.count()} overdue borrows')
#         )

from django.core.management.base import BaseCommand
from django.utils import timezone
from books.models import Borrow
from django.conf import settings

class Command(BaseCommand):
    help = 'Check for overdue books and create fines with notifications'
    
    def handle(self, *args, **options):
        overdue_borrows = Borrow.objects.filter(
            is_returned=False,
            due_date__lt=timezone.now().date()
        ).select_related('user', 'book')
        
        fine_count = 0
        notification_count = 0
        
        for borrow in overdue_borrows:
            # This will automatically create fines and send notifications
            # through the enhanced check_and_create_fine method
            if borrow.check_and_create_fine():
                fine_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Checked {overdue_borrows.count()} overdue borrows, '
                f'created {fine_count} new fines with notifications'
            )
        )