from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.utils import timezone
from .models import Depot, Employee, EmployeeAttendance, TripAssignment, Bus, BusAssignment, Maintenance
from bus_route.models import Schedule, Route, Trip
from datetime import datetime, timedelta

# Create your views here.
def index(request):
    # Count statistics for dashboard
    depot_count = Depot.objects.count()
    employee_count = Employee.objects.count()
    # Bus-related counts removed

    # Get today's assignments
    today = timezone.now().date()
    today_assignments = TripAssignment.objects.filter(assignment_date=today).count()

    # Get today's attendance
    present_today = EmployeeAttendance.objects.filter(
        date=today,
        status__in=['present', 'half_day']
    ).count()

    context = {
        'depot_count': depot_count,
        'employee_count': employee_count,
        'today_assignments': today_assignments,
        'present_today': present_today,
    }

    return render(request, 'depot_manager/index.html', context)

@login_required
def depot_list(request):
    depots = Depot.objects.all()
    return render(request, 'depot_manager/depot_list.html', {'depots': depots})

@login_required
def depot_detail(request, depot_id):
    depot = get_object_or_404(Depot, depot_id=depot_id)
    # Get all employees for this depot
    employees = Employee.objects.filter(depot=depot)

    # Get counts by role
    drivers = employees.filter(role='driver')
    conductors = employees.filter(role='conductor')

    # Create a custom object with the counts
    employee_stats = {
        'count': employees.count(),
        'drivers': {'count': drivers.count()},
        'conductors': {'count': conductors.count()}
    }

    context = {
        'depot': depot,
        'employees': employees,
        'employee_stats': employee_stats,
    }

    return render(request, 'depot_manager/depot_detail.html', context)

@login_required
def employee_list(request):
    employees = Employee.objects.all()
    return render(request, 'depot_manager/employee_list.html', {'employees': employees})

@login_required
def employee_detail(request, emp_id):
    employee = get_object_or_404(Employee, emp_id=emp_id)

    # Get recent attendance records
    attendance_records = EmployeeAttendance.objects.filter(employee=employee).order_by('-date')[:30]

    # Get upcoming assignments
    today = timezone.now().date()
    upcoming_assignments = TripAssignment.objects.filter(
        employee=employee,
        assignment_date__gte=today
    ).order_by('assignment_date', 'schedule__schedule_no', 'schedule__trip_no')[:10]

    context = {
        'employee': employee,
        'attendance_records': attendance_records,
        'upcoming_assignments': upcoming_assignments,
        'today': today,
    }

    return render(request, 'depot_manager/employee_detail.html', context)

@login_required
def mark_attendance(request):
    if request.method == 'POST':
        employee_id = request.POST.get('employee_id')
        date_str = request.POST.get('date')
        status = request.POST.get('status')
        remarks = request.POST.get('remarks')

        try:
            employee = Employee.objects.get(emp_id=employee_id)
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()

            # Create or update attendance record
            defaults = {
                'status': status,
                'remarks': remarks
            }

            # Check-in and check-out times removed

            attendance, created = EmployeeAttendance.objects.update_or_create(
                employee=employee,
                date=date_obj,
                defaults=defaults
            )

            messages.success(request, f'Attendance marked for {employee.name} on {date_obj}')
            return redirect('employee_detail', emp_id=employee_id)
        except Exception as e:
            messages.error(request, f'Error marking attendance: {str(e)}')
            return redirect('employee_list')

    # If GET request, show the attendance form
    employees = Employee.objects.all()
    today = timezone.now().date()

    # Pre-select employee if provided in GET parameters
    preselected_employee = request.GET.get('employee_id')

    context = {
        'employees': employees,
        'today': today,
        'preselected_employee': preselected_employee
    }

    return render(request, 'depot_manager/mark_attendance.html', context)

