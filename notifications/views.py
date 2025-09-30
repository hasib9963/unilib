from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Notification
from django.core.paginator import Paginator

@login_required
def notification_list(request):
    notifications = request.user.notifications.all().order_by('-created_at')
    paginator = Paginator(notifications, 10)  # Show 10 notifications per page
    
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calculate counts
    unread_count = request.user.notifications.filter(is_read=False).count()
    total_count = request.user.notifications.count()
    read_count = total_count - unread_count
    
    return render(request, 'notifications/notification_list.html', {
        'notifications': page_obj,
        'has_next': page_obj.has_next(),
        'unread_count': unread_count,
        'read_count': read_count,
        'total_count': total_count
    })

@login_required
def mark_as_read(request, pk):
    notification = request.user.notifications.get(pk=pk)
    notification.is_read = True
    notification.save()
    return redirect('notification-list')

@login_required
def mark_all_as_read(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return redirect('notification-list')