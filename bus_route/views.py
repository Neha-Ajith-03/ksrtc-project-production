import os
import json
import googlemaps
from geopy.geocoders import Nominatim
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseBadRequest
from django.conf import settings
from django.contrib import messages
from folium.plugins import MarkerCluster
import folium
import dotenv
from dotenv import load_dotenv
import polyline  # Required for decoding Google Maps encoded polylines
import pandas as pd
from datetime import datetime
from .models import Schedule, Route, Trip
from datetime import datetime
from django.shortcuts import render, get_object_or_404
# Load environment variables
env = dotenv.load_dotenv()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GMAP_API_KEY = os.getenv('GMAP_API_KEY')
if not GMAP_API_KEY:
    print("DEBUG: Google Maps API key not found. Please set the GMAP_API_KEY environment variable.")
else:
    print("DEBUG: GMAP_API_KEY loaded:", GMAP_API_KEY)

# Google Maps API setup
gmaps = googlemaps.Client(key=GMAP_API_KEY)
geolocator = Nominatim(user_agent="bus_stop_locator")

# Coordinates bounds for South India (customize as needed)
SOUTH_INDIA_LAT_MIN = 8.0
SOUTH_INDIA_LAT_MAX = 14.0
SOUTH_INDIA_LON_MIN = 76.0
SOUTH_INDIA_LON_MAX = 82.0

# Path to your geocoded stops JSON file
GEO_CACHE_FILE = 'bus_route/geocoded_stops.json'


# Function to check if coordinates are within South India region
def is_in_south_india(latitude, longitude):
    in_region = (SOUTH_INDIA_LAT_MIN <= latitude <= SOUTH_INDIA_LAT_MAX) and \
                (SOUTH_INDIA_LON_MIN <= longitude <= SOUTH_INDIA_LON_MAX)
    print(f"DEBUG: Checking if ({latitude}, {longitude}) is in South India: {in_region}")
    return in_region


# Function to load cached geocoded data from a JSON file
def load_geocoded_data():
    try:
        with open(GEO_CACHE_FILE, 'r') as f:
            data = json.load(f)
            print("DEBUG: Loaded cached geocoded data.")
            return data
    except FileNotFoundError:
        print("DEBUG: Cache file not found. Starting with empty cache.")
        return {}


# Function to geocode a bus stop, first checking the cache, then using Nominatim or Google Maps API
def geocode_stop_name(stop_name, cached_data):
    # Check if the stop is in cached data
    if stop_name in cached_data:
        print(f"DEBUG: Using cached data for {stop_name}")
        return cached_data[stop_name]['latitude'], cached_data[stop_name]['longitude']
    
    print(f"DEBUG: No cached data found for {stop_name}\n\n")
    return None, None

def create_map(bus_stops):
    if not bus_stops or len(bus_stops) < 2:
        print("DEBUG: Not enough bus stops provided to create map.")
        return None

    # Create a Folium map centered on a default location (adjust as needed)
    map_center = [8.4869, 76.9529]
    map = folium.Map(location=map_center, zoom_start=13)
    print(f"DEBUG: Creating map centered at {map_center}")

    # Add numbered markers for each bus stop in order
    marker_cluster = MarkerCluster().add_to(map)
    for index, stop in enumerate(bus_stops, start=1):
        lat = stop['latitude']
        lon = stop['longitude']
        popup_text = f"{index}. {stop['name']}"
        print(f"DEBUG: Adding marker for stop '{stop['name']}' as #{index} at ({lat}, {lon})")
        folium.Marker(
            [lat, lon],
            popup=popup_text,
            icon=folium.DivIcon(html=f"""<div style="font-size: 42pt; color:red"><b>{index}</b></div>""")
        ).add_to(marker_cluster)

    # Divide bus stops into segments of up to 20 stops (with one-stop overlap between segments)
    segment_size = 20
    segments = []
    i = 0
    while i < len(bus_stops):
        # For each segment, include up to segment_size stops
        segment = bus_stops[i:i + segment_size]
        # If not the first segment, ensure continuity by overlapping the first stop with the previous segment's last stop
        if i != 0 and segment:
            segment = [bus_stops[i - 1]] + segment
        segments.append(segment)
        # Move index forward by segment_size - 1 to have an overlap
        i += segment_size - 1

    # Define a cyclic list of colors for the route segments
    colors = ['blue', 'red', 'green', 'purple', 'orange', 'darkred', 'cadetblue', 'darkgreen', 'darkpurple', 'pink']

    # For each segment, request directions from Google Maps and add the polyline with a distinct color
    for seg_index, segment in enumerate(segments):
        # Extract latitude/longitude tuples for this segment
        waypoints = [(stop['latitude'], stop['longitude']) for stop in segment]
        if len(waypoints) < 2:
            print(f"DEBUG: Segment {seg_index + 1} has insufficient waypoints.")
            continue

        origin = waypoints[0]
        destination = waypoints[-1]
        intermediate_waypoints = waypoints[1:-1]

        try:
            print(f"DEBUG: Requesting directions for segment {seg_index + 1}: origin {origin}, destination {destination}, waypoints {intermediate_waypoints}")
            route = gmaps.directions(
                origin=origin,
                destination=destination,
                waypoints=intermediate_waypoints,
                mode="driving",
            )
            if route:
                overview_poly = route[0].get('overview_polyline', {}).get('points')
                if overview_poly:
                    print(f"DEBUG: Decoding polyline for segment {seg_index + 1}.")
                    decoded_points = polyline.decode(overview_poly)
                    color = colors[seg_index % len(colors)]
                    print(f"DEBUG: Drawing segment {seg_index + 1} with color {color}.")
                    folium.PolyLine(decoded_points, color=color, weight=2.5, opacity=1).add_to(map)
                else:
                    print(f"DEBUG: No overview polyline found for segment {seg_index + 1}.")
            else:
                print(f"DEBUG: No route found for segment {seg_index + 1}.")
        except Exception as e:
            print(f"DEBUG: Exception while retrieving route for segment {seg_index + 1}: {e}")

    return map




