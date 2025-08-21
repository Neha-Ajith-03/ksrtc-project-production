from django.db import models

class Route(models.Model):
      id = models.AutoField(primary_key=True)
      route_no = models.CharField(max_length=20)
      order_sequence = models.IntegerField(default=0)     
      stop_name = models.CharField(max_length=100)
      stop_latitude = models.FloatField()
      stop_longitude = models.FloatField()
      fare_stage = models.BooleanField(default=False)
      def save(self, *args, **kwargs):
            self.route_no = self.route_no.upper()
            super(Route, self).save(*args, **kwargs)
            
      def __str__(self):
            return f"Route {self.route_no}: {self.stop_name}"


class Schedule(models.Model):
      route_no = models.CharField(max_length=20)
      schedule_no = models.CharField(max_length=20)
      trip_no = models.IntegerField()
      source = models.CharField(max_length=100)
      destination = models.CharField(max_length=100)
      via = models.CharField(max_length=100, null=True, blank=True)
      
      # New fields for service details.
      service_type = models.CharField(max_length=50)
      start_time = models.TimeField(null=True, blank=True)
      end_time = models.TimeField(null=True, blank=True)
      trip_km = models.FloatField(null=True, blank=True)
      class Meta:
            unique_together = (('schedule_no', 'trip_no'),)
      def save(self, *args, **kwargs):
            self.schedule_no = self.schedule_no.upper()
            super(Schedule, self).save(*args, **kwargs)
      def __str__(self):
            return f"Schedule {self.schedule_no} - Trip {self.trip_no} "

class Trip(models.Model):
      date = models.DateField()
      schedule_no = models.CharField(max_length=20)
      trip_no = models.IntegerField()
      revenue = models.FloatField(null=True, blank=True)
      

      class Meta:
            unique_together = (('date', 'schedule_no', 'trip_no'),)

      @property
      def epkm(self):
            """
            Calculates EPKM as revenue divided by distance_km.
            Returns None if revenue or distance_km is missing or if distance_km is zero.
            """
            try:
                    schedule = Schedule.objects.get(schedule_no=self.schedule_no, trip_no=self.trip_no)
                    distance_km = schedule.trip_km
            except Schedule.DoesNotExist:
                    distance_km = None

            if self.revenue is not None and distance_km not in (None, 0):
                    return self.revenue / distance_km
            return None

      def __str__(self):
            return f"Trip on {self.date} - Schedule {self.schedule_no} - Trip {self.trip_no}"
