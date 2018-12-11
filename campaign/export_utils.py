import json

from .models import Thing, AttributeValue, UsefulLink, RandomEncounter, RandomAttribute, Weight, WeightPreset, ThingType, Attribute, RandomEncounterType, RandomizerAttribute, RandomizerAttributeCategory, RandomizerAttributeOption, RandomizerAttributeCategoryOption, GeneratorObject, GeneratorObjectContains, GeneratorObjectFieldToRandomizerAttribute


def campaign_to_json(campaign):
    thing_data = []
    for thing in Thing.objects.filter(campaign=campaign):
        attributes = []
        attribute_values = AttributeValue.objects.filter(thing=thing)
        for attribute_value in attribute_values:
            attributes.append({
                'attribute': attribute_value.attribute.name,
                'value': attribute_value.value
            })
        links = []
        for link in UsefulLink.objects.filter(thing=thing):
            links.append({
                'name': link.name,
                'value': link.value
            })
        random_encounters = []
        for random_encounter in RandomEncounter.objects.filter(thing=thing):
            random_encounters.append({
                'random_encounter_type': random_encounter.random_encounter_type.name,
                'name': random_encounter.name
            })
        thing_data.append({
            'name': thing.name,
            'description': thing.description,
            'background': thing.background,
            'current_state': thing.current_state,
            'image': thing.image,
            'thing_type': thing.thing_type.name,
            'children': [child.name for child in thing.children.all()],
            'attribute_values': attributes,
            'links': links,
            'random_encounters': random_encounters,
            'random_attributes': [a.text for a in RandomAttribute.objects.filter(thing=thing)],
            'is_bookmarked': thing.is_bookmarked
        })
    return thing_data


def weight_presets_to_json(campaign):
    weight_presets = []
    for weight_preset in WeightPreset.objects.filter(campaign=campaign):
        weights = [{'name_to_weight': w.name_to_weight, 'weight': w.weight} for w in Weight.objects.filter(weight_preset=weight_preset)]
        weight_presets.append({
            'name': weight_preset.name,
            'is_active': weight_preset.is_active,
            'attribute_name': weight_preset.attribute_name,
            'weights': weights
        })
    return weight_presets


def get_campaign_json(campaign):
    return {
        'things': campaign_to_json(campaign),
        'weight_presets': weight_presets_to_json(campaign)
    }


def save_campaign(campaign, json_file):
    Thing.objects.filter(campaign=campaign).delete()
    data = json.loads(json_file)
    for thing in data['things']:
        thing_object = Thing(campaign=campaign,
                             name=thing['name'],
                             description=thing['description'],
                             background=thing['background'],
                             current_state=thing['current_state'],
                             image=thing['image'],
                             thing_type=ThingType.objects.get(name=thing['thing_type']),
                             is_bookmarked=thing['is_bookmarked'])
        thing_object.save()

        for attribute in thing['attribute_values']:
            attr_value_object = AttributeValue(thing=thing_object, attribute=Attribute.objects.get(name=attribute['attribute'], thing_type=thing_object.thing_type), value=attribute['value'])
            attr_value_object.save()

        for link in thing['links']:
            link_object = UsefulLink(thing=thing_object, name=link['name'], value=link['value'])
            link_object.save()

        for random_encounter in thing['random_encounters']:
            random_encounter_object = RandomEncounter(thing=thing_object, random_encounter_type=RandomEncounterType.objects.get(name=random_encounter['random_encounter_type']), name=random_encounter['name'])
            random_encounter_object.save()

        for random_attribute in thing['random_attributes']:
            random_attribute_object = RandomAttribute(thing=thing_object, text=random_attribute)
            random_attribute_object.save()

    for thing in data['things']:
        thing_object = Thing.objects.get(campaign=campaign, name=thing['name'])
        for child in thing['children']:
            thing_object.children.add(Thing.objects.get(campaign=campaign, name=child))
        thing_object.save()

    WeightPreset.objects.filter(campaign=campaign).delete()
    for weight_preset in data['weight_presets']:
        preset = WeightPreset(name=weight_preset['name'], attribute_name=weight_preset['attribute_name'],
                              is_active=weight_preset['is_active'], campaign=campaign)
        preset.save()
        for weight in weight_preset['weights']:
            weight_object = Weight(weight_preset=preset, name_to_weight=weight['name_to_weight'],
                                   weight=weight['weight'])
            weight_object.save()