def create_enhanced_map(bus_stops):
    """
    Create a Google Maps visualization for the bus stops and route using Directions API
    with proper handling of routes with many stops
    """
    if not bus_stops or len(bus_stops) < 2:
        return None
    
    # Get the Google Maps API key from settings
    gmap_api_key = getattr(settings, 'GMAP_API_KEY', '') or GMAP_API_KEY
    
    # Convert bus stops to JSON for JavaScript
    import json
    stops_json = json.dumps([{
        'name': stop['name'],
        'lat': stop['latitude'],
        'lng': stop['longitude'],
        'sequence': stop.get('sequence', 0),
        'is_fare_stage': stop.get('is_fare_stage', False),
        'revenue': float(stop.get('revenue', 0))
    } for stop in bus_stops])
    
    # Generate HTML for Google Maps
    map_html = f"""
    <div id="map" style="height: 600px; width: 100%; border-radius: 10px;"></div>
    <script>
        // Initialize the map once the Google Maps API is loaded
        function initMap() {{
            // Parse the bus stops data
            const busStops = {stops_json};
            
            // Check if we have stops to display
            if (busStops.length < 1) {{
                console.error('No bus stops to display');
                return;
            }}
            
            // Create a map centered on the first stop
            const map = new google.maps.Map(document.getElementById('map'), {{
                center: {{ lat: busStops[0].lat, lng: busStops[0].lng }},
                zoom: 12,
                mapTypeId: google.maps.MapTypeId.ROADMAP,
                mapTypeControl: true,
                streetViewControl: true,
                fullscreenControl: true,
                styles: [
                    {{
                        "featureType": "poi",
                        "elementType": "labels",
                        "stylers": [{{ "visibility": "off" }}]
                    }}
                ]
            }});
            
            // Prepare bounds to include all stops
            const bounds = new google.maps.LatLngBounds();
            
            // Create info window for markers
            const infoWindow = new google.maps.InfoWindow();
            
            // Add markers for each bus stop
            busStops.forEach((stop, index) => {{
                // Create marker position
                const position = {{ lat: stop.lat, lng: stop.lng }};
                
                // Extend bounds to include this position
                bounds.extend(position);
                
                // Create marker with different icon based on whether it's a fare stage
                const marker = new google.maps.Marker({{
                    position: position,
                    map: map,
                    title: `${{index + 1}}. ${{stop.name}}`,
                    label: `${{index + 1}}`,
                    icon: {{
                        url: stop.is_fare_stage ? 
                            'https://maps.google.com/mapfiles/ms/icons/red-dot.png' : 
                            'https://maps.google.com/mapfiles/ms/icons/blue-dot.png'
                    }}
                }});
                
                // Create content for info window
                const contentString = `
                    <div>
                        <h5 style="margin: 0; padding: 0; font-size: 16px;">${{index + 1}}. ${{stop.name}}</h5>
                        ${{stop.is_fare_stage ? '<p style="margin: 5px 0; color: red;">Fare Stage</p>' : ''}}
                        ${{stop.revenue > 0 ? `<p style="margin: 5px 0;">Revenue: ₹${{stop.revenue.toFixed(2)}}</p>` : ''}}
                        <p style="margin: 5px 0; font-size: 12px;">Coordinates: ${{stop.lat.toFixed(6)}}, ${{stop.lng.toFixed(6)}}</p>
                    </div>
                `;
                
                // Add click event to show info
                marker.addListener('click', () => {{
                    infoWindow.setContent(contentString);
                    infoWindow.open(map, marker);
                }});
            }});
            
            // Fit map to show all markers
            map.fitBounds(bounds);
            
            // Add legend
            const legend = document.createElement('div');
            legend.className = 'legend';
            legend.style.cssText = 'background: white; padding: 10px; margin: 10px; border-radius: 5px; box-shadow: 0 2px 6px rgba(0,0,0,0.3);';
            
            legend.innerHTML = `
                <div style="margin-bottom: 5px;"><strong>Legend</strong></div>
                <div style="display: flex; align-items: center; margin-bottom: 5px;">
                    <img src="https://maps.google.com/mapfiles/ms/icons/blue-dot.png" width="20" height="20" style="margin-right: 5px;">
                    <span>Regular Stop</span>
                </div>
                <div style="display: flex; align-items: center;">
                    <img src="https://maps.google.com/mapfiles/ms/icons/red-dot.png" width="20" height="20" style="margin-right: 5px;">
                    <span>Fare Stage</span>
                </div>
            `;
            
            // Add legend to the map
            map.controls[google.maps.ControlPosition.RIGHT_BOTTOM].push(legend);
            
            // Connect stops with road segments by breaking into pairs
            async function connectStopsAlongRoads() {{
                if (busStops.length < 2) return;
                
                const directionsService = new google.maps.DirectionsService();
                
                // Process pairs of stops (from A to B, B to C, C to D, etc.)
                for (let i = 0; i < busStops.length - 1; i++) {{
                    const startStop = busStops[i];
                    const endStop = busStops[i + 1];
                    
                    try {{
                        // Request directions between this pair of stops
                        const result = await new Promise((resolve, reject) => {{
                            directionsService.route(
                                {{
                                    origin: {{ lat: startStop.lat, lng: startStop.lng }},
                                    destination: {{ lat: endStop.lat, lng: endStop.lng }},
                                    travelMode: google.maps.TravelMode.DRIVING,
                                }},
                                (response, status) => {{
                                    if (status === 'OK') {{
                                        resolve(response);
                                    }} else {{
                                        reject(new Error(`Directions request failed: ${{status}}`));
                                    }}
                                }}
                            );
                        }});
                        
                        // Extract the route
                        const route = result.routes[0];
                        
                        // Draw this segment with a custom polyline
                        const path = route.overview_path;
                        const routeSegment = new google.maps.Polyline({{
                            path: path,
                            geodesic: true,
                            strokeColor: '#4285F4',
                            strokeOpacity: 0.8,
                            strokeWeight: 5,
                            map: map
                        }});
                        
                        console.log(`Successfully drew segment from stop ${{i}} to ${{i+1}}`);
                        
                        // Add a small delay between requests to avoid rate limiting
                        await new Promise(resolve => setTimeout(resolve, 300));
                        
                    }} catch (error) {{
                        console.error(`Error connecting stops ${{i}} and ${{i+1}}: ${{error.message}}`);
                        
                        // If the directions service fails, draw a straight line as fallback
                        const straightLine = new google.maps.Polyline({{
                            path: [
                                {{ lat: startStop.lat, lng: startStop.lng }},
                                {{ lat: endStop.lat, lng: endStop.lng }}
                            ],
                            geodesic: true,
                            strokeColor: '#FF0000', // Red for fallback lines
                            strokeOpacity: 0.6,
                            strokeWeight: 4,
                            map: map
                        }});
                    }}
                }}
            }}
            
            // Connect all stops along roads
            connectStopsAlongRoads().catch(error => {{
                console.error('Failed to connect stops along roads:', error);
                
                // Fallback to a single polyline for the entire route
                const routePath = busStops.map(stop => ({{ lat: stop.lat, lng: stop.lng }}));
                const routeLine = new google.maps.Polyline({{
                    path: routePath,
                    geodesic: true,
                    strokeColor: '#3388ff',
                    strokeOpacity: 0.8,
                    strokeWeight: 4,
                    map: map
                }});
            }});
        }}
    </script>
    <script src="https://maps.googleapis.com/maps/api/js?key={gmap_api_key}&callback=initMap"></script>
    """
    
    return map_html

