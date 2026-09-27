from django.urls import path
from .views import AttendanceListView, ClockInView, ClockOutView, TeamAttendanceView

urlpatterns = [
    path('', AttendanceListView.as_view(), name='attendance_list'),
    path('clock-in/', ClockInView.as_view(), name='clock_in'),
    path('clock-out/', ClockOutView.as_view(), name='clock_out'),
    path('team/', TeamAttendanceView.as_view(), name='team_attendance'),
]
