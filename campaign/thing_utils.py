import random
import re
from operator import methodcaller

from .models import Thing, ThingType, RandomEncounter, RandomizerAttribute, Attribute, UsefulLink, RandomAttribute, AttributeValue, RandomEncounterType
from .randomizers import get_random_attribute_raw, get_random_attribute_in_category_raw


def get_js_class(name, value):
    return re.sub(r'\W+', '-', '{0}-{1}'.format(name, value))


def get_attributes_to_display(campaign, thing):
    attributes_to_display = []
    attribute_values = AttributeValue.objects.filter(thing=thing, attribute__display_in_summary=True).order_by('attribute__name')
    for attribute_value in attribute_values:
        attributes_to_display.append({
            'name': attribute_value.attribute.name,
            'value': attribute_value.value,
            'can_link': attribute_value.attribute.is_thing,
            'js_class': get_js_class(attribute_value.attribute.name, attribute_value.value)
        })

    parent_location = get_parent_location(campaign=campaign, thing=thing)
    if parent_location:
        attributes_to_display.append({
            'name': 'Location',
            'value': parent_location,
            'can_link': True,
            'js_class': get_js_class('Location', parent_location)
        })
    return attributes_to_display


def get_parent_location(campaign, thing):
    parents = Thing.objects.filter(campaign=campaign, children=thing, thing_type__name='Location').order_by('name')
    if len(parents) == 0:
        return None
    else:
        return parents[0].name


def get_details(campaign, thing):
    parent_locations = []
    parent_factions = []
    for parent in Thing.objects.filter(campaign=campaign, children=thing).order_by('name'):
        if parent.thing_type.name == 'Location':
            parent_locations.append({
                'name': parent.name,
                'description': parent.description,
                'attributes': get_attributes_to_display(campaign=campaign, thing=parent)
            })
        elif parent.thing_type.name == 'Faction':
            parent_factions.append({
                'name': parent.name,
                'description': parent.description,
                'attributes': get_attributes_to_display(campaign=campaign, thing=parent)
            })

    child_locations = []
    child_factions = []
    child_npcs = []
    for child in thing.children.order_by('name'):
        if child.thing_type.name == 'Location':
            child_locations.append({
                'name': child.name,
                'description': child.description,
                'attributes': get_attributes_to_display(campaign=campaign, thing=child)
            })
        elif child.thing_type.name == 'Faction':
            child_factions.append({
                'name': child.name,
                'description': child.description,
                'attributes': get_attributes_to_display(campaign=campaign, thing=child)
            })
        elif child.thing_type.name == 'NPC':
            child_npcs.append({
                'name': child.name,
                'description': child.description,
                'attributes': get_attributes_to_display(campaign=campaign, thing=child)
            })

    encounter_types = [t.name for t in RandomEncounterType.objects.all()]
    encounter_types.sort()
    encounters = []
    display_encounters = False
    for encounter_type in encounter_types:
        random_encounters = RandomEncounter.objects.filter(thing=thing, random_encounter_type__name=encounter_type)
        if random_encounters:
            display_encounters = True
        encounters.append({
            'count': len(random_encounters),
            'encounter_type': encounter_type,
            'list': random_encounters
        })

    editable_attributes = [a.name for a in Attribute.objects.filter(thing_type=thing.thing_type, display_in_summary=True).order_by('name')]

    random_attributes = [{'text': r.text, 'id': r.pk} for r in RandomAttribute.objects.filter(thing=thing).order_by('text')]
    randomizable_attributes = [a.name for a in RandomizerAttribute.objects.filter(thing_type=thing.thing_type, can_randomize_later=True).order_by('name')]

    thing_info = {
        'name': thing.name,
        'thing_type': thing.thing_type.name,
        'description': thing.description,
        'attributes': get_attributes_to_display(campaign=campaign, thing=thing),
        'useful_links': UsefulLink.objects.filter(thing=thing).order_by('name'),
        'random_attributes': random_attributes,
        'encounters': encounters,
        'display_encounters': display_encounters,
        'enable_random_encounters': thing.thing_type.name == 'Location',
        'editable_attributes': editable_attributes,
        'randomizable_attributes': randomizable_attributes,
        'is_bookmarked': thing.is_bookmarked,
        'show_name_randomizer': len(AttributeValue.objects.filter(attribute__name='Name Randomizer', thing=thing)) > 0,
        'parent_locations': parent_locations,
        'parent_factions': parent_factions,
        'child_locations': child_locations,
        'child_factions': child_factions,
        'child_npcs': child_npcs
    }

    attribute_values = AttributeValue.objects.filter(thing=thing, attribute__display_in_summary=False).order_by('attribute__name')
    for attribute_value in attribute_values:
        thing_info[attribute_value.attribute.name.lower()] = attribute_value.value

    return thing_info