def bus_route_view(request):
    print("DEBUG: bus_route_view called with method:", request.method)
    cached_data = load_geocoded_data()  # Load existing cached geocoded data
    print("DEBUG: Cached data loaded:", cached_data)

    if request.method == 'POST':
        # Get bus stop names from the form
        stop_names = request.POST.get('stop_names')
        print("DEBUG: Received stop names from form:", stop_names)
        bus_stop_names = [name.strip() for name in stop_names.split(',')]
        print("DEBUG: Parsed bus stop names:", bus_stop_names)
        bus_stops = []  # List to store geocoded results

        for stop_name in bus_stop_names:
            if stop_name:  # Ensure the stop name is not empty
                print(f"DEBUG: Processing stop name: {stop_name}")
                lat, lon = geocode_stop_name(stop_name, cached_data)
                if lat is not None and lon is not None:
                    print(f"DEBUG: Adding bus stop '{stop_name}' with coordinates: ({lat}, {lon})")
                    bus_stops.append({'name': stop_name, 'latitude': lat, 'longitude': lon})
                else:
                    print(f"DEBUG: Geocoding failed for stop: {stop_name}")

        if not bus_stops:
            # If no valid bus stops were found, display an error message
            print("DEBUG: No valid bus stops were found.")
            return render(request, 'bus_route/bus_route_form.html', {
                'error_message': 'No valid bus stops were found. Please try again with different names.'
            })

        # Create the map with bus stops and route
        map_object = create_map(bus_stops)
        if not map_object:
            print("DEBUG: Map creation failed due to insufficient bus stops.")
            return render(request, 'bus_route/bus_route_form.html', {
                'error_message': 'Not enough bus stops to create a route. At least two stops are required.'
            })

        map_html = map_object._repr_html_()  # Convert the folium map to HTML for embedding
        print("DEBUG: Map created successfully. Rendering map HTML.")
        return render(request, 'bus_route/bus_route_map.html', {'map_html': map_html})

    print("DEBUG: Rendering bus route form.")
    return render(request, 'bus_route/bus_route_form.html')

