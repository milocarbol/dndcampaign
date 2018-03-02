from django.db import models


class ThingType(models.Model):
    name = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return self.name


class Thing(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(max_length=500)
    children = models.ManyToManyField('self', blank=True, symmetrical=False)
    thing_type = models.ForeignKey(ThingType, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.name


class Attribute(models.Model):
    thing_type = models.ForeignKey(ThingType, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    display_in_summary = models.BooleanField(default=False)

    class Meta:
        unique_together = (('thing_type', 'name'),)

    def __str__(self):
        return '[' + self.thing_type.name + '] ' + self.name


class AttributeValue(models.Model):
    thing = models.ForeignKey(Thing, on_delete=models.CASCADE)
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)
    value = models.CharField(max_length=100)

    class Meta:
        unique_together = (('thing', 'attribute'),)

    def __str__(self):
        return '[' + self.thing.name + '] ' + self.attribute.name + ': ' + self.value