def get_attribute_filters(list_data):
    attribute_filter = {}

    for thing_type in list_data:
        for thing in thing_type['things']:
            for attribute_value in thing['attributes']:
                if attribute_value['name'] in attribute_filter:
                    if attribute_value['value'] not in attribute_filter[attribute_value['name']]:
                        attribute_filter[attribute_value['name']].append(attribute_value['value'])
                else:
                    attribute_filter[attribute_value['name']] = [attribute_value['value']]

    for attribute_name in attribute_filter.keys():
        values_with_js_classes = []
        for value in attribute_filter[attribute_name]:
            values_with_js_classes.append({
                'value': value,
                'class': get_js_class(attribute_name, value)
            })
        attribute_filter[attribute_name] = values_with_js_classes
    return attribute_filter


def order_attribute_filters(attribute_filters):
    ordered_filters = []
    for attribute, values in attribute_filters.items():
        ordered_filters.append({
            'name': attribute,
            'values': values
        })

    for attribute_filter in ordered_filters:
        sorted_values = sorted(attribute_filter['values'], key=methodcaller('get', 'value'))
        attribute_filter['values'] = sorted_values
    return sorted(ordered_filters, key=methodcaller('get', 'name'))


def get_list_data(campaign, thing_type):
    if thing_type:
        types = [thing_type]
    else:
        types = [thing.name for thing in ThingType.objects.all()]

    list_data = []

    for t in types:
        data_for_type = []
        for thing in Thing.objects.filter(campaign=campaign, thing_type__name__iexact=t).order_by('name'):
            data_for_type.append({
                'name': thing.name,
                'description': thing.description,
                'attributes': get_attributes_to_display(campaign=campaign, thing=thing)
            })
        list_data.append({
            'name': '{0}s'.format(t),
            'things': data_for_type
        })

    return list_data


def get_filters(list_data):
    return order_attribute_filters(get_attribute_filters(list_data))


def save_new_location(campaign, form_data):
    thing = Thing(campaign=campaign, name=form_data['name'], description=form_data['description'], thing_type=ThingType.objects.get(name='Location'))
    thing.save()

    children = []
    children.extend(form_data['factions'])
    children.extend(form_data['npcs'])

    for child in children:
        current_parent_locations = Thing.objects.filter(campaign=campaign, children=child, thing_type__name='Location')
        for parent in current_parent_locations:
            parent.children.remove(child)
            parent.save()
        thing.children.add(child)
    thing.save()

    new_parent = form_data['location']

    if new_parent:
        new_parent.children.add(thing)
        new_parent.save()

    if form_data['ruler']:
        ruler = AttributeValue(thing=thing, attribute=Attribute.objects.get(name='Ruler'), value=form_data['ruler'])
        ruler.save()

    if form_data['population']:
        randomized_population = '{:,}'.format(int(int(form_data['population'])*random.randint(5, 15)/10))
        population = AttributeValue(thing=thing, attribute=Attribute.objects.get(name='Population'), value=str(randomized_population))
        population.save()

    if form_data['generate_rumours']:
        randomizer_attribute = RandomizerAttribute.objects.get(thing_type=thing.thing_type, name='Rumour')

        for i in range(0, random.randint(1, randomizer_attribute.max_options_to_use)):
            option = get_random_attribute_raw(campaign=campaign, thing_type=thing.thing_type, attribute=randomizer_attribute.name)
            if option:
                random_attribute = RandomAttribute(thing=thing, text=option)
                random_attribute.save()
    return thing


def save_new_faction(campaign, form_data):
    thing = Thing(campaign=campaign, name=form_data['name'], description=form_data['description'], thing_type=ThingType.objects.get(name='Faction'))
    thing.save()

    for child in form_data['npcs']:
        thing.children.add(child)
    thing.save()

    new_parent = form_data['location']
    if new_parent:
        new_parent.children.add(thing)
        new_parent.save()

    if form_data['leader']:
        leader = AttributeValue(thing=thing, attribute=Attribute.objects.get(name='Leader'), value=form_data['leader'])
        leader.save()
        leader_thing = Thing.objects.get(campaign=campaign, thing_type__name='NPC', name=form_data['leader'])
        if not leader_thing in thing.children.all():
            thing.children.add(leader_thing)
            thing.save()

    if form_data['attitude']:
        attitude = AttributeValue(thing=thing, attribute=Attribute.objects.get(name='Attitude', thing_type__name='Faction'), value=form_data['attitude'])
        attitude.save()

    if form_data['power']:
        power = AttributeValue(thing=thing, attribute=Attribute.objects.get(name='Power'), value=form_data['power'])
        power.save()

    if form_data['reach']:
        reach = AttributeValue(thing=thing, attribute=Attribute.objects.get(name='Reach'), value=form_data['reach'])
        reach.save()
    return thing