def thing_settings_to_json():
    thing_data = []
    for thing_type in ThingType.objects.all():
        attributes = []
        for attribute in RandomizerAttribute.objects.filter(thing_type=thing_type).order_by('name'):
            categories = []
            for category in RandomizerAttributeCategory.objects.filter(attribute=attribute).order_by('name'):
                category_options = [o.name for o in RandomizerAttributeCategoryOption.objects.filter(category=category).order_by('name')]
                use_values_from = []
                for category_for_values in category.use_values_from.all():
                    use_values_from.append(category_for_values.name)
                categories.append({
                    'name': category.name,
                    'show': category.show,
                    'can_combine_with_self': category.can_combine_with_self,
                    'max_options_to_use': category.max_options_to_use,
                    'can_randomize_later': category.can_randomize_later,
                    'must_be_unique': category.must_be_unique,
                    'use_values_from': use_values_from,
                    'options': category_options
                })
            attribute_data = {
                'name': attribute.name,
                'concatenate_results': attribute.concatenate_results,
                'can_randomize_later': attribute.can_randomize_later,
                'must_be_unique': attribute.must_be_unique,
                'categories': categories,
                'options': [o.name for o in RandomizerAttributeOption.objects.filter(attribute=attribute).order_by('name')]
            }
            if attribute.category_parameter:
                attribute_data['category_parameter'] = attribute.category_parameter.name
            else:
                attribute_data['category_parameter'] = None
            attributes.append(attribute_data)
        thing_data.append({
            'name': thing_type.name,
            'attributes': attributes
        })
    return thing_data


def generator_settings_to_json():
    generator_data = []
    for generator_object in GeneratorObject.objects.all():
        contains = []
        for object_contains in GeneratorObjectContains.objects.filter(generator_object=generator_object):
            contains.append({
                'name': object_contains.contained_object.name,
                'min_objects': object_contains.min_objects,
                'max_objects': object_contains.max_objects
            })
        mappings = []
        for mapping in GeneratorObjectFieldToRandomizerAttribute.objects.filter(generator_object=generator_object):
            mapping_data = {
                'field_name': mapping.field_name,
                'randomizer_attribute': None,
                'randomizer_attribute_category': None
            }
            if mapping.randomizer_attribute:
                mapping_data['randomizer_attribute'] = mapping.randomizer_attribute.name
            if mapping.randomizer_attribute_category:
                mapping_data['randomizer_attribute_category'] = '{0}.{1}'.format(mapping.randomizer_attribute_category.attribute.name, mapping.randomizer_attribute_category.name)
            mappings.append(mapping_data)
        generator_object_data = {
            'name': generator_object.name,
            'thing_type': generator_object.thing_type.name,
            'generator_object_contains': contains,
            'attribute_for_container': generator_object.attribute_for_container,
            'generator_object_field_to_randomizers': mappings
        }
        if generator_object.inherit_settings_from:
            generator_object_data['inherit_settings_from'] = generator_object.inherit_settings_from.name
        else:
            generator_object_data['inherit_settings_from'] = None
        generator_data.append(generator_object_data)
    return generator_data


def get_settings_json():
    return {
        'thing_types': thing_settings_to_json(),
        'generators': generator_settings_to_json()
    }


