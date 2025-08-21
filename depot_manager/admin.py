from django.contrib import admin
from .models import Depot, Bus, Maintenance, Employee, EmployeeAttendance, TripAssignment, TripExecution, BusAssignment

# Register your models here.
@admin.register(Depot)
class DepotAdmin(admin.ModelAdmin):
    list_display = ('depot_id', 'name', 'location', 'capacity')
    search_fields = ('depot_id', 'name', 'location')
    list_filter = ('created_at',)

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('emp_id', 'name', 'depot', 'role', 'status')
    list_filter = ('depot', 'role', 'status', 'date_of_joining')
    search_fields = ('emp_id', 'name', 'contact_number')
    date_hierarchy = 'date_of_joining'
    fieldsets = (
        ('Basic Information', {
            'fields': ('emp_id', 'name', 'depot', 'role', 'status')
        }),
        ('Contact Information', {
            'fields': ('contact_number', 'email', 'address')
        }),
        ('Employment Details', {
            'fields': ('date_of_birth', 'date_of_joining', 'license_number')
        }),
    )

@admin.register(EmployeeAttendance)
class EmployeeAttendanceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'date', 'status', 'check_in_time', 'check_out_time')
    list_filter = ('status', 'date')
    search_fields = ('employee__name', 'employee__emp_id')
    date_hierarchy = 'date'
    raw_id_fields = ('employee',)

@admin.register(TripAssignment)
class TripAssignmentAdmin(admin.ModelAdmin):
    list_display = ('employee', 'schedule_no', 'trip_no', 'assignment_date', 'role', 'trip_executed')
    list_filter = ('role', 'assignment_date', 'trip_executed', 'slot')
    search_fields = ('employee__name', 'schedule_no', 'employee__emp_id')
    date_hierarchy = 'assignment_date'
    raw_id_fields = ('employee', 'assigned_by')

@admin.register(TripExecution)
class TripExecutionAdmin(admin.ModelAdmin):
    list_display = ('assignment', 'status', 'actual_start_time', 'actual_end_time')
    list_filter = ('status', 'created_at')
    search_fields = ('assignment__employee__name', 'assignment__schedule_no')
    date_hierarchy = 'created_at'
    raw_id_fields = ('assignment',)

@admin.register(Bus)
class BusAdmin(admin.ModelAdmin):
    list_display = ('registration_number', 'depot', 'bus_type', 'seating_capacity', 'status')
    list_filter = ('depot', 'bus_type', 'status', 'manufacturing_year')
    search_fields = ('registration_number', 'depot__name')
    date_hierarchy = 'created_at'

@admin.register(BusAssignment)
class BusAssignmentAdmin(admin.ModelAdmin):
    list_display = ('bus', 'schedule_no', 'assignment_date', 'assigned_by')
    list_filter = ('assignment_date',)
    search_fields = ('bus__registration_number', 'schedule_no')
    date_hierarchy = 'assignment_date'
    raw_id_fields = ('bus', 'assigned_by')

@admin.register(Maintenance)
class MaintenanceAdmin(admin.ModelAdmin):
    list_display = ('bus', 'maintenance_type', 'scheduled_date', 'completion_date', 'status', 'performed_by')
    list_filter = ('maintenance_type', 'status', 'scheduled_date')
    search_fields = ('bus__registration_number', 'description')
    date_hierarchy = 'scheduled_date'
    raw_id_fields = ('bus', 'performed_by')
