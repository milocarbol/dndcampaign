from django.db import models


class Thing(models.Model):
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=500)
    children = models.ManyToManyField('self', blank=True, symmetrical=False)

    def __str__(self):
        return self.name
