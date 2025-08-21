from django.urls import path
from . import views
from bus_route import views as bus_route_views


urlpatterns = [
    path('', views.main_dashboard_view, name='main_dashboard'),
    path('route/', views.bus_route_view, name='bus_route_view'),
    path('route/schedule/', views.schedule_list_view, name='schedule_list_view'),
    path('route/schedule/<str:schedule_no>/', views.trip_list_view, name='trip_list_view'),
    path('route/schedule/<str:schedule_no>/trip/<int:trip_no>/<str:route_no>', views.trip_map_view, name='trip_map_view'),
    path('analyzer/', views.enhanced_schedule_analyzer_view, name='enhanced_schedule_analyzer'),
    path('submit/', views.schedule_submit_view, name='schedule_submit'),
    path('api/route-details/', views.get_route_details, name='get_route_details'),
    path('revenue-analysis/', views.revenue_analysis, name='revenue_analysis'),
    path('trip-revenue-analysis/', views.trip_revenue_analysis, name='trip_revenue_analysis'),

]