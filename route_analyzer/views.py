from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db.models import Q, Avg, Count, Sum, F, FloatField
from django.db.models.functions import Coalesce
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from bus_route.models import Route, Schedule, Trip
from datetime import datetime, timedelta
import json

# Create your views here.
@login_required
def index(request):
    """Main page for route analyzer"""
    # Get unique route numbers
    route_numbers = Route.objects.values_list('route_no', flat=True).distinct().order_by('route_no')

    # Get unique stop names for search
    stop_names = Route.objects.values_list('stop_name', flat=True).distinct().order_by('stop_name')

    context = {
        'route_numbers': route_numbers,
        'stop_names': stop_names,
    }

    return render(request, 'route_analyzer/index.html', context)

@login_required
def search_routes(request):
    """Search routes by stop name"""
    query = request.GET.get('query', '')

    if not query:
        return JsonResponse({'routes': []})

    # Search for routes containing the stop name
    routes = Route.objects.filter(stop_name__icontains=query)

    # Get unique route numbers from the results
    route_numbers = routes.values_list('route_no', flat=True).distinct()

    # For each route number, get the source and destination
    result = []
    for route_no in route_numbers:
        # Get all stops for this route in order
        stops = Route.objects.filter(route_no=route_no).order_by('order_sequence')

        if stops.exists():
            result.append({
                'route_no': route_no,
                'source': stops.first().stop_name,
                'destination': stops.last().stop_name,
                'stops_count': stops.count(),
            })

    return JsonResponse({'routes': result})

@login_required
def route_detail(request, route_no):
    """Show details of a specific route with Gantt chart"""
    # Get all stops for this route in order
    stops = Route.objects.filter(route_no=route_no).order_by('order_sequence')

    if not stops.exists():
        messages.error(request, f"Route {route_no} not found.")
        return redirect('route_analyzer:index')

    # Get all schedules for this route
    schedules = Schedule.objects.filter(route_no=route_no).order_by('schedule_no', 'trip_no')

    # Calculate duration for each schedule
    for schedule in schedules:
        if schedule.start_time and schedule.end_time:
            # Convert times to minutes since midnight
            start_minutes = schedule.start_time.hour * 60 + schedule.start_time.minute
            end_minutes = schedule.end_time.hour * 60 + schedule.end_time.minute

            # Handle overnight schedules
            if end_minutes < start_minutes:
                end_minutes += 24 * 60  # Add 24 hours

            # Calculate duration in minutes
            duration_minutes = end_minutes - start_minutes

            # Format as hours and minutes
            hours = duration_minutes // 60
            minutes = duration_minutes % 60
            schedule.duration = f"{hours}h {minutes}m"

    # Prepare data for Gantt chart
    gantt_data = []
    for schedule in schedules:
        if schedule.start_time and schedule.end_time:
            gantt_data.append({
                'id': f"{schedule.schedule_no}-{schedule.trip_no}",
                'schedule_no': schedule.schedule_no,
                'trip_no': schedule.trip_no,
                'start_time': schedule.start_time.strftime('%H:%M'),
                'end_time': schedule.end_time.strftime('%H:%M'),
                'source': schedule.source,
                'destination': schedule.destination,
                'service_type': schedule.service_type,
            })

    context = {
        'route_no': route_no,
        'stops': stops,
        'schedules': schedules,
        'gantt_data': json.dumps(gantt_data),
        'source': stops.first().stop_name if stops.exists() else '',
        'destination': stops.last().stop_name if stops.exists() else '',
    }

    return render(request, 'route_analyzer/route_detail.html', context)

@login_required
def stop_detail(request, stop_name):
    """Show details of a specific stop"""
    # Get all routes passing through this stop
    routes = Route.objects.filter(stop_name=stop_name).order_by('route_no')

    if not routes.exists():
        messages.error(request, f"Stop {stop_name} not found.")
        return redirect('route_analyzer:index')

    # Get unique route numbers
    route_numbers = routes.values_list('route_no', flat=True).distinct()

    # For each route, get the source and destination
    route_details = []
    for route_no in route_numbers:
        # Get all stops for this route in order
        stops = Route.objects.filter(route_no=route_no).order_by('order_sequence')

        if stops.exists():
            # Find the position of this stop in the route
            current_stop = stops.filter(stop_name=stop_name).first()
            position = list(stops).index(current_stop) + 1 if current_stop else 0

            route_details.append({
                'route_no': route_no,
                'source': stops.first().stop_name,
                'destination': stops.last().stop_name,
                'stops_count': stops.count(),
                'position': position,
                'percentage': int((position / stops.count()) * 100) if stops.count() > 0 else 0,
            })

    context = {
        'stop_name': stop_name,
        'route_details': route_details,
    }

    return render(request, 'route_analyzer/stop_detail.html', context)

