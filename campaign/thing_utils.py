import logging
import random
import re
from operator import methodcaller

from .generator_utils import VARIABLE_REGEX
from .models import Thing, ThingType, RandomEncounter, RandomizerAttribute, Attribute, UsefulLink, RandomAttribute, AttributeValue, RandomEncounterType
from .randomizers import get_random_attribute_raw, get_random_attribute_in_category_raw


logger = logging.getLogger(__name__)


def get_js_class(name, value):
    return re.sub(r'\W+', '-', '{0}-{1}'.format(name, value))


def get_attributes_to_display(campaign, thing, include_location=True):
    attributes_to_display = []
    attribute_values = AttributeValue.objects.filter(thing=thing, attribute__display_in_summary=True).order_by('attribute__name')
    for attribute_value in attribute_values:
        attributes_to_display.append({
            'name': attribute_value.attribute.name,
            'value': attribute_value.value,
            'can_link': attribute_value.attribute.is_thing,
            'js_class': get_js_class(attribute_value.attribute.name, attribute_value.value)
        })

    if include_location:
        parent_location = get_parent_location(campaign=campaign, thing=thing)
        if parent_location:
            attributes_to_display.append({
                'name': 'Location',
                'value': parent_location,
                'can_link': True,
                'js_class': get_js_class('Location', parent_location)
            })
    return attributes_to_display


def get_basic_data_for_thing(campaign, thing):
    return {
        'name': thing.name,
        'description': thing.description,
        'attributes': get_attributes_to_display(campaign=campaign, thing=thing),
        'child_locations': thing.children.filter(thing_type__name='Location'),
        'child_npcs': thing.children.filter(thing_type__name='NPC'),
        'child_factions': thing.children.filter(thing_type__name='Faction')
    }


def get_parent_location(campaign, thing):
    parents = Thing.objects.filter(campaign=campaign, children=thing, thing_type__name='Location').order_by('name')
    if len(parents) == 0:
        return None
    else:
        return parents[0].name


