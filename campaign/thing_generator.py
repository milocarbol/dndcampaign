import random
import re

from django.db import IntegrityError

from .models import Attribute, AttributeValue, GeneratorObjectContains, Thing, RandomizerAttribute, GeneratorObjectFieldToRandomizerAttribute, GeneratorObject, RandomizerAttributeCategory
from .randomizers import get_random_attribute_raw, get_random_attribute_in_category_raw, generate_random_attributes_for_thing_raw

CONTAINS_REGEX = r'^(([\d]+)(-(\d+))? )?(([\w ]+)\.([\w ]+))$'
MAPPING_REGEX = r'^((\w+): )?([\w ]+)(\.([\w ]+))?$'
VARIABLE_REGEX = r'\$\{([^\}]+)\}'


def generate_thing(generator_object, campaign, parent_object=None):
    print('Generating {0}...'.format(generator_object.name))
    thing = Thing(thing_type=generator_object.thing_type, campaign=campaign)

    fields_to_save = {
        'thing': [],
        'attribute_values': [],
        'random_attributes': []
    }

    field_mappings = []
    inherit_settings_from = generator_object
    while inherit_settings_from is not None:
        inherited_settings = GeneratorObjectFieldToRandomizerAttribute.objects.filter(generator_object=inherit_settings_from)
        for inherited_setting in inherited_settings:
            is_overridden = False
            for field_mapping in field_mappings:
                if field_mapping.field_name and field_mapping.field_name == inherited_setting.field_name \
                        or field_mapping.randomizer_attribute \
                                and field_mapping.randomizer_attribute == inherited_setting.randomizer_attribute \
                        or field_mapping.randomizer_attribute_category and inherited_setting.randomizer_attribute_category \
                                and field_mapping.randomizer_attribute_category.attribute == inherited_setting.randomizer_attribute_category.attribute:
                    is_overridden = True
                    break
            if not is_overridden:
                field_mappings.append(inherited_setting)
        inherit_settings_from = inherit_settings_from.inherit_settings_from
    for field_mapping in field_mappings:
        if field_mapping.randomizer_attribute:
            if field_mapping.randomizer_attribute.category_parameter:
                parameter = get_random_attribute_raw(campaign, generator_object.thing_type, field_mapping.randomizer_attribute.category_parameter.name)
                attribute = Attribute.objects.get(thing_type=generator_object.thing_type, name=field_mapping.randomizer_attribute.category_parameter.name)
                fields_to_save['attribute_values'].append({
                    'attribute': attribute,
                    'value': parameter
                })
                value = get_random_attribute_in_category_raw(thing_type=generator_object.thing_type, attribute=field_mapping.randomizer_attribute.name, category=parameter)
                while field_mapping.randomizer_attribute.must_be_unique and len(Thing.objects.filter(campaign=campaign, name=value)) > 0:
                    print('Tried to use {0} but was in use'.format(value))
                    value = get_random_attribute_in_category_raw(thing_type=generator_object.thing_type, attribute=field_mapping.randomizer_attribute.name, category=parameter)
            else:
                value = get_random_attribute_raw(campaign=campaign, thing_type=thing.thing_type, attribute=field_mapping.randomizer_attribute.name)
                while field_mapping.randomizer_attribute.must_be_unique and len(Thing.objects.filter(campaign=campaign, name=value)) > 0:
                    print('Tried to use {0} but was in use'.format(value))
                    value = get_random_attribute_raw(campaign=campaign, thing_type=thing.thing_type, attribute=field_mapping.randomizer_attribute.name)
        else:
            value = get_random_attribute_in_category_raw(thing_type=thing.thing_type, attribute=field_mapping.randomizer_attribute_category.attribute.name, category=field_mapping.randomizer_attribute_category.name)
            while field_mapping.randomizer_attribute_category.must_be_unique and len(Thing.objects.filter(campaign=campaign, name=value)) > 0:
                print('Tried to use {0} but was in use'.format(value))
                value = get_random_attribute_in_category_raw(thing_type=thing.thing_type, attribute=field_mapping.randomizer_attribute_category.attribute.name, category=field_mapping.randomizer_attribute_category.name)

        if field_mapping.field_name:
            fields_to_save['thing'].append({
                'name': field_mapping.field_name,
                'value': value
            })
        elif field_mapping.randomizer_attribute:
            if field_mapping.randomizer_attribute.can_randomize_later:
                fields_to_save['random_attributes'].append(field_mapping.randomizer_attribute)
            else:
                attribute = Attribute.objects.get(thing_type=generator_object.thing_type, name=field_mapping.randomizer_attribute.name)
                if value:
                    fields_to_save['attribute_values'].append({
                        'attribute': attribute,
                        'value': value
                    })
        elif field_mapping.randomizer_attribute_category:
            attribute = Attribute.objects.get(thing_type=generator_object.thing_type, name=field_mapping.randomizer_attribute_category.attribute.name)
            if value:
                fields_to_save['attribute_values'].append({
                    'attribute': attribute,
                    'value': value
                })

    for field in fields_to_save['thing']:
        if field['value']:
            var_search = re.findall(VARIABLE_REGEX, field['value'])
            if var_search:
                for variable in var_search:
                    if '.' in variable:
                        parts = variable.split('.')
                        if parts[0] == 'parent' and parent_object:
                            try:
                                parent_value = getattr(parent_object, parts[1])
                            except AttributeError:
                                parent_value = AttributeValue.objects.get(attribute__name__iexact=parts[1], thing=parent_object).value
                            field['value'] = re.sub(r'\$\{' + variable + '\}', parent_value, field['value'])
                    else:
                        for thing_field in fields_to_save['thing']:
                            if thing_field['name'] == variable:
                                field['value'] = re.sub(r'\$\{' + variable + '\}', thing_field['value'], field['value'])
                                break
                        for thing_field in fields_to_save['attribute_values']:
                            if thing_field['attribute'].name.lower() == variable.lower():
                                field['value'] = re.sub(r'\$\{' + variable + '\}', thing_field['value'], field['value'])
                                break
            setattr(thing, field['name'], field['value'])

    try:
        if thing.name:
            thing.save()
        else:
            print('Could not save {0}: likely a configuration error. Are all variables populated?'.format(fields_to_save))
            return None
    except IntegrityError:
        print('Failed to save {0}: already exists.'.format(thing.name))
        return None

    for attribute_value_data in fields_to_save['attribute_values']:
        var_search = re.search(VARIABLE_REGEX, attribute_value_data['value'])
        if var_search:
            variable = var_search.group(1)
            if '.' in variable:
                parts = variable.split('.')
                if parts[0] == 'parent' and parent_object:
                    try:
                        parent_value = getattr(parent_object, parts[1])
                    except AttributeError:
                        parent_value = AttributeValue.objects.get(attribute__name__iexact=parts[1], thing=parent_object).value
                    attribute_value_data['value'] = re.sub(r'\$\{.+\}', parent_value, attribute_value_data['value'])
        attribute_value = AttributeValue(thing=thing, attribute=attribute_value_data['attribute'], value=attribute_value_data['value'])
        attribute_value.save()

    name_randomizer_attribute = Attribute.objects.get(thing_type=thing.thing_type, name='Name Randomizer')
    name_randomizer = AttributeValue(thing=thing, attribute=name_randomizer_attribute)
    if thing.thing_type.name == 'NPC':
        name_randomizer.value = AttributeValue.objects.get(thing=thing, attribute__name='Race').value
    elif thing.thing_type.name == 'Faction' or thing.thing_type.name == 'Location':
        name_randomizer.value = generator_object.name
    name_randomizer.save()

    for attribute in fields_to_save['random_attributes']:
        randomizer_attribute = RandomizerAttribute.objects.get(thing_type=thing.thing_type, name__iexact=attribute.name)
        generate_random_attributes_for_thing_raw(campaign=campaign, thing=thing, attribute=randomizer_attribute)

    children = GeneratorObjectContains.objects.filter(generator_object=generator_object)
    for child in children:
        for i in range(0, random.randint(child.min_objects, child.max_objects)):
            child_object = generate_thing(child.contained_object, campaign, thing)
            if not child_object:
                continue
            print('Adding {0} to {1}...'.format(child_object.name, thing.name))
            thing.children.add(child_object)
            thing.save()
            if thing.thing_type.name == 'Location':
                for child_faction in thing.children.filter(thing_type__name='Faction'):
                    for faction_npc in child_faction.children.filter(thing_type__name='NPC'):
                        thing.children.add(faction_npc)
                        thing.save()
            attribute_for_container = child.contained_object.attribute_for_container
            inherit_settings_from = child.contained_object.inherit_settings_from
            while not attribute_for_container and inherit_settings_from:
                attribute_for_container = inherit_settings_from.attribute_for_container
                inherit_settings_from = inherit_settings_from.inherit_settings_from
            if attribute_for_container:
                print('Setting {0} for {1} to {2}...'.format(attribute_for_container, thing.name, child_object.name))
                attribute = Attribute.objects.get(thing_type=thing.thing_type, name__iexact=attribute_for_container)
                attribute_value = AttributeValue(thing=thing, attribute=attribute, value=child_object.name)
                attribute_value.save()

                var_search = re.search(VARIABLE_REGEX, thing.name)
                if var_search:
                    variable = var_search.group(1)
                    if variable == attribute_for_container:
                        new_name = re.sub(r'\$\{.+\}', child_object.name, thing.name)
                        print('Changing {0} to {1}'.format(thing.name, new_name))
                        thing.name = new_name
                        thing.save()

    return thing


