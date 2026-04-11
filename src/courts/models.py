from django.db import models

class Court(models.Model):
    number = models.IntegerField(unique=True)

    def __str__(self):
        return f"Court {self.number}"