def get_route_details(request):
    if request.method != 'GET':
        return HttpResponseBadRequest("Only GET method is allowed.")
    
    schedule_no = request.GET.get('schedule_no')
    trip_no = request.GET.get('trip_no')

    if not schedule_no or not trip_no:
        return HttpResponseBadRequest("Missing required parameters: schedule_no and trip_no.")
    
    try:
        trip_no = int(trip_no)
    except ValueError:
        return HttpResponseBadRequest("Invalid trip_no parameter. It must be an integer.")
    
    try:
        # Ensure schedule_no is uppercase as per the model's save method.
        schedule = Schedule.objects.get(schedule_no=schedule_no.upper(), trip_no=trip_no)
    except Schedule.DoesNotExist:
        return JsonResponse({"error": "Schedule not found."}, status=404)
    
    # Retrieve all Route objects that match the schedule's route_no, ordered by the sequence number.
    routes = Route.objects.filter(route_no=schedule.route_no.upper()).order_by('order_sequence')
    
    # Prepare the response data with each key as the sequence number.
    data = {}
    for route in routes:
        data[route.order_sequence] = {
            "stop_name": route.stop_name,
            "latitude": route.stop_latitude,
            "longitude": route.stop_longitude,
        }
    
    return JsonResponse(data)


def bus_route_by_schedule_view(request):
    if request.method == 'POST':
        # Get schedule and trip numbers from the form
        schedule_no = request.POST.get('schedule_no')
        trip_no = request.POST.get('trip_no')
        if not schedule_no or not trip_no:
            return render(request, 'bus_route/bus_route_schedule_form.html', {
                'error_message': 'Please provide both Schedule No and Trip No.'
            })
        try:
            trip_no_int = int(trip_no)
        except ValueError:
            return render(request, 'bus_route/bus_route_schedule_form.html', {
                'error_message': 'Trip No must be an integer.'
            })
        
        # Retrieve the schedule (ensure schedule_no is uppercase as in your model)
        try:
            schedule = Schedule.objects.get(schedule_no=schedule_no.upper(), trip_no=trip_no_int)
        except Schedule.DoesNotExist:
            return render(request, 'bus_route/bus_route_schedule_form.html', {
                'error_message': 'Schedule not found.'
            })
        
        # Get all Route objects for the schedule's route, ordered by sequence number
        routes = Route.objects.filter(route_no=schedule.route_no.upper()).order_by('order_sequence')
        if not routes:
            return render(request, 'bus_route/bus_route_schedule_form.html', {
                'error_message': 'No route stops found for this schedule.'
            })
        
        # Build bus_stops list (each with name, latitude, longitude)
        bus_stops = []
        for route in routes:
            bus_stops.append({
                'name': route.stop_name,
                'latitude': route.stop_latitude,
                'longitude': route.stop_longitude,
                'is_fare_stage': route.fare_stage,
                'sequence': route.order_sequence
            })
        
        # Create the map with bus stops and route using enhanced map
        map_html = create_enhanced_map(bus_stops)
        if not map_html:
            return render(request, 'bus_route/bus_route_schedule_form.html', {
                'error_message': 'Not enough bus stops to create a route. At least two stops are required.'
            })
        
        # Render the enhanced map
        return render(request, 'bus_route/bus_route_map.html', {'map_html': map_html})
    
    # For GET requests, simply render the schedule input form
    return render(request, 'bus_route/bus_route_schedule_form.html')


