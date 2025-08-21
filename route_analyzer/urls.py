from django.urls import path
from . import views

app_name = 'route_analyzer'

urlpatterns = [
    path('', views.index, name='index'),
    path('search/', views.search_routes, name='search_routes'),
    path('route/<str:route_no>/', views.route_detail, name='route_detail'),
    path('stop/<str:stop_name>/', views.stop_detail, name='stop_detail'),
    path('profitability/', views.route_profitability, name='route_profitability'),
]