def save_settings(json_file):
    data = json.loads(json_file)
    for thing_type_data in data['thing_types']:
        thing_type = ThingType.objects.get(name=thing_type_data['name'])
        for attribute in thing_type_data['attributes']:
            RandomizerAttribute.objects.filter(thing_type=thing_type, name=attribute['name']).delete()
            randomizer_attribute = RandomizerAttribute(thing_type=thing_type,
                                                       name=attribute['name'],
                                                       concatenate_results=attribute['concatenate_results'],
                                                       can_randomize_later=attribute['can_randomize_later'],
                                                       must_be_unique=attribute['must_be_unique'])
            randomizer_attribute.save()

            for attribute_option in attribute['options']:
                randomizer_attribute_option = RandomizerAttributeOption(attribute=randomizer_attribute,
                                                                        name=attribute_option)
                randomizer_attribute_option.save()

            for attribute_category in attribute['categories']:
                randomizer_attribute_category = RandomizerAttributeCategory(attribute=randomizer_attribute,
                                                                            name=attribute_category['name'],
                                                                            show=attribute_category['show'],
                                                                            can_combine_with_self=attribute_category['can_combine_with_self'],
                                                                            max_options_to_use=attribute_category['max_options_to_use'],
                                                                            can_randomize_later=attribute_category['can_randomize_later'],
                                                                            must_be_unique=attribute['must_be_unique'])
                randomizer_attribute_category.save()

                for category_option in attribute_category['options']:
                    randomizer_attribute_category_option = RandomizerAttributeCategoryOption(category=randomizer_attribute_category,
                                                                                             name=category_option)
                    randomizer_attribute_category_option.save()

        for attribute in thing_type_data['attributes']:
            randomizer_attribute = RandomizerAttribute.objects.get(thing_type=thing_type, name=attribute['name'])
            if attribute['category_parameter']:
                randomizer_attribute.category_parameter = RandomizerAttribute.objects.get(thing_type=thing_type, name=attribute['category_parameter'])
                randomizer_attribute.save()
            for category in attribute['categories']:
                randomizer_attribute_category = RandomizerAttributeCategory.objects.get(attribute=randomizer_attribute, name=category['name'])
                if category['use_values_from']:
                    for value in category['use_values_from']:
                        value_attribute = RandomizerAttributeCategory.objects.get(attribute=randomizer_attribute, name=value)
                        randomizer_attribute_category.use_values_from.add(value_attribute)
                        randomizer_attribute_category.save()

    GeneratorObject.objects.all().delete()
    for generator_data in data['generators']:
        thing_type = ThingType.objects.get(name=generator_data['thing_type'])
        generator_object = GeneratorObject(name=generator_data['name'],
                                           thing_type=thing_type,
                                           attribute_for_container=generator_data['attribute_for_container'])
        generator_object.save()

        for mapping in generator_data['generator_object_field_to_randomizers']:
            randomizer_attribute = None
            randomizer_attribute_category = None

            if mapping['randomizer_attribute']:
                randomizer_attribute = RandomizerAttribute.objects.get(thing_type=thing_type, name=mapping['randomizer_attribute'])
            if mapping['randomizer_attribute_category']:
                parts = mapping['randomizer_attribute_category'].split('.')
                attribute = RandomizerAttribute.objects.get(thing_type=thing_type, name=parts[0])
                randomizer_attribute_category = RandomizerAttributeCategory.objects.get(attribute=attribute, name=parts[1])

            generator_object_field_to_randomizer_attribute = GeneratorObjectFieldToRandomizerAttribute(generator_object=generator_object,
                                                                                                       field_name=mapping['field_name'],
                                                                                                       randomizer_attribute=randomizer_attribute,
                                                                                                       randomizer_attribute_category=randomizer_attribute_category)
            generator_object_field_to_randomizer_attribute.save()

    for generator_data in data['generators']:
        thing_type = ThingType.objects.get(name=generator_data['thing_type'])
        generator_object = GeneratorObject.objects.get(thing_type=thing_type, name=generator_data['name'])

        if generator_data['inherit_settings_from']:
            generator_object.inherit_settings_from = GeneratorObject.objects.get(thing_type=thing_type, name=generator_data['inherit_settings_from'])
            generator_object.save()
        for contains in generator_data['generator_object_contains']:
            contained_object = GeneratorObject.objects.get(name=contains['name'])
            contains_entry = GeneratorObjectContains(generator_object=generator_object,
                                                     contained_object=contained_object,
                                                     min_objects=contains['min_objects'],
                                                     max_objects=contains['max_objects'])
            contains_entry.save()