def schedule_list_view(request):
    """View to display a list of all available schedules"""
    # Get all schedules first
    all_schedules = Schedule.objects.values(
        'schedule_no', 'source', 'destination', 'via', 'service_type', 'route_no', 'start_time', 'end_time'
    ).order_by('schedule_no')
    
    # Use a dictionary to track unique schedule numbers
    unique_schedules = {}
    for schedule in all_schedules:
        schedule_no = schedule['schedule_no']
        if schedule_no not in unique_schedules:
            unique_schedules[schedule_no] = schedule
    
    # Convert the dictionary values to a list
    schedules = list(unique_schedules.values())
    
    context = {
        'schedules': schedules
    }
    
    return render(request, 'bus_route/schedule_list.html', context)
def trip_list_view(request, schedule_no):
    """View to display trips for a specific schedule with date filtering"""
    # Ensure schedule_no is uppercase
    schedule_no = schedule_no.upper()

    # Get date from query parameters, default to today if not provided
    selected_date = request.GET.get('date', '2024-08-15')

    # Get all trips for this schedule_no and selected date
    trips = Trip.objects.filter(schedule_no=schedule_no, date=selected_date)
    
    # Get all schedules associated with these trips
    trip_schedules = []
    for trip in trips:
        try:
            schedule = Schedule.objects.get(schedule_no=schedule_no, trip_no=trip.trip_no)
            # Create a combined data structure with schedule and trip information
            combined_data = {
                'route_no': schedule.route_no,
                'trip_no': trip.trip_no,
                'date': trip.date,
                'source': schedule.source,
                'via': schedule.via,
                'destination': schedule.destination,
                'start_time': schedule.start_time,
                'end_time': schedule.end_time,
                'trip_km': schedule.trip_km,
                'revenue': trip.revenue,
                'schedule_no': schedule_no
            }
            trip_schedules.append(combined_data)
        except Schedule.DoesNotExist:
            continue
    
    # Sort by trip_no
    trip_schedules.sort(key=lambda x: x['trip_no'])
    
    # Get a list of unique dates that have trips for this schedule
    all_dates = Trip.objects.filter(schedule_no=schedule_no).values_list('date', flat=True).distinct().order_by('-date')

    # Get unique route numbers for this schedule
    routes = Schedule.objects.filter(schedule_no=schedule_no).values_list('route_no', flat=True).distinct().order_by('route_no')

    context = {
        'schedule_no': schedule_no,
        'trips': trip_schedules,
        'selected_date': selected_date,
        'all_dates': all_dates,
        'routes': routes
    }

    return render(request, 'bus_route/trip_list.html', context)

def trip_map_view(request, schedule_no, trip_no,route_no):
    """View to display the map for a specific trip"""
    # Ensure schedule_no is uppercase
    schedule_no = schedule_no.upper()
    
    try:
        # Get schedule details for this specific trip
        schedule = Schedule.objects.get(schedule_no=schedule_no, trip_no=trip_no)
        
        # Get trip data if available
        trip = Trip.objects.filter(schedule_no=schedule_no, trip_no=trip_no).order_by('-date').first()
        
        # Get route stops
        routes = Route.objects.filter(route_no=route_no).order_by('order_sequence')
        
        if not routes:
            messages.error(request, 'No route stops found for this schedule.')
            return redirect('trip_list_view', schedule_no=schedule_no)
        
        # Build bus_stops list
        bus_stops = []
        for route in routes:
            bus_stops.append({
                'name': route.stop_name,
                'latitude': route.stop_latitude,
                'longitude': route.stop_longitude,
                'is_fare_stage': route.fare_stage,
                'sequence': route.order_sequence
            })
        
        # Create map
        map_html = create_enhanced_map(bus_stops)
        if not map_html:
            messages.error(request, 'Not enough bus stops to create a route.')
            return redirect('trip_list_view', schedule_no=schedule_no)
        context = {
            'map_html': map_html,
            'schedule': schedule,
            'trip': trip,
            'route_no':route_no
        }
        
        return render(request, 'bus_route/trip_map.html', context)
    
    except Schedule.DoesNotExist:
        messages.error(request, f'Schedule {schedule_no} Trip {trip_no} not found.')
        return redirect('schedule_list_view')