def get_details(campaign, thing, include_location=True):
    parent_locations = []
    parent_factions = []
    for parent in Thing.objects.filter(campaign=campaign, children=thing).order_by('name'):
        if parent.thing_type.name == 'Location':
            parent_locations.append(get_details(campaign=campaign, thing=parent))
        elif parent.thing_type.name == 'Faction':
            parent_factions.append(get_details(campaign=campaign, thing=parent))

    child_locations = []
    child_factions = []
    child_npcs = []
    for child in thing.children.order_by('name'):
        if child.thing_type.name == 'Location':
            child_locations.append(get_basic_data_for_thing(campaign=campaign, thing=child))
        elif child.thing_type.name == 'Faction':
            child_factions.append(get_basic_data_for_thing(campaign=campaign, thing=child))
        elif child.thing_type.name == 'NPC':
            child_npcs.append(get_basic_data_for_thing(campaign=campaign, thing=child))

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

    attributes_to_display = [a.name for a in Attribute.objects.filter(thing_type=thing.thing_type, display_in_summary=True).order_by('name')]
    editable_attributes = [a.name for a in Attribute.objects.filter(thing_type=thing.thing_type, editable=True).order_by('name')]

    random_attributes = [{'text': r.text, 'id': r.pk} for r in RandomAttribute.objects.filter(thing=thing).order_by('text')]
    randomizable_attributes = [a.name for a in RandomizerAttribute.objects.filter(thing_type=thing.thing_type, can_randomize_later=True).order_by('name')]

    thing_info = {
        'name': thing.name,
        'thing_type': thing.thing_type.name,
        'description': thing.description,
        'background': thing.background,
        'current_state': thing.current_state,
        'attributes': get_attributes_to_display(campaign=campaign, thing=thing, include_location=include_location),
        'useful_links': UsefulLink.objects.filter(thing=thing).order_by('name'),
        'image': thing.image,
        'random_attributes': random_attributes,
        'encounters': encounters,
        'display_encounters': display_encounters,
        'enable_random_encounters': thing.thing_type.name == 'Location',
        'attributes_to_display': attributes_to_display,
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


def get_list_data(campaign, thing_type, bookmarks_only=False):
    if thing_type:
        types = [thing_type]
    else:
        types = [thing.name for thing in ThingType.objects.all()]

    list_data = []

    for t in types:
        data_for_type = []
        if bookmarks_only:
            things_to_show = Thing.objects.filter(campaign=campaign, thing_type__name__iexact=t, is_bookmarked=True).order_by('name')
        else:
            things_to_show = Thing.objects.filter(campaign=campaign, thing_type__name__iexact=t).order_by('name')

        for thing in things_to_show:
            data_for_type.append({
                'name': thing.name,
                'description': thing.description,
                'attributes': get_attributes_to_display(campaign=campaign, thing=thing),
                'child_locations': thing.children.filter(thing_type__name='Location'),
                'child_npcs': thing.children.filter(thing_type__name='NPC'),
                'child_factions': thing.children.filter(thing_type__name='Faction')
            })
        list_data.append({
            'name': '{0}s'.format(t),
            'things': data_for_type
        })

    return list_data


def get_filters(list_data):
    return order_attribute_filters(get_attribute_filters(list_data))


def save_new_location(campaign, form_data):
    thing = Thing(campaign=campaign,
                  name=form_data['name'],
                  description=form_data['description'],
                  background=form_data['background'],
                  current_state=form_data['current_state'],
                  thing_type=ThingType.objects.get(name='Location'))
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
    thing = Thing(campaign=campaign,
                  name=form_data['name'],
                  description=form_data['description'],
                  background=form_data['background'],
                  current_state=form_data['current_state'],
                  thing_type=ThingType.objects.get(name='Faction'))
    thing.save()

    for child in form_data['npcs']:
        thing.children.add(child)
    thing.save()

    new_parent = form_data['location']
    if new_parent:
        new_parent.children.add(thing)
        new_parent.save()

    if form_data['leader']:
        leader = AttributeValue(thing=thing, attribute=Attribute.objects.get(thing_type=thing.thing_type, name='Leader'), value=form_data['leader'])
        leader.save()
        leader_thing = Thing.objects.get(campaign=campaign, thing_type__name='NPC', name=form_data['leader'])
        if not leader_thing in thing.children.all():
            thing.children.add(leader_thing)
            thing.save()

    if form_data['attitude']:
        attitude = AttributeValue(thing=thing, attribute=Attribute.objects.get(thing_type=thing.thing_type, name='Attitude', thing_type__name='Faction'), value=form_data['attitude'])
        attitude.save()

    if form_data['power']:
        power = AttributeValue(thing=thing, attribute=Attribute.objects.get(thing_type=thing.thing_type, name='Power'), value=form_data['power'])
        power.save()

    if form_data['reach']:
        reach = AttributeValue(thing=thing, attribute=Attribute.objects.get(thing_type=thing.thing_type, name='Reach'), value=form_data['reach'])
        reach.save()
    return thing


def save_new_npc(campaign, form_data):
    thing = Thing(campaign=campaign,
                  name=form_data['name'],
                  description=form_data['description'],
                  background=form_data['background'],
                  current_state=form_data['current_state'],
                  thing_type=ThingType.objects.get(name='NPC'))
    thing.save()

    new_parents = []
    if form_data['location']:
        new_parents.append(form_data['location'])
    new_parents.extend(form_data['factions'])
    for new_parent in new_parents:
        new_parent.children.add(thing)
        new_parent.save()

    if form_data['race']:
        race = AttributeValue(thing=thing, attribute=Attribute.objects.get(thing_type=thing.thing_type, name='Race'), value=form_data['race'])
        race.save()

    if form_data['attitude']:
        attitude = AttributeValue(thing=thing, attribute=Attribute.objects.get(thing_type=thing.thing_type, name='Attitude', thing_type__name='NPC'), value=form_data['attitude'])
        attitude.save()

    if form_data['occupation']:
        occupation = AttributeValue(thing=thing, attribute=Attribute.objects.get(thing_type=thing.thing_type, name='Occupation'), value=form_data['occupation'])
        occupation.save()

    if form_data['link']:
        link = AttributeValue(thing=thing, attribute=Attribute.objects.get(thing_type=thing.thing_type, name='Link'), value=form_data['link'])
        link.save()

    if form_data['generate_hooks']:
        randomizer_attribute = RandomizerAttribute.objects.get(thing_type=thing.thing_type, name='Hook')

        for i in range(0, random.randint(1, randomizer_attribute.max_options_to_use)):
            option = get_random_attribute_raw(campaign=campaign, thing_type=thing.thing_type, attribute=randomizer_attribute.name)
            if option:
                random_attribute = RandomAttribute(thing=thing, text=option)
                random_attribute.save()

    return thing


def save_new_item(campaign, form_data):
    thing = Thing(campaign=campaign,
                  name=form_data['name'],
                  description=form_data['description'],
                  background=form_data['background'],
                  thing_type=ThingType.objects.get(name='Item'))
    thing.save()

    if form_data['link']:
        link = AttributeValue(thing=thing, attribute=Attribute.objects.get(thing_type=thing.thing_type, name='Link'), value=form_data['link'])
        link.save()

    return thing


def save_new_note(campaign, form_data):
    thing = Thing(campaign=campaign,
                  name=form_data['name'],
                  description=form_data['description'],
                  background=form_data['background'],
                  thing_type=ThingType.objects.get(name='Note'))
    thing.save()

    if form_data['link']:
        link = AttributeValue(thing=thing, attribute=Attribute.objects.get(thing_type=thing.thing_type, name='Link'), value=form_data['link'])
        link.save()

    return thing


def replace_variables_in_name(thing, name):
    var_search = re.findall(VARIABLE_REGEX, name)
    if var_search:
        for variable in var_search:
            if '.' in variable:
                parts = variable.split('.')
                if parts[0] == 'parent':
                    try:
                        parent_object = Thing.objects.get(campaign=thing.campaign, thing_type__name='Location', children=thing)
                    except Thing.DoesNotExist:
                        parent_object = None
                    if parent_object:
                        try:
                            parent_value = getattr(parent_object, parts[1])
                        except AttributeError:
                            parent_value = AttributeValue.objects.get(attribute__name__iexact=parts[1], thing=parent_object).value
                        return re.sub(r'\$\{' + variable + '\}', parent_value, name)
            else:
                for attribute_value in AttributeValue.objects.filter(thing=thing):
                    if attribute_value.attribute.name.lower() == variable:
                        return re.sub(r'\$\{' + variable + '\}', attribute_value.value, name)
    return name


def randomize_name_for_thing(thing):
    try:
        name_randomizer = AttributeValue.objects.get(attribute__name='Name Randomizer', thing=thing)
    except AttributeValue.DoesNotExist:
        name_randomizer = None

    if name_randomizer:
        new_name = None
        while not new_name or thing.name != new_name and Thing.objects.filter(name__iexact=new_name):
            if new_name:
                logger.debug('Tried randomizing {0} to {1} but it was in use.'.format(thing.name, new_name))
            else:
                logger.debug('Getting new name for {0}.'.format(thing.name))
            raw_name = get_random_attribute_in_category_raw(thing.thing_type, 'name', AttributeValue.objects.get(attribute__name='Name Randomizer', thing=thing).value)
            logger.debug('Got {0}'.format(raw_name))
            new_name = replace_variables_in_name(thing, raw_name)

        update_thing_name_and_all_related(thing, new_name)
    else:
        logger.info('Cannot randomize name for {0}: no name randomizer set (likely not a generated object).'.format(thing.name))


def update_value_in_string(string, old_value, new_value):
    new_string = string.replace(old_value, new_value)

    if ' ' in old_value:
        old_pieces = old_value.split(' ')
        new_pieces = new_value.split(' ')
        for i, piece in enumerate(old_pieces):
            if i >= len(new_pieces):
                break
            new_string = new_string.replace(piece, new_pieces[i])
    return new_string


def update_thing_name_and_all_related(thing, new_name, check_parents=True):
    name = thing.name

    thing.name = new_name
    thing.description = update_value_in_string(thing.description, name, new_name)
    thing.background = update_value_in_string(thing.background, name, new_name)
    thing.current_state = update_value_in_string(thing.current_state, name, new_name)
    thing.save()

    if thing.thing_type.name == 'NPC':
        try:
            faction = Thing.objects.get(campaign=thing.campaign, thing_type__name='Faction', children=thing)
            try:
                leader = AttributeValue.objects.get(attribute__name='Leader', thing=faction)
                leader.value = update_value_in_string(leader.value, name, new_name)
                leader.save()
                logger.info('Updated leader attribute of {0}: {1}'.format(faction.name, leader.value))
            except AttributeValue.DoesNotExist:
                pass
        except Thing.DoesNotExist:
            pass
        try:
            location = Thing.objects.get(campaign=thing.campaign, thing_type__name='Location', children=thing)
            try:
                ruler = AttributeValue.objects.get(attribute__name='Ruler', thing=location)
                ruler.value = update_value_in_string(ruler.value, name, new_name)
                ruler.save()
                logger.info('Updated ruler attribute of {0}: {1}'.format(location.name, ruler.value))
            except AttributeValue.DoesNotExist:
                pass
        except Thing.DoesNotExist:
            pass
        try:
            parent_with_name = Thing.objects.get(campaign=thing.campaign, name__icontains=name, children=thing)
            parent_new_name = update_value_in_string(parent_with_name.name, name, new_name)
            old_name = parent_with_name.name
            update_thing_name_and_all_related(parent_with_name, parent_new_name, False)
            logger.info('Updated name of {0}: {1}'.format(old_name, parent_with_name.name))
        except Thing.DoesNotExist:
            pass
    elif thing.thing_type.name == 'Location':
        try:
            ruler = AttributeValue.objects.get(attribute__name='Ruler', thing=thing)
            npc = Thing.objects.get(campaign=thing.campaign, thing_type__name='NPC', name=ruler.value)
            npc_occupation = AttributeValue.objects.get(attribute__name='Occupation', thing=npc)
            npc_occupation.value = update_value_in_string(npc_occupation.value, name, new_name)
            npc_occupation.save()
            logger.info('Updated occupation of {0}: {1}'.format(npc.name, npc_occupation.value))
        except AttributeValue.DoesNotExist:
            pass
        for child_with_name in thing.children.filter(name__icontains=name):
            child_new_name = update_value_in_string(child_with_name.name, name, new_name)
            old_name = child_with_name.name
            update_thing_name_and_all_related(child_with_name, child_new_name, False)
            logger.info('Updated name of {0}: {1}'.format(old_name, child_with_name.name))
    elif thing.thing_type.name == 'Faction':
        try:
            leader = AttributeValue.objects.get(attribute__name='Leader', thing=thing)
            npc = Thing.objects.get(campaign=thing.campaign, thing_type__name='NPC', name=leader.value)
            npc_occupation = AttributeValue.objects.get(attribute__name='Occupation', thing=npc)
            npc_occupation.value = update_value_in_string(npc_occupation.value, name, new_name)
            npc_occupation.save()
            logger.info('Updated occupation of {0}: {1}'.format(npc.name, npc_occupation.value))
        except AttributeValue.DoesNotExist:
            pass