from django.db import models

class Court(models.Model):
    """
    Model representing a physical sports court that can be booked by members.
    """
    number = models.IntegerField(unique=True)

    def __str__(self):
        return f"Court {self.number}"

class Reservation(models.Model):
    """
    Model to track court bookings (reservations).
    Each reservation tracks its creator, who is playing, and the time slot details.
    """
    court = models.ForeignKey(Court, on_delete=models.CASCADE, related_name='reservations')
    
    # Track the specific member who made the booking request
    creator = models.ForeignKey('members.Member', on_delete=models.CASCADE, related_name='created_reservations')
    
    # Store all the players participating in this court reservation
    players = models.ManyToManyField('members.Member', related_name='court_reservations')
    
    date_time = models.DateTimeField()
    duration = models.IntegerField() # In minutes

    class Meta:
        db_table = 'reservation'

    def __str__(self):
        return f"Reservation on {self.court} at {self.date_time}"