@login_required
def assign_trips(request):
    if request.method == 'POST':
        employee_id = request.POST.get('employee_id')
        schedule_id = request.POST.get('schedule_id')
        assignment_date_str = request.POST.get('assignment_date')
        role = request.POST.get('role')
        slot = request.POST.get('slot', 'full_day')
        assigned_time = request.POST.get('assigned_time')
        remarks = request.POST.get('remarks')

        try:
            employee = Employee.objects.get(emp_id=employee_id)
            schedule = Schedule.objects.get(id=schedule_id)
            assignment_date = datetime.strptime(assignment_date_str, '%Y-%m-%d').date()

            # Validate that employee role matches assignment role
            if employee.role != role:
                messages.error(request, f'Employee {employee.name} is not a {role}. Please select an employee with the correct role.')
                return redirect('assign_trips')

            # Create the assignment
            assignment = TripAssignment.objects.create(
                employee=employee,
                schedule=schedule,
                assignment_date=assignment_date,
                role=role,
                slot=slot,
                assigned_time=assigned_time if assigned_time else None,
                remarks=remarks,
                assigned_by=request.user.employee if hasattr(request.user, 'employee') else None
            )

            messages.success(request, f'Trip {schedule.schedule_no}-{schedule.trip_no} assigned to {employee.name}')
            return redirect('employee_detail', emp_id=employee_id)
        except Schedule.DoesNotExist:
            messages.error(request, 'Selected schedule does not exist.')
            return redirect('assign_trips')
        except Exception as e:
            messages.error(request, f'Error assigning trip: {str(e)}')
            return redirect('assign_trips')

    # If GET request, show the assignment form
    employees = Employee.objects.filter(role__in=['driver', 'conductor'], status='active')
    schedules = Schedule.objects.all().order_by('schedule_no', 'trip_no')

    # Pre-select employee if provided in GET parameters
    preselected_employee = request.GET.get('employee_id')

    # Set default date to tomorrow (assignments are typically made for the next day)
    tomorrow = (timezone.now() + timedelta(days=1)).date()

    context = {
        'employees': employees,
        'schedules': schedules,
        'preselected_employee': preselected_employee,
        'tomorrow': tomorrow,
    }

    return render(request, 'depot_manager/assign_trips.html', context)

@login_required
def daily_roster(request):
    # Get date from request or use today
    date_str = request.GET.get('date')
    if date_str:
        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = timezone.now().date()
    else:
        selected_date = timezone.now().date()

    # Get all assignments for the selected date
    assignments = TripAssignment.objects.filter(assignment_date=selected_date).select_related('schedule', 'employee').order_by('schedule__schedule_no', 'schedule__trip_no')

    # Group assignments by schedule
    schedules = {}
    for assignment in assignments:
        schedule_no = assignment.schedule.schedule_no
        if schedule_no not in schedules:
            schedules[schedule_no] = []
        schedules[schedule_no].append(assignment)

    context = {
        'selected_date': selected_date,
        'schedules': schedules,
    }

    return render(request, 'depot_manager/daily_roster.html', context)

@login_required
def bus_list(request):
    buses = Bus.objects.all()
    return render(request, 'depot_manager/bus_list.html', {'buses': buses})

@login_required
def bus_detail(request, registration_number):
    bus = get_object_or_404(Bus, registration_number=registration_number)

    # Get maintenance records
    maintenance_records = Maintenance.objects.filter(bus=bus).order_by('-scheduled_date')

    # Get upcoming assignments
    today = timezone.now().date()
    upcoming_assignments = BusAssignment.objects.filter(
        bus=bus,
        assignment_date__gte=today
    ).order_by('assignment_date')

    context = {
        'bus': bus,
        'maintenance_records': maintenance_records,
        'upcoming_assignments': upcoming_assignments,
    }

    return render(request, 'depot_manager/bus_detail.html', context)

@login_required
def print_employee_trips(request, emp_id):
    """Print an employee's trips for a specific day"""
    employee = get_object_or_404(Employee, emp_id=emp_id)

    # Get date from request or use today
    date_str = request.GET.get('date')
    if date_str:
        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = timezone.now().date()
    else:
        selected_date = timezone.now().date()

    # Get all assignments for the employee on the selected date
    assignments = TripAssignment.objects.filter(
        employee=employee,
        assignment_date=selected_date
    ).select_related('schedule', 'employee').order_by('schedule__start_time')

    context = {
        'employee': employee,
        'selected_date': selected_date,
        'assignments': assignments,
        'print_mode': True,
    }

    return render(request, 'depot_manager/print_employee_trips.html', context)