def main_dashboard_view(request):
    """View for the main dashboard page"""
    return render(request, 'main_dashboard.html')


def schedule_submit_view(request):
    """View for submitting new schedule data"""
    if request.method == 'POST':
        # Extract form data
        route_no = request.POST.get('route_no', '').strip()
        schedule_no = request.POST.get('schedule_no', '').strip()
        trip_no = request.POST.get('trip_no', '')
        service_type = request.POST.get('service_type', '').strip()
        source = request.POST.get('source', '').strip()
        destination = request.POST.get('destination', '').strip()
        via = request.POST.get('via', '').strip() or None
        start_time = request.POST.get('start_time', '')
        end_time = request.POST.get('end_time', '')
        date_str = request.POST.get('date', '')
        revenue = request.POST.get('revenue', '') or None
        distance_km = request.POST.get('distance_km', '') or None
        
        # Basic validation
        if not all([route_no, schedule_no, trip_no, service_type, source, destination, start_time, end_time, date_str]):
            return render(request, 'bus_route/schedule_submit.html', {
                'error_message': 'Please fill in all required fields.'
            })
        
        try:
            # Convert numeric fields
            trip_no = int(trip_no)
            if revenue:
                revenue = float(revenue)
            if distance_km:
                distance_km = float(distance_km)
            
            # Parse date
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # Create or update Schedule
            schedule, created = Schedule.objects.update_or_create(
                schedule_no=schedule_no,
                trip_no=trip_no,
                defaults={
                    'route_no': route_no,
                    'source': source,
                    'destination': destination,
                    'via': via,
                    'service_type': service_type,
                    'start_time': start_time,
                    'end_time': end_time,
                }
            )
            
            # Create or update Trip
            trip, trip_created = Trip.objects.update_or_create(
                date=date_obj,
                schedule_no=schedule,
                trip_no=trip_no,
                defaults={
                    'revenue': revenue,
                    'distance_km': distance_km,
                }
            )
            
            return render(request, 'bus_route/schedule_submit.html', {
                'success_message': f"Schedule {schedule_no} - Trip {trip_no} successfully {'created' if created else 'updated'}."
            })
            
        except ValueError as e:
            return render(request, 'bus_route/schedule_submit.html', {
                'error_message': f'Invalid data format: {str(e)}'
            })
        except Exception as e:
            return render(request, 'bus_route/schedule_submit.html', {
                'error_message': f'Error saving data: {str(e)}'
            })
    
    return render(request, 'bus_route/schedule_submit.html')


def fetch_trip_revenue_data(schedule_no, trip_no, date=None):
    """Fetch revenue data for a specific trip (placeholder function)"""
    # This would normally query BigQuery or another data source
    # For now, return an empty DataFrame
    return pd.DataFrame()


def calculate_fare_stage_revenue(schedule_no, trip_no, date=None):
    """Calculate revenue for each fare stage (placeholder function)"""
    # This would normally perform calculations based on BigQuery data
    # For now, return an empty DataFrame
    return pd.DataFrame()


