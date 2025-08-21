from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from bus_route.models import Schedule, Route, Trip

# Create your models here.
class Depot(models.Model):
    depot_id = models.CharField(max_length=10, primary_key=True)
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=200)
    address = models.TextField()
    contact_number = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    capacity = models.IntegerField(default=0)  # Number of buses that can be parked
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.depot_id})"

class Employee(models.Model):
    ROLE_CHOICES = (
        ('driver', 'Driver'),
        ('conductor', 'Conductor'),
        ('mechanic', 'Mechanic'),
        ('manager', 'Manager'),
        ('admin', 'Administrative Staff'),
        ('other', 'Other'),
    )

    STATUS_CHOICES = (
        ('active', 'Active'),
        ('on_leave', 'On Leave'),
        ('suspended', 'Suspended'),
        ('retired', 'Retired'),
        ('terminated', 'Terminated'),
    )

    emp_id = models.CharField(max_length=10, primary_key=True)
    name = models.CharField(max_length=100)
    depot = models.ForeignKey(Depot, on_delete=models.CASCADE, related_name='employees')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    license_number = models.CharField(max_length=20, blank=True, null=True)  # For drivers
    contact_number = models.CharField(max_length=15)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField()
    date_of_birth = models.DateField()
    date_of_joining = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        # Validate that drivers have a license number
        if self.role == 'driver' and not self.license_number:
            raise ValidationError({'license_number': 'License number is required for drivers.'})

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.emp_id}) - {self.get_role_display()}"

class EmployeeAttendance(models.Model):
    STATUS_CHOICES = (
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('half_day', 'Half Day'),
        ('leave', 'On Leave'),
    )

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='absent')
    check_in_time = models.TimeField(null=True, blank=True)
    check_out_time = models.TimeField(null=True, blank=True)
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('employee', 'date')

    def __str__(self):
        return f"{self.employee.name} - {self.date} - {self.get_status_display()}"

class TripAssignment(models.Model):
    ROLE_CHOICES = (
        ('driver', 'Driver'),
        ('conductor', 'Conductor'),
    )

    SLOT_CHOICES = (
        ('morning', 'Morning'),
        ('afternoon', 'Afternoon'),
        ('evening', 'Evening'),
        ('night', 'Night'),
        ('full_day', 'Full Day'),
    )

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='trip_assignments')
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, related_name='assignments')
    assignment_date = models.DateField()  # The date for which the trip is assigned
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    slot = models.CharField(max_length=10, choices=SLOT_CHOICES, default='full_day')
    assigned_time = models.TimeField(null=True, blank=True)  # Scheduled departure time
    trip_executed = models.BooleanField(default=False)  # Whether the trip was actually executed
    assigned_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, related_name='assignments_made')
    assigned_at = models.DateTimeField(auto_now_add=True)  # When the assignment was created
    remarks = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('employee', 'schedule', 'assignment_date', 'role')

    def clean(self):
        # Validate that the employee role matches the assignment role
        if self.employee.role not in ['driver', 'conductor'] or self.employee.role != self.role:
            raise ValidationError({'employee': f'Employee must be a {self.get_role_display()} for this assignment.'})

        # Validate that the employee is active
        if self.employee.status != 'active':
            raise ValidationError({'employee': 'Employee must be active to be assigned to trips.'})

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    @property
    def schedule_no(self):
        return self.schedule.schedule_no

    @property
    def trip_no(self):
        return self.schedule.trip_no

    def __str__(self):
        return f"{self.employee.name} - Schedule {self.schedule.schedule_no} - Trip {self.schedule.trip_no} - {self.assignment_date}"

class TripExecution(models.Model):
    STATUS_CHOICES = (
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('delayed', 'Delayed'),
        ('partial', 'Partially Completed'),
    )

    assignment = models.ForeignKey(TripAssignment, on_delete=models.CASCADE, related_name='executions')
    actual_start_time = models.TimeField(null=True, blank=True)
    actual_end_time = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='completed')
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Update the trip_executed flag in the assignment
        if self.status == 'completed' or self.status == 'partial':
            self.assignment.trip_executed = True
            self.assignment.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Execution of {self.assignment} - {self.get_status_display()}"

class Bus(models.Model):
    BUS_TYPES = (
        ('ordinary', 'Ordinary'),
        ('express', 'Express'),
        ('super_express', 'Super Express'),
        ('luxury', 'Luxury'),
        ('ac', 'Air Conditioned'),
    )

    BUS_STATUS = (
        ('active', 'Active'),
        ('maintenance', 'Under Maintenance'),
        ('inactive', 'Inactive'),
    )

    registration_number = models.CharField(max_length=20, primary_key=True)
    depot = models.ForeignKey(Depot, on_delete=models.CASCADE, related_name='buses')
    bus_type = models.CharField(max_length=20, choices=BUS_TYPES)
    seating_capacity = models.IntegerField()
    manufacturing_year = models.IntegerField()
    last_maintenance_date = models.DateField(null=True, blank=True)
    next_maintenance_due = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=BUS_STATUS, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.registration_number} - {self.get_bus_type_display()}"

class BusAssignment(models.Model):
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE, related_name='assignments')
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, related_name='bus_assignments')
    assignment_date = models.DateField()  # The date for which the bus is assigned
    assigned_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, related_name='bus_assignments_made')
    assigned_at = models.DateTimeField(auto_now_add=True)  # When the assignment was created
    remarks = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('bus', 'schedule', 'assignment_date')

    def clean(self):
        # Validate that the bus is active
        if self.bus.status != 'active':
            raise ValidationError({'bus': 'Bus must be active to be assigned to schedules.'})

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    @property
    def schedule_no(self):
        return self.schedule.schedule_no

    def __str__(self):
        return f"{self.bus.registration_number} - Schedule {self.schedule.schedule_no} - {self.assignment_date}"

class Maintenance(models.Model):
    MAINTENANCE_TYPES = (
        ('routine', 'Routine Check'),
        ('repair', 'Repair'),
        ('overhaul', 'Overhaul'),
        ('emergency', 'Emergency Repair'),
    )

    STATUS_CHOICES = (
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )

    bus = models.ForeignKey(Bus, on_delete=models.CASCADE, related_name='maintenance_records')
    maintenance_type = models.CharField(max_length=20, choices=MAINTENANCE_TYPES)
    description = models.TextField()
    scheduled_date = models.DateField()
    completion_date = models.DateField(null=True, blank=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    performed_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='maintenance_performed')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Update the bus status when maintenance is scheduled or completed
        if self.status == 'scheduled' or self.status == 'in_progress':
            self.bus.status = 'maintenance'
            self.bus.save()
        elif self.status == 'completed':
            self.bus.status = 'active'
            self.bus.last_maintenance_date = self.completion_date or timezone.now().date()
            self.bus.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.bus.registration_number} - {self.get_maintenance_type_display()} - {self.scheduled_date}"
