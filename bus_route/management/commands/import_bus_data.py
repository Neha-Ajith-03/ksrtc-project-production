from django.core.management.base import BaseCommand
from bus_route.models import Route, Schedule, Trip
from datetime import datetime, time

class Command(BaseCommand):
    help = 'Import bus schedule and route data from CSV files'

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting data import...")
        
        # Import schedules
        self.import_schedules()
        
        # Import routes - East Fort to Kattakada
        self.import_eastfort_to_kattakada_routes()
        
        # Import routes - Kattakada to East Fort
        self.import_kattakada_to_eastfort_routes()
        
        self.stdout.write(self.style.SUCCESS("Data import completed successfully!"))
    
    def import_schedules(self):
        self.stdout.write("Importing schedules...")
        
        # Define the schedule data from image 1
        schedule_data = [
            {
                'service_type': 'CITY FAST PASSENGER',
                'schedule_no': 'S026001',
                'trip_no': 1,
                'start_time': '7:10',
                'from_stop': 'EASTFORT',
                'via': 'VALIYARATHALA OORUTTAMBALAM',
                'to_stop': 'KATTAKADA',
                'end_time': '8:10',
                'distance': 23,
                'route_name': '1518E'
            },
            {
                'service_type': 'CITY FAST PASSENGER',
                'schedule_no': 'S026001',
                'trip_no': 2,
                'start_time': '8:40',
                'from_stop': 'KATTAKADA',
                'via': 'OORUTTAMBALAM VALIYARATHALA',
                'to_stop': 'EASTFORT',
                'end_time': '9:40',
                'distance': 23,
                'route_name': '1542E'
            },
            {
                'service_type': 'CITY FAST PASSENGER',
                'schedule_no': 'S026001',
                'trip_no': 3,
                'start_time': '9:50',
                'from_stop': 'EASTFORT',
                'via': 'VALIYARATHALA OORUTTAMBALAM',
                'to_stop': 'KATTAKADA',
                'end_time': '10:50',
                'distance': 23,
                'route_name': '1518E'
            },
            {
                'service_type': 'CITY FAST PASSENGER',
                'schedule_no': 'S026001',
                'trip_no': 4,
                'start_time': '11:20',
                'from_stop': 'KATTAKADA',
                'via': 'OORUTTAMBALAM VALIYARATHALA',
                'to_stop': 'EASTFORT',
                'end_time': '12:20',
                'distance': 23,
                'route_name': '1542E'
            },
            {
                'service_type': 'CITY FAST PASSENGER',
                'schedule_no': 'S026001',
                'trip_no': 5,
                'start_time': '12:30',
                'from_stop': 'EASTFORT',
                'via': 'VALIYARATHALA OORUTTAMBALAM',
                'to_stop': 'KATTAKADA',
                'end_time': '13:30',
                'distance': 23,
                'route_name': '1518E'
            },
            {
                'service_type': 'CITY FAST PASSENGER',
                'schedule_no': 'S026001',
                'trip_no': 6,
                'start_time': '14:00',
                'from_stop': 'KATTAKADA',
                'via': 'OORUTTAMBALAM VALIYARATHALA',
                'to_stop': 'EASTFORT',
                'end_time': '15:00',
                'distance': 23,
                'route_name': '1542E'
            },
            {
                'service_type': 'CITY FAST PASSENGER',
                'schedule_no': 'S026001',
                'trip_no': 7,
                'start_time': '15:10',
                'from_stop': 'EASTFORT',
                'via': 'VALIYARATHALA OORUTTAMBALAM',
                'to_stop': 'KATTAKADA',
                'end_time': '16:10',
                'distance': 23,
                'route_name': '1518E'
            },
            {
                'service_type': 'CITY FAST PASSENGER',
                'schedule_no': 'S026001',
                'trip_no': 8,
                'start_time': '16:40',
                'from_stop': 'KATTAKADA',
                'via': 'OORUTTAMBALAM VALIYARATHALA',
                'to_stop': 'EASTFORT',
                'end_time': '17:40',
                'distance': 23,
                'route_name': '1542E'
            }
        ]
        
        # Insert schedules into the database
        for item in schedule_data:
            # Parse time strings to time objects
            start_time = datetime.strptime(item['start_time'], '%H:%M').time()
            end_time = datetime.strptime(item['end_time'], '%H:%M').time()
            
            # Create or update schedule
            schedule, created = Schedule.objects.update_or_create(
                schedule_no=item['schedule_no'],
                trip_no=item['trip_no'],
                defaults={
                    'route_no': item['route_name'],
                    'service_type': item['service_type'],
                    'source': item['from_stop'],
                    'destination': item['to_stop'],
                    'via': item['via'],
                    'start_time': start_time,
                    'end_time': end_time
                }
            )
            
            # Create a sample trip for today
            trip, created = Trip.objects.update_or_create(
                date=datetime.now().date(),
                schedule_no=schedule,
                trip_no=item['trip_no'],
                defaults={
                    'distance_km': item['distance'],
                    'revenue': item['distance'] * 100  # Dummy revenue calculation
                }
            )
            
            self.stdout.write(f"Added schedule {schedule.schedule_no}-{schedule.trip_no} ({item['from_stop']} to {item['to_stop']})")
    
    def import_eastfort_to_kattakada_routes(self):
        self.stdout.write("Importing East Fort to Kattakada routes...")
        
        # Route data from image 2
        route_data = [
            {'seq': 1, 'name': 'EASTFORT SOUTH STAND 2', 'lat': 8.482314, 'lng': 76.947991, 'fare_stage': True},
            {'seq': 2, 'name': 'THAMPANOOR BUS STAND', 'lat': 8.487791, 'lng': 76.951686, 'fare_stage': False},
            {'seq': 3, 'name': 'KILLIPALAM', 'lat': 8.481154, 'lng': 76.95703, 'fare_stage': False},
            {'seq': 4, 'name': 'PRS', 'lat': 8.481424, 'lng': 76.959537, 'fare_stage': False},
            {'seq': 5, 'name': 'KARAMANA IN', 'lat': 8.482042, 'lng': 76.966706, 'fare_stage': True},
            {'seq': 6, 'name': 'NEERAMANKARA', 'lat': 8.476539, 'lng': 76.973123, 'fare_stage': False},
            {'seq': 7, 'name': 'KAIMANAM JUNCTION', 'lat': 8.472742, 'lng': 76.978281, 'fare_stage': False},
            {'seq': 8, 'name': 'CENTRAL WORKS', 'lat': 8.471531, 'lng': 76.979728, 'fare_stage': False},
            {'seq': 9, 'name': 'PAPPANAMCODE', 'lat': 8.470414, 'lng': 76.981079, 'fare_stage': True},
            {'seq': 10, 'name': 'KARAKKAMANDAPAM JUNCTION', 'lat': 8.464406, 'lng': 76.991042, 'fare_stage': False},
            {'seq': 11, 'name': 'OLD KARAKKAMANDAPAM', 'lat': 8.461097, 'lng': 76.994733, 'fare_stage': False},
            {'seq': 12, 'name': 'VELLAYANI', 'lat': 8.456897, 'lng': 77.000836, 'fare_stage': False},
            {'seq': 13, 'name': 'NEMOM', 'lat': 8.453748, 'lng': 77.004106, 'fare_stage': True},
            {'seq': 14, 'name': 'NEMOM SCHOOL', 'lat': 8.451858, 'lng': 77.007636, 'fare_stage': False},
            {'seq': 15, 'name': 'PRAVACHAMBALAM', 'lat': 8.449132, 'lng': 77.012767, 'fare_stage': False},
            {'seq': 16, 'name': 'ARIKKADAMUKKU', 'lat': 8.449552, 'lng': 77.014861, 'fare_stage': False},
            {'seq': 17, 'name': 'NETHAJI NAGAR', 'lat': 8.449646, 'lng': 77.01963, 'fare_stage': False},
            {'seq': 18, 'name': 'MOTTAMMOODU', 'lat': 8.609497, 'lng': 76.945997, 'fare_stage': True},
            {'seq': 19, 'name': 'MUKKUNADA', 'lat': 8.451104, 'lng': 77.028755, 'fare_stage': False},
            {'seq': 20, 'name': 'NARUVAMOODU', 'lat': 8.450235, 'lng': 77.034501, 'fare_stage': False},
            {'seq': 21, 'name': 'NADUKKADU JN', 'lat': 8.455527, 'lng': 77.037709, 'fare_stage': False},
            {'seq': 22, 'name': 'OLIPPUNADA', 'lat': 8.459868, 'lng': 77.0382, 'fare_stage': False},
            {'seq': 23, 'name': 'VALIYARATHALA JN', 'lat': 8.460845, 'lng': 77.042185, 'fare_stage': True},
            {'seq': 24, 'name': 'GOVINDAMANGALAM TEMPLE', 'lat': 8.461508, 'lng': 77.048602, 'fare_stage': False},
            {'seq': 25, 'name': 'GOVINDAMANGALAM JN', 'lat': 8.460566, 'lng': 77.050725, 'fare_stage': False},
            {'seq': 26, 'name': 'KUMBALATHUNADA', 'lat': 8.459828, 'lng': 77.053084, 'fare_stage': False},
            {'seq': 27, 'name': 'ISHALIKODU', 'lat': 8.45916, 'lng': 77.056853, 'fare_stage': False},
            {'seq': 28, 'name': 'OORUTTAMBALAM JN', 'lat': 8.459286, 'lng': 77.061445, 'fare_stage': True},
            {'seq': 29, 'name': 'VELLOORKONAM', 'lat': 8.589329, 'lng': 77.016322, 'fare_stage': False},
            {'seq': 30, 'name': 'MOOLAKONAM JN', 'lat': 8.465989, 'lng': 77.070206, 'fare_stage': False},
            {'seq': 31, 'name': 'MARANALLOOR', 'lat': 8.471826, 'lng': 77.072437, 'fare_stage': True},
            {'seq': 32, 'name': 'ARUMALLOOR', 'lat': 8.476911, 'lng': 77.074359, 'fare_stage': False},
            {'seq': 33, 'name': 'KANDALA', 'lat': 8.482613, 'lng': 77.072695, 'fare_stage': False},
            {'seq': 34, 'name': 'KOCHUPALLINADA KANDALA', 'lat': 8.486897, 'lng': 77.074424, 'fare_stage': False},
            {'seq': 35, 'name': 'THOONGAMPARA', 'lat': 8.492433, 'lng': 77.076464, 'fare_stage': True},
            {'seq': 36, 'name': 'ANJUTHENGINMOODU', 'lat': 8.502041, 'lng': 77.077896, 'fare_stage': False},
            {'seq': 37, 'name': 'KATTAKADA KSRTC DEPOT PLATFORM NO1', 'lat': 8.506665, 'lng': 77.081073, 'fare_stage': True}
        ]
        
        # Insert routes into the database
        route_no = '1518E'  # East Fort to Kattakada route number
        
        for item in route_data:
            route, created = Route.objects.update_or_create(
                route_no=route_no,
                order_sequence=item['seq'],
                defaults={
                    'stop_name': item['name'],
                    'stop_latitude': item['lat'],
                    'stop_longitude': item['lng'],
                    'fare_stage': item['fare_stage']
                }
            )
            
            self.stdout.write(f"Added route stop {route_no}-{item['seq']}: {item['name']}")
    
    def import_kattakada_to_eastfort_routes(self):
        self.stdout.write("Importing Kattakada to East Fort routes...")
        
        # Route data from image 3
        route_data = [
            {'seq': 1, 'name': 'KATTAKADA KSRTC DEPOT PLATFORM NO1', 'lat': 8.50667, 'lng': 77.08107, 'fare_stage': True},
            {'seq': 2, 'name': 'ANJUTHENGINMOODU', 'lat': 8.50204, 'lng': 77.0779, 'fare_stage': False},
            {'seq': 3, 'name': 'THOONGAMPARA', 'lat': 8.49243, 'lng': 77.07646, 'fare_stage': True},
            {'seq': 4, 'name': 'KOCHUPALLINADA KANDALA', 'lat': 8.48687, 'lng': 77.07448, 'fare_stage': False},
            {'seq': 5, 'name': 'KANDALA', 'lat': 8.48277, 'lng': 77.07275, 'fare_stage': False},
            {'seq': 6, 'name': 'ARUMALLOOR', 'lat': 8.47693, 'lng': 77.07443, 'fare_stage': False},
            {'seq': 7, 'name': 'MARANALLOOR', 'lat': 8.47187, 'lng': 77.0724, 'fare_stage': True},
            {'seq': 8, 'name': 'MOOLAKONAM 1', 'lat': 8.46369, 'lng': 77.06959, 'fare_stage': False},
            {'seq': 9, 'name': 'VELLOORKONAM', 'lat': 8.58946, 'lng': 77.01642, 'fare_stage': False},
            {'seq': 10, 'name': 'OORUTTAMBALAM GOVT SCHOOL', 'lat': 8.45929, 'lng': 77.06145, 'fare_stage': True},
            {'seq': 11, 'name': 'OORUTTAMBALAM ISHALIKKODU', 'lat': 8.45879, 'lng': 77.05948, 'fare_stage': False},
            {'seq': 12, 'name': 'ISHALIKODU', 'lat': 8.45916, 'lng': 77.05686, 'fare_stage': False},
            {'seq': 13, 'name': 'KUMBALATHU NADA', 'lat': 8.45986, 'lng': 77.053, 'fare_stage': False},
            {'seq': 14, 'name': 'GOVINDAMANGALAM JN', 'lat': 8.46057, 'lng': 77.05072, 'fare_stage': False},
            {'seq': 15, 'name': 'GOVINDAMANGALAM TEMPLE', 'lat': 8.46151, 'lng': 77.0486, 'fare_stage': False},
            {'seq': 16, 'name': 'VALIYARATHALA', 'lat': 8.46072, 'lng': 77.04231, 'fare_stage': True},
            {'seq': 17, 'name': 'OLIPPUNADA', 'lat': 8.45987, 'lng': 77.0382, 'fare_stage': False},
            {'seq': 18, 'name': 'NADUKKADU.', 'lat': 8.45555, 'lng': 77.03771, 'fare_stage': False},
            {'seq': 19, 'name': 'NARUVAMOODU', 'lat': 8.45016, 'lng': 77.03416, 'fare_stage': False},
            {'seq': 20, 'name': 'MOTTAMOODU', 'lat': 8.4498, 'lng': 77.02547, 'fare_stage': True},
            {'seq': 21, 'name': 'NETHAJI NAGAR', 'lat': 8.44961, 'lng': 77.01977, 'fare_stage': False},
            {'seq': 22, 'name': 'ARIKKADAMUKKU', 'lat': 8.44955, 'lng': 77.01485, 'fare_stage': False},
            {'seq': 23, 'name': 'PRAVACHAMBALAM', 'lat': 8.44959, 'lng': 77.01036, 'fare_stage': False},
            {'seq': 24, 'name': 'NEMOM SCHOOL', 'lat': 8.45167, 'lng': 77.00744, 'fare_stage': False},
            {'seq': 25, 'name': 'NEMOM', 'lat': 8.45496, 'lng': 77.00242, 'fare_stage': True},
            {'seq': 26, 'name': 'VELLAYANI JUNCTION', 'lat': 8.45825, 'lng': 76.99854, 'fare_stage': False},
            {'seq': 27, 'name': 'OLD KARAKKAMANDAPAM', 'lat': 8.46103, 'lng': 76.99444, 'fare_stage': False},
            {'seq': 28, 'name': 'KARAKKAMANDAPAM JUNCTION', 'lat': 8.46494, 'lng': 76.99003, 'fare_stage': False},
            {'seq': 29, 'name': 'PAPPANAMCODE', 'lat': 8.47087, 'lng': 76.98023, 'fare_stage': True},
            {'seq': 30, 'name': 'CENTRAL WORKS', 'lat': 8.47152, 'lng': 76.97937, 'fare_stage': False},
            {'seq': 31, 'name': 'KAIMANAM JUNCTION', 'lat': 8.47381, 'lng': 76.97656, 'fare_stage': False},
            {'seq': 32, 'name': 'NEERAMANKARA', 'lat': 8.47702, 'lng': 76.97194, 'fare_stage': False},
            {'seq': 33, 'name': 'KARAMANA CO OPETATIVE BANK', 'lat': 8.47851, 'lng': 76.96387, 'fare_stage': True},
            {'seq': 34, 'name': 'PRS HOSPITAL', 'lat': 8.48138, 'lng': 76.9595, 'fare_stage': False},
            {'seq': 35, 'name': 'KILLIPALAM', 'lat': 8.48241, 'lng': 76.95725, 'fare_stage': False},
            {'seq': 36, 'name': 'RMS THAMPANOOR', 'lat': 8.4878, 'lng': 76.95017, 'fare_stage': False},
            {'seq': 37, 'name': 'EASTFORT', 'lat': 8.48293, 'lng': 76.94833, 'fare_stage': True}
        ]
        
        # Insert routes into the database
        route_no = '1542E'  # Kattakada to East Fort route number
        
        for item in route_data:
            route, created = Route.objects.update_or_create(
                route_no=route_no,
                order_sequence=item['seq'],
                defaults={
                    'stop_name': item['name'],
                    'stop_latitude': item['lat'],
                    'stop_longitude': item['lng'],
                    'fare_stage': item['fare_stage']
                }
            )
            
            self.stdout.write(f"Added route stop {route_no}-{item['seq']}: {item['name']}")