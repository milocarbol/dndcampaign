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
    description = models.TextField(null=False, blank=True)
    background = models.TextField(null=True, blank=True)
    current_state = models.TextField(null=True, blank=True)

    markup_description = models.TextField(null=True, blank=True)
    markup_background = models.TextField(null=True, blank=True)
    markup_current_state = models.TextField(null=True, blank=True)

    is_bookmarked = models.BooleanField(default=False)
    children = models.ManyToManyField('self', blank=True, symmetrical=False)
    thing_type = models.ForeignKey(ThingType, on_delete=models.CASCADE, null=True)
    image = models.CharField(max_length=300, null=True, blank=True)

    class Meta:
        unique_together = (('campaign', 'name'),)

    def __str__(self):
        return self.name


class Attribute(models.Model):
    thing_type = models.ForeignKey(ThingType, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    display_in_summary = models.BooleanField(default=False)
    editable = models.BooleanField(default=True)
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


class DndBeyondType(models.Model):
    name = models.CharField(max_length=50, unique=True)
    base_url = models.CharField(max_length=50)
    markup_symbol = models.CharField(max_length=1)

    def __str__(self):
        return '{0}: {1} ({2})'.format(self.name, self.base_url, self.markup_symbol)


class DndBeyondRef(models.Model):
    dndbeyond_type = models.ForeignKey(DndBeyondType, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)

    class Meta:
        unique_together = (('dndbeyond_type', 'name'),)

    def __str__(self):
        return '[{0}] {1}'.format(self.dndbeyond_type.name, self.name)


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
    category_parameter = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    concatenate_results = models.BooleanField(default=False)
    can_randomize_later = models.BooleanField(default=False)
    must_be_unique = models.BooleanField(default=True)
    max_options_to_use = models.IntegerField(default=1)

    class Meta:
        unique_together = (('name', 'thing_type'),)

    def __str__(self):
        return '[{0}] {1}'.format(self.thing_type.name, self.name)


class RandomizerAttributeOption(models.Model):
    name = models.CharField(max_length=50)
    attribute = models.ForeignKey(RandomizerAttribute, on_delete=models.CASCADE)

    class Meta:
        unique_together = (('name', 'attribute'),)

    def __str__(self):
        return '[{0}.{1}] {2}'.format(self.attribute.thing_type.name, self.attribute.name, self.name)



class RandomizerAttributeCategory(models.Model):
    name = models.CharField(max_length=50)
    attribute = models.ForeignKey(RandomizerAttribute, on_delete=models.CASCADE)
    show = models.BooleanField(default=True)
    can_combine_with_self = models.BooleanField(default=False)
    max_options_to_use = models.IntegerField(default=1)
    can_randomize_later = models.BooleanField(default=False)
    must_be_unique = models.BooleanField(default=True)
    use_values_from = models.ManyToManyField('self', blank=True, symmetrical=False)

    class Meta:
        unique_together = (('name', 'attribute'),)

    def __str__(self):
        return '[{0}.{1}] {2}'.format(self.attribute.thing_type.name, self.attribute.name, self.name)


class RandomizerAttributeCategoryOption(models.Model):
    name = models.CharField(max_length=50)
    category = models.ForeignKey(RandomizerAttributeCategory, on_delete=models.CASCADE)

    class Meta:
        unique_together = (('name', 'category'),)

    def __str__(self):
        return '[{0}] {1}: {2}'.format(self.category.attribute.name, self.category.name, self.name)


class WeightPreset(models.Model):
    name = models.CharField(max_length=50)
    attribute_name = models.CharField(max_length=50, null=True, blank=True)
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=False)

    class Meta:
        unique_together = (('name', 'attribute_name', 'campaign'),)

    def __str__(self):
        return '[{0}] {1}'.format(self.campaign.name, self.name)


class Weight(models.Model):
    name_to_weight = models.CharField(max_length=50)
    weight = models.IntegerField(default=0)
    weight_preset = models.ForeignKey(WeightPreset, on_delete=models.CASCADE)

    class Meta:
        unique_together = (('name_to_weight', 'weight_preset'),)

    def __str__(self):
        return '[{0}] {1}: {2}'.format(self.weight_preset.name, self.name_to_weight, self.weight)


class RandomAttribute(models.Model):
    thing = models.ForeignKey(Thing, on_delete=models.CASCADE)
    text = models.CharField(max_length=100)

    def __str__(self):
        return '[{0}] {1}...'.format(self.thing.name, self.text[:20])


class GeneratorObject(models.Model):
    name = models.CharField(max_length=50, unique=True)
    thing_type = models.ForeignKey(ThingType, on_delete=models.CASCADE)
    inherit_settings_from = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    attribute_for_container = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return self.name


class GeneratorObjectContains(models.Model):
    generator_object = models.ForeignKey(GeneratorObject, on_delete=models.CASCADE, related_name='generator_object')
    contained_object = models.ForeignKey(GeneratorObject, on_delete=models.CASCADE, related_name='contained_object')
    percent_chance_for_one = models.IntegerField(default=0)
    min_objects = models.IntegerField(default=1)
    max_objects = models.IntegerField(default=5)

    def __str__(self):
        if self.percent_chance_for_one:
            display_string = '{0} has a {1}% chance to contain 1 {2}'.format(self.generator_object.name, self.percent_chance_for_one, self.contained_object.name)
        else:
            display_string = '{0} contains {1}-{2} {3}s'.format(self.generator_object.name, self.min_objects, self.max_objects, self.contained_object.name)
        return display_string


class GeneratorObjectFieldToRandomizerAttribute(models.Model):
    generator_object = models.ForeignKey(GeneratorObject, on_delete=models.CASCADE)
    field_name = models.CharField(max_length=50, null=True, blank=True)
    randomizer_attribute = models.ForeignKey(RandomizerAttribute, on_delete=models.CASCADE, null=True, blank=True)
    randomizer_attribute_category = models.ForeignKey(RandomizerAttributeCategory, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        if self.field_name:
            if self.randomizer_attribute:
                return '{0}: {1} = {2}'.format(self.generator_object.name, self.field_name, self.randomizer_attribute)
            else:
                return '{0}: {1} = {2}'.format(self.generator_object.name, self.field_name, self.randomizer_attribute_category)
        elif self.randomizer_attribute:
            return '{0}: add {1}'.format(self.generator_object.name, self.randomizer_attribute)
        elif self.randomizer_attribute_category:
            return '{0}: add {1}'.format(self.generator_object.name, self.randomizer_attribute_category)
        else:
            return '{0}: NOT MAPPED'