def save_new_npc(campaign, form_data):
    thing = Thing(campaign=campaign, name=form_data['name'], description=form_data['description'], thing_type=ThingType.objects.get(name='NPC'))
    thing.save()

    new_parents = []
    if form_data['location']:
        new_parents.append(form_data['location'])
    new_parents.extend(form_data['factions'])
    for new_parent in new_parents:
        new_parent.children.add(thing)
        new_parent.save()

    if form_data['race']:
        race = AttributeValue(thing=thing, attribute=Attribute.objects.get(name='Race'), value=form_data['race'])
        race.save()

    if form_data['attitude']:
        attitude = AttributeValue(thing=thing, attribute=Attribute.objects.get(name='Attitude', thing_type__name='NPC'), value=form_data['attitude'])
        attitude.save()

    if form_data['occupation']:
        occupation = AttributeValue(thing=thing, attribute=Attribute.objects.get(name='Occupation'), value=form_data['occupation'])
        occupation.save()

    if form_data['link']:
        link = AttributeValue(thing=thing, attribute=Attribute.objects.get(name='Link'), value=form_data['link'])
        link.save()

    if form_data['generate_hooks']:
        randomizer_attribute = RandomizerAttribute.objects.get(thing_type=thing.thing_type, name='Hook')

        for i in range(0, random.randint(1, randomizer_attribute.max_options_to_use)):
            option = get_random_attribute_raw(campaign=campaign, thing_type=thing.thing_type, attribute=randomizer_attribute.name)
            if option:
                random_attribute = RandomAttribute(thing=thing, text=option)
                random_attribute.save()

    return thing


def randomize_name_for_thing(campaign, name, thing):
    name_pieces = name.split(' ')
    try:
        name_randomizer = AttributeValue.objects.get(attribute__name='Name Randomizer', thing=thing)
    except AttributeValue.DoesNotExist:
        name_randomizer = None

    if name_randomizer:
        thing.name = get_random_attribute_in_category_raw(thing.thing_type, 'name', AttributeValue.objects.get(attribute__name='Name Randomizer', thing=thing).value)
        new_name_pieces = thing.name.split(' ')
        thing.description = thing.description.replace(name_pieces[0], new_name_pieces[0])
        if len(name_pieces) > 1:
            thing.description.replace(name_pieces[1], new_name_pieces[1])
        thing.save()

        print('Regenerating name for {0}: {1}'.format(name, thing.name))
        if thing.thing_type.name == 'NPC':
            try:
                faction = Thing.objects.get(campaign=campaign, thing_type__name='Faction', children=thing)
                try:
                    leader = AttributeValue.objects.get(attribute__name='Leader', thing=faction)
                    leader.value = leader.value.replace(name_pieces[0], new_name_pieces[0]).replace(name_pieces[1], new_name_pieces[1])
                    leader.save()
                    print('Updated leader attribute of {0}: {1}'.format(faction.name, leader.value))
                except AttributeValue.DoesNotExist:
                    pass
            except Thing.DoesNotExist:
                pass
            try:
                location = Thing.objects.get(campaign=campaign, thing_type__name='Location', children=thing)
                try:
                    ruler = AttributeValue.objects.get(attribute__name='Ruler', thing=location)
                    ruler.value = ruler.value.replace(name_pieces[0], new_name_pieces[0]).replace(name_pieces[1], new_name_pieces[1])
                    ruler.save()
                    print('Updated ruler attribute of {0}: {1}'.format(location.name, ruler.value))
                except AttributeValue.DoesNotExist:
                    pass
            except Thing.DoesNotExist:
                pass
        elif thing.thing_type.name == 'Location':
            try:
                ruler = AttributeValue.objects.get(attribute__name='Ruler', thing=thing)
                npc = Thing.objects.get(thing_type__name='NPC', name=ruler.value)
                npc_occupation = AttributeValue.objects.get(attribute__name='Occupation', thing=npc)
                npc_occupation.value = npc_occupation.value.replace(name_pieces[0], new_name_pieces[0])
                if len(name_pieces) > 1:
                    npc_occupation.value.replace(name_pieces[1], new_name_pieces[1])
                npc_occupation.save()
                print('Updated occupation of {0}: {1}'.format(npc.name, npc_occupation.value))
            except AttributeValue.DoesNotExist:
                pass
        elif thing.thing_type.name == 'Faction':
            try:
                leader = AttributeValue.objects.get(attribute__name='Leader', thing=thing)
                npc = Thing.objects.get(thing_type__name='NPC', name=leader.value)
                npc_occupation = AttributeValue.objects.get(attribute__name='Occupation', thing=npc)
                npc_occupation.value = npc_occupation.value.replace(name_pieces[0], new_name_pieces[0])
                if len(name_pieces) > 1:
                    npc_occupation.value.replace(name_pieces[1], new_name_pieces[1])
                npc_occupation.save()
                print('Updated occupation of {0}: {1}'.format(npc.name, npc_occupation.value))
            except AttributeValue.DoesNotExist:
                pass
    else:
        print('Cannot randomize name for {0}: no name randomizer set (likely not a generated object).'.format(thing.name))