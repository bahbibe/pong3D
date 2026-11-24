from django.urls import path

from .views import mark_all_notifications_as_read, mark_notification_as_read

# Mounted at /api/auth/notifications/ (the URLs the frontend already uses).
urlpatterns = [
    path("mark_as_read/", mark_all_notifications_as_read, name="mark-notifications-as-read"),
    path("mark_as_read/<str:uuid>/", mark_notification_as_read, name="mark-notification-as-read"),
]