@login_required
def route_profitability(request):
    """Analyze route profitability based on EPKM data"""
    # Get date range from request or use default (last 30 days)
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    try:
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        else:
            start_date = datetime.now().date() - timedelta(days=30)

        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        else:
            end_date = datetime.now().date()
    except ValueError:
        messages.error(request, "Invalid date format. Please use YYYY-MM-DD.")
        start_date = datetime.now().date() - timedelta(days=30)
        end_date = datetime.now().date()

    # Get all trips within the date range
    trips = Trip.objects.filter(date__gte=start_date, date__lte=end_date)

    # If no trips found, show a message
    if not trips.exists():
        messages.warning(request, f"No trip data found between {start_date} and {end_date}.")
        return render(request, 'route_analyzer/route_profitability.html', {
            'start_date': start_date,
            'end_date': end_date,
        })

    # Get all unique route numbers from schedules
    route_numbers = Schedule.objects.values_list('route_no', flat=True).distinct()

    # Calculate profitability metrics for each route
    route_metrics = []

    for route_no in route_numbers:
        # Get all schedules for this route
        schedules = Schedule.objects.filter(route_no=route_no)

        if not schedules.exists():
            continue

        # Get all trips for these schedules
        route_trips = []
        total_revenue = 0
        total_distance = 0
        trip_count = 0

        for schedule in schedules:
            schedule_trips = trips.filter(schedule_no=schedule.schedule_no, trip_no=schedule.trip_no)

            for trip in schedule_trips:
                if trip.revenue is not None and schedule.trip_km is not None and schedule.trip_km > 0:
                    total_revenue += trip.revenue
                    total_distance += schedule.trip_km
                    trip_count += 1
                    route_trips.append(trip)

        # Calculate average EPKM for the route
        if total_distance > 0:
            avg_epkm = total_revenue / total_distance
        else:
            avg_epkm = 0

        # Get source and destination for the route
        route_stops = Route.objects.filter(route_no=route_no).order_by('order_sequence')
        source = route_stops.first().stop_name if route_stops.exists() else 'Unknown'
        destination = route_stops.last().stop_name if route_stops.exists() else 'Unknown'

        # Add to metrics list
        route_metrics.append({
            'route_no': route_no,
            'source': source,
            'destination': destination,
            'avg_epkm': avg_epkm,
            'total_revenue': total_revenue,
            'total_distance': total_distance,
            'trip_count': trip_count,
        })

    # Sort routes by EPKM (descending)
    profitable_routes = sorted(route_metrics, key=lambda x: x['avg_epkm'], reverse=True)

    # Identify top 10 most profitable and least profitable routes
    most_profitable = profitable_routes[:10] if len(profitable_routes) > 10 else profitable_routes
    least_profitable = profitable_routes[-10:][::-1] if len(profitable_routes) > 10 else profitable_routes[::-1]

    # Calculate overall statistics
    overall_revenue = sum(route['total_revenue'] for route in route_metrics)
    overall_distance = sum(route['total_distance'] for route in route_metrics)
    overall_epkm = overall_revenue / overall_distance if overall_distance > 0 else 0
    total_routes = len(route_metrics)

    # Prepare data for charts
    profitable_chart_data = {
        'labels': [route['route_no'] for route in most_profitable],
        'epkm_values': [route['avg_epkm'] for route in most_profitable],
        'revenue_values': [route['total_revenue'] for route in most_profitable],
    }

    unprofitable_chart_data = {
        'labels': [route['route_no'] for route in least_profitable],
        'epkm_values': [route['avg_epkm'] for route in least_profitable],
        'revenue_values': [route['total_revenue'] for route in least_profitable],
    }

    context = {
        'start_date': start_date,
        'end_date': end_date,
        'most_profitable': most_profitable,
        'least_profitable': least_profitable,
        'overall_revenue': overall_revenue,
        'overall_distance': overall_distance,
        'overall_epkm': overall_epkm,
        'total_routes': total_routes,
        'profitable_chart_data': json.dumps(profitable_chart_data),
        'unprofitable_chart_data': json.dumps(unprofitable_chart_data),
    }

    return render(request, 'route_analyzer/route_profitability.html', context)