def save_containers(generator_object, container_text):
    for container in container_text.split('\n'):
        container = container.strip()
        contains_search = re.search(CONTAINS_REGEX, container)
        if contains_search:
            min = contains_search.group(2) or 1
            max = contains_search.group(4) or 1
            thing_type_name = contains_search.group(6)
            contained_name = contains_search.group(7)
            contained_object = GeneratorObject.objects.get(thing_type__name__iexact=thing_type_name,
                                                           name__iexact=contained_name)
            object_contains = GeneratorObjectContains(generator_object=generator_object,
                                                      contained_object=contained_object,
                                                      min_objects=min,
                                                      max_objects=max)
            object_contains.save()


def save_mappings(generator_object, mapping_text):
    for mapping in mapping_text.split('\n'):
        mapping = mapping.strip()
        mapping_search = re.search(MAPPING_REGEX, mapping)
        if mapping_search:
            field_name = mapping_search.group(2)
            attribute_name = mapping_search.group(3)
            category_name = mapping_search.group(5)

            attribute = None
            category = None
            if attribute_name:
                attribute = RandomizerAttribute.objects.get(thing_type=generator_object.thing_type,
                                                            name__iexact=attribute_name)
                if category_name:
                    category = RandomizerAttributeCategory.objects.get(attribute=attribute,
                                                                       name__iexact=category_name)
            if category:
                generator_object_mapping = GeneratorObjectFieldToRandomizerAttribute(generator_object=generator_object,
                                                                                     field_name=field_name,
                                                                                     randomizer_attribute_category=category)
                generator_object_mapping.save()
            elif attribute:
                generator_object_mapping = GeneratorObjectFieldToRandomizerAttribute(generator_object=generator_object,
                                                                                     field_name=field_name,
                                                                                     randomizer_attribute=attribute)
                generator_object_mapping.save()
            else:
                generator_object_mapping = GeneratorObjectFieldToRandomizerAttribute(generator_object=generator_object,
                                                                                     field_name=field_name)
                generator_object_mapping.save()
                
                
def save_new_generator(thing_type, form_data):
    generator_object = GeneratorObject(name=form_data['name'], thing_type=thing_type,
                                               inherit_settings_from=form_data['inherit_settings_from'],
                                               attribute_for_container=form_data['attribute_for_container'])
    generator_object.save()

    save_containers(generator_object, form_data['contains'])
    save_mappings(generator_object, form_data['mappings'])
    
    return generator_object


def edit_generator(generator_object, form_data):
    GeneratorObjectContains.objects.filter(generator_object=generator_object).delete()
    GeneratorObjectFieldToRandomizerAttribute.objects.filter(generator_object=generator_object).delete()
    save_containers(generator_object, form_data['contains'])
    save_mappings(generator_object, form_data['mappings'])
    return generator_object
