from django.db import models

class Court(models.Model):
    number = models.IntegerField(unique=True)

    def __str__(self):
        return f"Court {self.number}"

class Reservation(models.Model):
    court = models.ForeignKey(Court, on_delete=models.CASCADE, related_name='reservations')
    creator = models.ForeignKey('members.Member', on_delete=models.CASCADE, related_name='created_reservations')
    players = models.ManyToManyField('members.Member', related_name='court_reservations')
    date_time = models.DateTimeField()
    duration = models.IntegerField()

    class Meta:
        db_table = 'reservation'

    def __str__(self):
        return f"Reservation on {self.court} at {self.date_time}"
