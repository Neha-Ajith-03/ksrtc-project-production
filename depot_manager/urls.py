from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='depot_manager_index'),
    path('depots/', views.depot_list, name='depot_list'),
    path('depots/<str:depot_id>/', views.depot_detail, name='depot_detail'),
    path('employees/', views.employee_list, name='employee_list'),
    path('employees/<str:emp_id>/', views.employee_detail, name='employee_detail'),
    path('attendance/', views.mark_attendance, name='mark_attendance'),
    path('assign-trips/', views.assign_trips, name='assign_trips'),
    path('daily-roster/', views.daily_roster, name='daily_roster'),
    # Buses pages removed
    path('employees/<str:emp_id>/print-trips/', views.print_employee_trips, name='print_employee_trips'),
]
