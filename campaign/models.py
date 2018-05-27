from django.db import models


class Campaign(models.Model):
    name = models.CharField(max_length=50, unique=True)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return '{0} (active={1})'.format(self.name, self.is_active)


class ThingType(models.Model):
    name = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return self.name


class Thing(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=50)
    description = models.TextField()
    children = models.ManyToManyField('self', blank=True, symmetrical=False)
    thing_type = models.ForeignKey(ThingType, on_delete=models.CASCADE, null=True)

    class Meta:
        unique_together = (('campaign', 'name'),)

    def __str__(self):
        return self.name


class Attribute(models.Model):
    thing_type = models.ForeignKey(ThingType, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    display_in_summary = models.BooleanField(default=False)
    is_thing = models.BooleanField(default=False)

    class Meta:
        unique_together = (('thing_type', 'name'),)

    def __str__(self):
        return '[{0}] {1}'.format(self.thing_type.name, self.name)


class AttributeValue(models.Model):
    thing = models.ForeignKey(Thing, on_delete=models.CASCADE)
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)
    value = models.CharField(max_length=100)

    class Meta:
        unique_together = (('thing', 'attribute'),)

    def __str__(self):
        return '[{0}] {1}:{2}'.format(self.thing.name, self.attribute.name, self.value)


class UsefulLink(models.Model):
    thing = models.ForeignKey(Thing, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    value = models.CharField(max_length=100)

    def __str__(self):
        return '[{0}] {1}:{2}'.format(self.thing.name, self.name, self.value)


class RandomEncounterType(models.Model):
    name = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return self.name


class RandomEncounter(models.Model):
    thing = models.ForeignKey(Thing, on_delete=models.CASCADE)
    random_encounter_type = models.ForeignKey(RandomEncounterType, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=50)

    class Meta:
        unique_together = (('thing', 'random_encounter_type', 'name'),)

    def __str__(self):
        return '[{0}] {1}:{2}'.format(self.thing.name, self.random_encounter_type.name, self.name)


class RandomizerAttribute(models.Model):
    name = models.CharField(max_length=50)
    thing_type = models.ForeignKey(ThingType, on_delete=models.CASCADE)
    concatenate_results = models.BooleanField(default=False)
    can_randomize_later = models.BooleanField(default=False)

    class Meta:
        unique_together = (('name', 'thing_type'))

    def __str__(self):
        return '[{0}] {1}'.format(self.thing_type.name, self.name)


class RandomizerAttributeOption(models.Model):
    name = models.CharField(max_length=50)
    attribute = models.ForeignKey(RandomizerAttribute, on_delete=models.CASCADE)

    class Meta:
        unique_together = (('name', 'attribute'))

    def __str__(self):
        return '[{0}] {1}'.format(self.attribute.name, self.name)


class RandomizerAttributeCategory(models.Model):
    name = models.CharField(max_length=50)
    attribute = models.ForeignKey(RandomizerAttribute, on_delete=models.CASCADE)
    show = models.BooleanField(default=True)
    can_combine_with_self = models.BooleanField(default=False)
    max_options_to_use = models.IntegerField(default=1)
    can_randomize_later = models.BooleanField(default=False)

    class Meta:
        unique_together = (('name', 'attribute'))

    def __str__(self):
        return '[{0}] {1}'.format(self.attribute.name, self.name)


class RandomizerAttributeCategoryOption(models.Model):
    name = models.CharField(max_length=50)
    category = models.ForeignKey(RandomizerAttributeCategory, on_delete=models.CASCADE)

    class Meta:
        unique_together = (('name', 'category'))

    def __str__(self):
        return '[{0}] {1}: {2}'.format(self.category.attribute.name, self.category.name, self.name)


class RandomAttribute(models.Model):
    thing = models.ForeignKey(Thing, on_delete=models.CASCADE)
    randomizer_attribute_category = models.ForeignKey(RandomizerAttributeCategory, on_delete=models.CASCADE)
    text = models.CharField(max_length=100)

    def __str__(self):
        return '[{0}] {1}...'.format(self.thing.name, self.text[:20])
