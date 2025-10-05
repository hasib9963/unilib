from django.core.management.base import BaseCommand
from django.utils import timezone
from transactions.models import Borrow

class Command(BaseCommand):
    help = 'Check for overdue books and create fines'

    def handle(self, *args, **options):
        overdue_borrows = Borrow.objects.filter(
            is_returned=False,
            due_date__lt=timezone.now().date(),
            overdue_notification_sent=False
        )
        
        self.stdout.write(f"Found {overdue_borrows.count()} overdue borrows")
        
        for borrow in overdue_borrows:
            self.stdout.write(f"Processing overdue: {borrow}")
            fine_created = borrow.check_and_create_fine()
            if fine_created:
                borrow.overdue_notification_sent = True
                borrow.save(update_fields=['overdue_notification_sent'])
                self.stdout.write(f"✓ Fine created and notification sent for {borrow}")
            else:
                self.stdout.write(f"✗ No fine created for {borrow}")
        
        self.stdout.write(
            self.style.SUCCESS('Successfully processed all overdue books')
        )