def enhanced_schedule_analyzer_view(request):
    """View for enhanced schedule analysis"""
    if request.method == 'POST':
        # Get form data
        schedule_no = request.POST.get('schedule_no')
        trip_no = request.POST.get('trip_no')
        date = request.POST.get('date', None)
        
        if not schedule_no or not trip_no:
            return render(request, 'bus_route/enhanced_schedule_form.html', {
                'error_message': 'Please provide both Schedule No and Trip No.'
            })
        
        try:
            trip_no_int = int(trip_no)
        except ValueError:
            return render(request, 'bus_route/enhanced_schedule_form.html', {
                'error_message': 'Trip No must be an integer.'
            })
        
        # Retrieve the schedule
        try:
            schedule = Schedule.objects.get(schedule_no=schedule_no.upper(), trip_no=trip_no_int)
        except Schedule.DoesNotExist:
            return render(request, 'bus_route/enhanced_schedule_form.html', {
                'error_message': 'Schedule not found.'
            })
        
        # Get route data
        routes = Route.objects.filter(route_no=schedule.route_no.upper()).order_by('order_sequence')
        if not routes:
            return render(request, 'bus_route/enhanced_schedule_form.html', {
                'error_message': 'No route stops found for this schedule.'
            })
        
        # Get trip data (from database if exists)
        trip = None
        try:
            if date:
                parsed_date = datetime.strptime(date, '%Y-%m-%d').date()
                trip = Trip.objects.get(date=parsed_date, schedule_no=schedule, trip_no=trip_no_int)
            else:
                # Get most recent trip
                trip = Trip.objects.filter(schedule_no=schedule, trip_no=trip_no_int).order_by('-date').first()
        except Trip.DoesNotExist:
            pass
        
        # Fetch revenue data (dummy function for now)
        try:
            revenue_data = fetch_trip_revenue_data(schedule_no, trip_no, date)
            fare_stage_data = calculate_fare_stage_revenue(schedule_no, trip_no, date)
        except Exception as e:
            # If there's an error, use existing data if available
            revenue_data = pd.DataFrame()
            fare_stage_data = pd.DataFrame()
            if trip:
                print(f"Using existing trip data due to error: {str(e)}")
            else:
                print(f"Error fetching data: {str(e)}")
        
        # Calculate EPKM
        if not revenue_data.empty and 'REVENUE' in revenue_data.columns and 'DISTANCE' in revenue_data.columns:
            total_revenue = revenue_data['REVENUE'].sum()
            total_distance = revenue_data['DISTANCE'].mean() * len(routes)
            epkm = total_revenue / total_distance if total_distance > 0 else 0
        elif trip and trip.revenue is not None and trip.distance_km is not None and trip.distance_km > 0:
            # Fall back to trip data if available
            total_revenue = trip.revenue
            total_distance = trip.distance_km
            epkm = trip.epkm or 0
        else:
            total_revenue = 0
            total_distance = 0
            epkm = 0
        
        # Build bus_stops list with revenue data
        bus_stops = []
        for route in routes:
            stop_data = {
                'name': route.stop_name,
                'latitude': route.stop_latitude,
                'longitude': route.stop_longitude,
                'is_fare_stage': route.fare_stage,
                'sequence': route.order_sequence,
                'revenue': 0  # Default value
            }
            
            # Add revenue data if available
            if not revenue_data.empty and 'TO_STOP_NAME' in revenue_data.columns and 'REVENUE' in revenue_data.columns:
                stop_revenue = revenue_data[revenue_data['TO_STOP_NAME'] == route.stop_name]['REVENUE'].sum()
                stop_data['revenue'] = stop_revenue
            
            bus_stops.append(stop_data)
        
        # Create map
        map_html = create_enhanced_map(bus_stops)
        if not map_html:
            return render(request, 'bus_route/enhanced_schedule_form.html', {
                'error_message': 'Not enough bus stops to create a route.'
            })
        
        # Process fare stage data for charts
        fare_stages = []
        if not fare_stage_data.empty:
            for index, row in fare_stage_data.iterrows():
                fare_stages.append({
                    'from': row.get('FROM_STOP_NAME', ''),
                    'to': row.get('TO_STOP_NAME', ''),
                    'revenue': row.get('REVENUE', 0),
                    'passengers': row.get('PASSENGERS', 0)
                })
        
        # Prepare data for the template
        context = {
            'map_html': map_html,
            'schedule': schedule,
            'trip': trip,
            'bus_stops': bus_stops,
            'epkm': epkm,
            'total_revenue': total_revenue,
            'total_distance': total_distance,
            'fare_stages': fare_stages,
            'schedule_no': schedule_no,
            'trip_no': trip_no
        }
    
        return render(request, 'bus_route/enhanced_schedule_analysis.html', context)
    
    # For GET requests, render the form
    return render(request, 'bus_route/enhanced_schedule_form.html')
# Add this function to your views.py file



# Add this to your views.py file



# In bus_route/views.py

from django.http import JsonResponse
from datetime import datetime
from .models import Trip, Schedule
from django.db.models import Sum

# In bus_route/views.py

from django.http import JsonResponse
from datetime import datetime, timedelta
from .models import Trip
from django.db.models import Sum

