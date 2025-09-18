# notifications/urls.py

from django.urls import path
from .views import notification_list, mark_as_read, mark_all_as_read

urlpatterns = [
    path('', notification_list, name='notification-list'),
    path('<int:pk>/mark-read/', mark_as_read, name='mark-as-read'),
    path('mark-all-read/', mark_all_as_read, name='mark-all-as-read'),
]