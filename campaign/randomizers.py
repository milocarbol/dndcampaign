import random

from .models import RandomAttribute, RandomizerAttribute, RandomizerAttributeCategory, RandomizerAttributeOption, RandomizerAttributeCategoryOption, WeightPreset, Weight


def generate_random_attributes_for_thing_raw(campaign, thing, attribute):
    for i in range(0, random.randint(1, attribute.max_options_to_use)):
        option = get_random_attribute_raw(campaign, thing.thing_type, attribute.name)
        if option:
            random_attribute = RandomAttribute(thing=thing, text=option)
            random_attribute.save()


def get_random_attribute_raw(campaign, thing_type, attribute):
    try:
        randomizer_attribute = RandomizerAttribute.objects.get(thing_type__name__iexact=thing_type, name__iexact=attribute)
    except RandomizerAttribute.DoesNotExist:
        raise ValueError('Invalid randomizer attribute: {0}'.format(attribute))
    if randomizer_attribute.concatenate_results:
        categories = RandomizerAttributeCategory.objects.filter(attribute=randomizer_attribute).order_by('name')
        result = ''
        if categories:
            for category in categories:
                result += '{0}:\n*-\n'.format(category.name)
                for i in range(0, random.randint(1, category.max_options_to_use)):
                    option = get_random_attribute_in_category_raw(thing_type=thing_type, attribute=attribute, category=category.name)
                    if option:
                        result += '- {0}-\n'.format(option)
                result += '-*\n'
        if result:
            return result
        else:
            return None
    else:
        try:
            weight_preset = WeightPreset.objects.get(campaign=campaign, attribute_name__iexact=attribute, is_active=True)
        except WeightPreset.DoesNotExist:
            weight_preset = None
        if weight_preset:
            options = []
            for option in RandomizerAttributeOption.objects.filter(attribute=randomizer_attribute):
                try:
                    weight = Weight.objects.get(weight_preset=weight_preset, name_to_weight__iexact=option.name).weight
                except Weight.DoesNotExist:
                    weight = 0
                for i in range(0, weight):
                    options.append(option.name)
        else:
            options = [o.name for o in RandomizerAttributeOption.objects.filter(attribute=randomizer_attribute)]
        if options:
            return random.choice(options)
        else:
            return None


def get_random_attribute_in_category_raw(thing_type, attribute, category):
    try:
        randomizer_attribute = RandomizerAttribute.objects.get(thing_type__name__iexact=thing_type, name__iexact=attribute)
    except RandomizerAttribute.DoesNotExist:
        raise ValueError('Invalid randomizer attribute: {0}'.format(attribute))

    try:
        randomizer_attribute_category = RandomizerAttributeCategory.objects.get(attribute=randomizer_attribute,
                                                                                name__iexact=category)
        if randomizer_attribute_category.use_values_from.all():
            randomizer_attribute_category = random.choice(randomizer_attribute_category.use_values_from.all())
    except RandomizerAttributeCategory.DoesNotExist:
        raise ValueError('Invalid randomizer attribute category for {0}: {1}'.format(attribute, category))

    randomizer_attribute_category_2 = RandomizerAttributeCategory.objects.filter(attribute=randomizer_attribute,
                                                                                 name__iexact=randomizer_attribute_category.name + '_2')
    randomizer_attribute_category_synonym_first = RandomizerAttributeCategory.objects.filter(attribute=randomizer_attribute,
                                                                                             name__iexact=randomizer_attribute_category.name + '_synonym_first')
    randomizer_attribute_category_synonym_last = RandomizerAttributeCategory.objects.filter(attribute=randomizer_attribute,
                                                                                             name__iexact=randomizer_attribute_category.name + '_synonym_last')

    result = ''
    result_and = ''

    options = [o.name for o in RandomizerAttributeCategoryOption.objects.filter(category=randomizer_attribute_category)]
    options2 = []
    if randomizer_attribute_category_2:
        options2 = [o.name for o in RandomizerAttributeCategoryOption.objects.filter(category=randomizer_attribute_category_2[0])]

    if options:
        result = random.choice(options)
    if options2:
        result2 = random.choice(options2)
        if result2 == result2.lower():
            result += result2
        else:
            result += ' ' + result2
        if randomizer_attribute_category_2[0].can_combine_with_self:
            result_and = random.choice(options2) + ' and ' + random.choice(options2)

    if result and result_and:
        if random.choice([0, 1]) == 0:
            result = result_and

    use_first_synonym = False
    use_last_synonym = False
    if randomizer_attribute_category_synonym_first and randomizer_attribute_category_synonym_last:
        if random.choice([0, 1]) == 0:
            use_first_synonym = True
        else:
            use_last_synonym = True
    elif randomizer_attribute_category_synonym_first:
        use_first_synonym = True
    elif randomizer_attribute_category_synonym_last:
        use_last_synonym = True
    if use_first_synonym:
        synonyms = [o.name for o in RandomizerAttributeCategoryOption.objects.filter(category=randomizer_attribute_category_synonym_first[0])]
        synonym = random.choice(synonyms)
        result = synonym + ' ' + result
    elif use_last_synonym:
        synonyms = [o.name for o in RandomizerAttributeCategoryOption.objects.filter(category=randomizer_attribute_category_synonym_last[0])]
        synonym = random.choice(synonyms)
        result += ' ' + synonym

    if result:
        return result
    else:
        return None


def get_randomization_options_for_new_thing(thing_type):
    all_attributes = RandomizerAttribute.objects.filter(thing_type=thing_type)
    allow_random = []
    allow_random_by_category = []
    for attr in all_attributes:
        if attr.concatenate_results or len(RandomizerAttributeCategory.objects.filter(attribute=attr)) == 0:
            allow_random.append(attr.name.lower())
        else:
            allow_random_by_category.append(attr.name.lower())
    randomizer_categories = []
    for attribute in allow_random_by_category:
        randomizer_attribute = RandomizerAttribute.objects.get(thing_type=thing_type, name__iexact=attribute)
        randomizer_categories.append({
            'field_name': attribute,
            'categories': [o.name for o in RandomizerAttributeCategory.objects.filter(attribute=randomizer_attribute, show=True).order_by('name')]
        })
    return {
        'allow_random': allow_random,
        'allow_random_by_category': allow_random_by_category,
        'randomizer_categories': randomizer_categories
    }