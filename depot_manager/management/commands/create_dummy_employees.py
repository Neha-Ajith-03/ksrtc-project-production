from django.core.management.base import BaseCommand
from depot_manager.models import Depot, Employee
from django.utils import timezone
import random
from datetime import timedelta
import string

class Command(BaseCommand):
    help = 'Creates dummy data for conductors and drivers'

    def add_arguments(self, parser):
        parser.add_argument('--drivers', type=int, default=20, help='Number of drivers to create')
        parser.add_argument('--conductors', type=int, default=20, help='Number of conductors to create')
        parser.add_argument('--depots', type=int, default=3, help='Number of depots to create')

    def handle(self, *args, **options):
        num_drivers = options['drivers']
        num_conductors = options['conductors']
        num_depots = options['depots']
        
        # Create depots if they don't exist
        depots = self.create_depots(num_depots)
        
        # Create drivers
        self.create_employees('driver', num_drivers, depots)
        
        # Create conductors
        self.create_employees('conductor', num_conductors, depots)
        
        self.stdout.write(self.style.SUCCESS(f'Successfully created {num_drivers} drivers and {num_conductors} conductors across {num_depots} depots'))

    def create_depots(self, num_depots):
        depots = []
        
        # Check if depots already exist
        existing_depots = Depot.objects.all()
        if existing_depots.exists():
            self.stdout.write(self.style.WARNING(f'Using {existing_depots.count()} existing depots'))
            return list(existing_depots)
        
        # Create new depots
        depot_locations = [
            ('Trivandrum Central', 'Thampanoor, Thiruvananthapuram'),
            ('East Fort', 'East Fort, Thiruvananthapuram'),
            ('Kattakada', 'Kattakada, Thiruvananthapuram'),
            ('Neyyattinkara', 'Neyyattinkara, Thiruvananthapuram'),
            ('Attingal', 'Attingal, Thiruvananthapuram'),
            ('Kollam', 'Kollam'),
            ('Kottarakkara', 'Kottarakkara, Kollam'),
            ('Pathanamthitta', 'Pathanamthitta'),
            ('Alappuzha', 'Alappuzha'),
            ('Kottayam', 'Kottayam'),
        ]
        
        # Use only the number of depots requested
        depot_locations = depot_locations[:num_depots]
        
        for i, (name, location) in enumerate(depot_locations):
            depot_id = f'DEP{i+1:03d}'
            depot = Depot.objects.create(
                depot_id=depot_id,
                name=name,
                location=location,
                address=f'{location}, Kerala, India',
                contact_number=f'0471-{random.randint(2000000, 2999999)}',
                email=f'{name.lower().replace(" ", "")}@ksrtc.kerala.gov.in',
                capacity=random.randint(30, 100)
            )
            depots.append(depot)
            self.stdout.write(f'Created depot: {depot.name}')
        
        return depots

    def create_employees(self, role, count, depots):
        # First names
        first_names = [
            'Anil', 'Sunil', 'Rajesh', 'Ramesh', 'Suresh', 'Mahesh', 'Dinesh', 'Ganesh',
            'Rajan', 'Vijayan', 'Krishnan', 'Gopan', 'Soman', 'Thomas', 'Joseph', 'George',
            'Mathew', 'Jacob', 'Philip', 'Samuel', 'Antony', 'Francis', 'Sebastian', 'Varghese',
            'Biju', 'Saju', 'Raju', 'Babu', 'Manu', 'Unni', 'Vinod', 'Manoj', 'Pramod', 'Arun',
            'Ajith', 'Anoop', 'Deepak', 'Pradeep', 'Sandeep', 'Dileep', 'Sajeev', 'Rajeev',
            'Santhosh', 'Jayesh', 'Girish', 'Harish', 'Jitesh', 'Nitesh', 'Umesh', 'Ramesh'
        ]
        
        # Last names
        last_names = [
            'Nair', 'Menon', 'Pillai', 'Kurup', 'Panicker', 'Thampi', 'Varma', 'Kaimal',
            'Namboothiri', 'Warrier', 'Pisharody', 'Pothuval', 'Kartha', 'Bhattathiri',
            'Kurian', 'Varghese', 'Thomas', 'Mathew', 'Philip', 'Samuel', 'Joseph', 'George',
            'Fernandez', 'D\'Souza', 'D\'Cruz', 'Pereira', 'Gonsalves', 'Rodrigues',
            'Khan', 'Mohammed', 'Salim', 'Hameed', 'Basheer', 'Ahammed', 'Ismail', 'Ibrahim',
            'Krishnan', 'Govindan', 'Gopalan', 'Achuthan', 'Madhavan', 'Balakrishnan', 'Chandran',
            'Raman', 'Venugopal', 'Narayanan', 'Damodaran', 'Gangadharan', 'Hariharan'
        ]
        
        # Generate a random date of birth
        def random_dob():
            # Between 25 and 55 years ago
            days_ago = random.randint(25*365, 55*365)
            return (timezone.now() - timedelta(days=days_ago)).date()
        
        # Generate a random date of joining
        def random_doj():
            # Between 1 and 25 years ago
            days_ago = random.randint(365, 25*365)
            return (timezone.now() - timedelta(days=days_ago)).date()
        
        # Generate a random license number (for drivers)
        def random_license():
            prefix = ''.join(random.choices(string.ascii_uppercase, k=2))
            numbers = ''.join(random.choices(string.digits, k=8))
            return f'{prefix}-{numbers}'
        
        # Get existing employee count to start ID from there
        existing_count = Employee.objects.filter(role=role).count()
        
        for i in range(count):
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            name = f'{first_name} {last_name}'
            
            # Create a unique employee ID
            emp_id = f'{role[0].upper()}{existing_count + i + 1:04d}'
            
            # Random depot
            depot = random.choice(depots)
            
            # Create the employee
            employee = Employee(
                emp_id=emp_id,
                name=name,
                depot=depot,
                role=role,
                contact_number=f'9{random.randint(100000000, 999999999)}',
                email=f'{first_name.lower()}.{last_name.lower()}@ksrtc.kerala.gov.in',
                address=f'{random.randint(1, 100)}, {random.choice(["Green", "Park", "Lake", "Hill", "River"])} View, {depot.location}',
                date_of_birth=random_dob(),
                date_of_joining=random_doj(),
                status='active'
            )
            
            # Add license number for drivers
            if role == 'driver':
                employee.license_number = random_license()
            
            employee.save()
            self.stdout.write(f'Created {role}: {employee.name} ({employee.emp_id})')