def revenue_analysis(request):
    """
    API endpoint to fetch revenue data for selected schedules within a date range
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Only GET method is allowed'}, status=405)
    
    # Get query parameters
    schedule_no = request.GET.get('schedule_no', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    
    # Validate parameters
    if not start_date or not end_date:
        return JsonResponse({'error': 'Date range is required'}, status=400)
    
    try:
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Invalid date format. Use YYYY-MM-DD'}, status=400)
    
    # Build date list for the entire range
    date_list = []
    current_date = start_date_obj
    while current_date <= end_date_obj:
        date_list.append(current_date.strftime('%Y-%m-%d'))
        current_date += timedelta(days=1)
    
    result_data = []
    
    # Handle 'all' schedules case
    if schedule_no.lower() == 'all':
        # Get all schedules that have trips in the date range
        schedules_with_trips = Trip.objects.filter(
            date__gte=start_date_obj,
            date__lte=end_date_obj
        ).values_list('schedule_no', flat=True).distinct()
        
        # Process each schedule
        for schedule in schedules_with_trips:
            schedule_data = process_schedule_revenue(schedule, start_date_obj, end_date_obj, date_list)
            if schedule_data:
                result_data.append(schedule_data)
    else:
        # Process single schedule
        schedule_data = process_schedule_revenue(schedule_no, start_date_obj, end_date_obj, date_list)
        if schedule_data:
            result_data.append(schedule_data)
    
    return JsonResponse({'data': result_data})

def process_schedule_revenue(schedule_no, start_date, end_date, date_list):
    """Helper function to process revenue data for a specific schedule"""
    # Query for daily revenue for this schedule
    daily_revenues = Trip.objects.filter(
        schedule_no=schedule_no,
        date__gte=start_date,
        date__lte=end_date
    ).values('date').annotate(total_revenue=Sum('revenue'))
    
    # If no data, return None
    if not daily_revenues.exists():
        return None
    
    # Create a lookup dictionary for quick access
    revenue_lookup = {
        revenue_data['date'].strftime('%Y-%m-%d'): revenue_data['total_revenue'] 
        for revenue_data in daily_revenues
    }
    
    # Build the revenue list for all dates in the range
    revenue_list = []
    for date_str in date_list:
        # Use the revenue if available, otherwise null (not 0, to create gaps in the chart)
        revenue_list.append(float(revenue_lookup.get(date_str, 0)) if date_str in revenue_lookup else None)
    
    return {
        'schedule': schedule_no,
        'dates': date_list,
        'revenues': revenue_list
    }

# Add this function to your views.py file

from django.http import JsonResponse
from datetime import datetime, timedelta
from .models import Trip
from django.db.models import Sum

def trip_revenue_analysis(request):
    """
    API endpoint to fetch revenue data for selected trips within a date range
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Only GET method is allowed'}, status=405)
    
    # Get query parameters
    schedule_no = request.GET.get('schedule_no', '')
    trip_no = request.GET.get('trip_no', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    
    # Validate parameters
    if not schedule_no:
        return JsonResponse({'error': 'Schedule number is required'}, status=400)
    
    if not start_date or not end_date:
        return JsonResponse({'error': 'Date range is required'}, status=400)
    
    try:
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Invalid date format. Use YYYY-MM-DD'}, status=400)
    
    # Build date list for the entire range
    date_list = []
    current_date = start_date_obj
    while current_date <= end_date_obj:
        date_list.append(current_date.strftime('%Y-%m-%d'))
        current_date += timedelta(days=1)
    
    result_data = []
    
    # Handle 'all' trips case
    if trip_no.lower() == 'all':
        # Get all trips for this schedule in the database
        trips_with_revenue = Trip.objects.filter(
            schedule_no=schedule_no,
            date__gte=start_date_obj,
            date__lte=end_date_obj
        ).values_list('trip_no', flat=True).distinct()
        
        # Process each trip
        for trip in trips_with_revenue:
            trip_data = process_trip_revenue(schedule_no, trip, start_date_obj, end_date_obj, date_list)
            if trip_data:
                result_data.append(trip_data)
    else:
        # Process single trip
        try:
            trip_no_int = int(trip_no)
            trip_data = process_trip_revenue(schedule_no, trip_no_int, start_date_obj, end_date_obj, date_list)
            if trip_data:
                result_data.append(trip_data)
        except ValueError:
            return JsonResponse({'error': 'Invalid trip number'}, status=400)
    
    return JsonResponse({'data': result_data})

def process_trip_revenue(schedule_no, trip_no, start_date, end_date, date_list):
    """Helper function to process revenue data for a specific trip"""
    # Query for daily revenue for this trip
    trip_revenues = Trip.objects.filter(
        schedule_no=schedule_no,
        trip_no=trip_no,
        date__gte=start_date,
        date__lte=end_date
    ).values('date', 'revenue')
    
    # If no data, return None
    if not trip_revenues.exists():
        return None
    
    # Create a lookup dictionary for quick access
    revenue_lookup = {
        rev_data['date'].strftime('%Y-%m-%d'): rev_data['revenue']
        for rev_data in trip_revenues
    }
    
    # Build the revenue list for all dates in the range
    revenue_list = []
    for date_str in date_list:
        # Use the revenue if available, otherwise null (not 0, to create gaps in the chart)
        revenue_list.append(float(revenue_lookup.get(date_str, 0)) if date_str in revenue_lookup else None)
    
    return {
        'trip': trip_no,
        'dates': date_list,
        'revenues': revenue_list
    }