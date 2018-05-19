import json, re

from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, HttpResponseRedirect, Http404, JsonResponse
from django.urls import reverse
from operator import methodcaller

from .models import Thing, ThingType, Attribute, AttributeValue, UsefulLink, Campaign, RandomEncounter, RandomEncounterType
from .forms import AddLinkForm, SearchForm, UploadFileForm, NewLocationForm, NewFactionForm, NewNpcForm, EditEncountersForm, EditDescriptionForm, ChangeTextAttributeForm, ChangeOptionAttributeForm, ChangeLocationForm


def index(request):
    context = {
    }
    return render(request, 'campaign/index.html', context)


def search(request):
    campaign = Campaign.objects.get(is_active=True)
    form = SearchForm(request.POST)
    if form.is_valid():
        return go_to_closest_thing(campaign=campaign, name=form.cleaned_data['search_text'])


def go_to_closest_thing(campaign, name):
    results = Thing.objects.filter(campaign=campaign, name__icontains=name)
    if len(results) == 0:
        raise Http404('"{0}" does not exist.'.format(name))
    elif len(results) == 1:
        return HttpResponseRedirect(reverse('campaign:detail', args=(results[0].name,)))
    else:
        min_length_diff = len(results[0].name) - len(name)
        result = results[0]
        for r in results[1:]:
            new_length_diff = len(r.name) - len(name)
            if new_length_diff < min_length_diff:
                result = r
                min_length_diff = new_length_diff
        return HttpResponseRedirect(reverse('campaign:detail', args=(result.name,)))


def list_all(request, thing_type):
    campaign = Campaign.objects.get(is_active=True)

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

    context = {
        'types': list_data,
        'thing_link_marker': '@',
        'thing_url': '/campaign/thing/',
        'beyond_link_marker': '$',
        'beyond_url': 'https://www.dndbeyond.com/monsters/',
        'campaign': campaign.name,
        'campaigns': [c.name for c in Campaign.objects.all().order_by('name')],
        'filters': order_attribute_filters(get_attribute_filters(list_data)),
        'search_form': SearchForm()
    }

    return render(request, 'campaign/list.html', context)


def list_everything(request):
    return list_all(request, None)


def detail(request, name):
    campaign = Campaign.objects.get(is_active=True)
    try:
        thing = Thing.objects.get(campaign=campaign, name=name)
    except Thing.DoesNotExist:
        return go_to_closest_thing(campaign=campaign, name=name)

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

    editable_attributes = [a.name for a in Attribute.objects.filter(thing_type=thing.thing_type).order_by('name')]

    thing_info = {
        'name': thing.name,
        'description': thing.description,
        'attributes': get_attributes_to_display(campaign=campaign, thing=thing),
        'useful_links': UsefulLink.objects.filter(thing=thing).order_by('name'),
        'encounters': encounters,
        'display_encounters': display_encounters,
        'enable_random_encounters': thing.thing_type.name == 'Location',
        'editable_attributes': editable_attributes
    }

    attribute_values = AttributeValue.objects.filter(thing=thing, attribute__display_in_summary=False).order_by('attribute__name')
    for attribute_value in attribute_values:
        thing_info[attribute_value.attribute.name.lower()] = attribute_value.value

    context = {
        'thing': thing_info,
        'thing_link_marker': '@',
        'thing_url': '/campaign/thing/',
        'beyond_link_marker': '$',
        'beyond_url': 'https://www.dndbeyond.com/monsters/',
        'campaign': campaign.name,
        'campaigns': [c.name for c in Campaign.objects.all().order_by('name')],
        'parent_locations': parent_locations,
        'parent_factions': parent_factions,
        'child_locations': child_locations,
        'child_npcs': child_npcs,
        'child_factions': child_factions,
        'search_form': SearchForm()
    }
    return render(request, 'campaign/detail.html', context)


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


def get_js_class(name, value):
    return re.sub(r'\W+', '-', '{0}-{1}'.format(name, value))


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


def export(request):
    campaign = Campaign.objects.get(is_active=True)
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
            'thing_type': thing.thing_type.name,
            'children': [child.name for child in thing.children.all()],
            'attribute_values': attributes,
            'links': links,
            'random_encounters': random_encounters
        })

    data = {
        'things': thing_data,
    }

    response = JsonResponse(data)
    response['Content-Disposition'] = 'attachment; filename="{0}.json"'.format(campaign.name.lower().replace(' ', '_'))

    return response


def import_campaign(request):
    campaign = Campaign.objects.get(is_active=True)
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            save_campaign(campaign=campaign, json_file=request.FILES['file'].read().decode('UTF-8'))
            return HttpResponseRedirect('/campaign')
        else:
            print(request.POST)
    else:

        context = {
            'campaign': campaign.name,
            'campaigns': [c.name for c in Campaign.objects.all().order_by('name')],
            'search_form': SearchForm(),
            'form': UploadFileForm()
        }
        return render(request, 'campaign/import.html', context)


def save_campaign(campaign, json_file):
    Thing.objects.filter(campaign=campaign).delete()
    AttributeValue.objects.all().delete()
    data = json.loads(json_file)
    for thing in data['things']:
        thing_object = Thing(campaign=campaign, name=thing['name'], description=thing['description'], thing_type=ThingType.objects.get(name=thing['thing_type']))
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

    for thing in data['things']:
        thing_object = Thing.objects.get(campaign=campaign, name=thing['name'])
        for child in thing['children']:
            thing_object.children.add(Thing.objects.get(campaign=campaign, name=child))
        thing_object.save()


def move_thing(request, name):
    campaign = Campaign.objects.get(is_active=True)
    thing = get_object_or_404(Thing, campaign=campaign, name=name)

    if request.method == 'POST':
        form = ChangeLocationForm(request.POST)
        if form.is_valid():
            for old_location in Thing.objects.filter(campaign=campaign, children=thing, thing_type__name='Location'):
                old_location.children.remove(thing)
                old_location.save()
            if not form.cleaned_data['clear_location'] and form.cleaned_data['location']:
                new_location = get_object_or_404(Thing, campaign=campaign, thing_type__name='Location', name=form.cleaned_data['location'])
                new_location.children.add(thing)
                new_location.save()
            return HttpResponseRedirect(reverse('campaign:detail', args=(thing.name,)))
    else:
        current_locations = Thing.objects.filter(campaign=campaign, children=thing, thing_type__name='Location')
        if len(current_locations) == 0:
            current_location = None
        else:
            current_location = current_locations[0].pk
        print(current_location)
        form = ChangeLocationForm({'location': current_location})
        form.refresh_fields()

    context = {
        'thing': thing,
        'url': reverse('campaign:move_thing', args=(thing.name,)),
        'header': 'Change location for {0} '.format(thing.name),
        'form': form,
        'search_form': SearchForm()
    }
    return render(request, 'campaign/edit_page.html', context)


def new_thing(request, thing_type):
    if thing_type == 'Location':
        return create_new_location(request)
    elif thing_type == 'Faction':
        return create_new_faction(request)
    elif thing_type == 'NPC':
        return create_new_npc(request)
    else:
        raise Http404


def create_new_location(request):
    campaign = Campaign.objects.get(is_active=True)
    if request.method == 'POST':
        form = NewLocationForm(request.POST)
        if form.is_valid():
            thing = Thing(campaign=campaign, name=form.cleaned_data['name'], description=form.cleaned_data['description'], thing_type=ThingType.objects.get(name='Location'))
            thing.save()

            children = []
            children.extend(form.cleaned_data['factions'])
            children.extend(form.cleaned_data['npcs'])

            for child in children:
                current_parent_locations = Thing.objects.filter(campaign=campaign, children=child, thing_type__name='Location')
                for parent in current_parent_locations:
                    parent.children.remove(child)
                    parent.save()
                thing.children.add(child)
            thing.save()

            new_parent = form.cleaned_data['location']

            if new_parent:
                new_parent.children.add(thing)
                new_parent.save()

            return HttpResponseRedirect(reverse('campaign:detail', args=(thing.name,)))
    else:
        form = NewLocationForm()

    form.refresh_fields()

    context = {
        'search_form': SearchForm(),
        'campaign': campaign.name,
        'campaigns': [c.name for c in Campaign.objects.all().order_by('name')],
        'thing_form': form,
        'thing_type': 'Location'
    }
    return render(request, 'campaign/new_thing.html', context)


def create_new_faction(request):
    campaign = Campaign.objects.get(is_active=True)
    if request.method == 'POST':
        form = NewFactionForm(request.POST)
        if form.is_valid():
            thing = Thing(campaign=campaign, name=form.cleaned_data['name'], description=form.cleaned_data['description'], thing_type=ThingType.objects.get(name='Faction'))
            thing.save()

            for child in form.cleaned_data['npcs']:
                thing.children.add(child)
            thing.save()

            new_parent = form.cleaned_data['location']
            if new_parent:
                new_parent.children.add(thing)
                new_parent.save()

            if form.cleaned_data['leader']:
                leader = AttributeValue(thing=thing, attribute=Attribute.objects.get(name='Leader'), value=form.cleaned_data['leader'].name)
                leader.save()

            if form.cleaned_data['attitude']:
                attitude = AttributeValue(thing=thing, attribute=Attribute.objects.get(name='Attitude', thing_type__name='Faction'), value=form.cleaned_data['attitude'])
                attitude.save()

            if form.cleaned_data['power']:
                power = AttributeValue(thing=thing, attribute=Attribute.objects.get(name='Power'), value=form.cleaned_data['power'])
                power.save()

            if form.cleaned_data['reach']:
                reach = AttributeValue(thing=thing, attribute=Attribute.objects.get(name='Reach'), value=form.cleaned_data['reach'])
                reach.save()

            return HttpResponseRedirect(reverse('campaign:detail', args=(thing.name,)))
    else:
        form = NewFactionForm()

    form.refresh_fields()

    context = {
        'search_form': SearchForm(),
        'campaign': campaign.name,
        'campaigns': [c.name for c in Campaign.objects.all().order_by('name')],
        'thing_form': form,
        'thing_type': 'Faction'
    }
    return render(request, 'campaign/new_thing.html', context)


def create_new_npc(request):
    campaign = Campaign.objects.get(is_active=True)
    if request.method == 'POST':
        form = NewNpcForm(request.POST)
        if form.is_valid():
            thing = Thing(campaign=campaign, name=form.cleaned_data['name'], description=form.cleaned_data['description'], thing_type=ThingType.objects.get(name='NPC'))
            thing.save()

            new_parents = []
            if form.cleaned_data['location']:
                new_parents.append(form.cleaned_data['location'])
            new_parents.extend(form.cleaned_data['factions'])
            for new_parent in new_parents:
                new_parent.children.add(thing)
                new_parent.save()

            if form.cleaned_data['race']:
                race = AttributeValue(thing=thing, attribute=Attribute.objects.get(name='Race'), value=form.cleaned_data['race'])
                race.save()

            if form.cleaned_data['attitude']:
                attitude = AttributeValue(thing=thing, attribute=Attribute.objects.get(name='Attitude', thing_type__name='NPC'), value=form.cleaned_data['attitude'])
                attitude.save()

            if form.cleaned_data['occupation']:
                occupation = AttributeValue(thing=thing, attribute=Attribute.objects.get(name='Occupation'), value=form.cleaned_data['occupation'])
                occupation.save()

            if form.cleaned_data['link']:
                link = AttributeValue(thing=thing, attribute=Attribute.objects.get(name='Link'), value=form.cleaned_data['link'])
                link.save()

            return HttpResponseRedirect(reverse('campaign:detail', args=(thing.name,)))
    else:
        form = NewNpcForm()

    form.refresh_fields()

    context = {
        'search_form': SearchForm(),
        'campaign': campaign.name,
        'campaigns': [c.name for c in Campaign.objects.all().order_by('name')],
        'thing_form': form,
        'thing_type': 'NPC'
    }
    return render(request, 'campaign/new_thing.html', context)


def add_link(request, name):
    campaign = Campaign.objects.get(is_active=True)
    try:
        thing = Thing.objects.get(campaign=campaign, name=name)
    except Thing.DoesNotExist:
        raise Http404

    if request.method == 'POST':
        form = AddLinkForm(request.POST)
        if form.is_valid():
            link = UsefulLink(thing=thing, name=form.cleaned_data['name'], value=form.cleaned_data['value'])
            link.save()
            return HttpResponseRedirect(reverse('campaign:detail', args=(thing.name,)))
    else:
        form = AddLinkForm()

    context = {
        'thing': {
            'name': thing.name
        },
        'campaign': campaign.name,
        'campaigns': [c.name for c in Campaign.objects.all().order_by('name')],
        'search_form': SearchForm(),
        'form': form
    }
    return render(request, 'campaign/add_link.html', context)


def remove_link(request, name, link_name):
    campaign = Campaign.objects.get(is_active=True)
    thing = get_object_or_404(Thing, campaign=campaign, name=name)

    useful_link = get_object_or_404(UsefulLink, thing=thing, name=link_name)
    useful_link.delete()

    return HttpResponseRedirect(reverse('campaign:detail', args=(thing.name,)))


def edit_random_encounters(request, name, type_name):
    campaign = Campaign.objects.get(is_active=True)
    try:
        thing = Thing.objects.get(campaign=campaign, name=name)
    except Thing.DoesNotExist:
        raise Http404

    random_encounter_type = RandomEncounterType.objects.get(name=type_name)
    random_encounters = RandomEncounter.objects.filter(thing=thing, random_encounter_type=random_encounter_type)

    if request.method == 'POST':
        form = EditEncountersForm(request.POST)
        if form.is_valid():
            random_encounters.delete()
            for name in form.cleaned_data['encounters'].split('\n'):
                if name:
                    random_encounter = RandomEncounter(thing=thing, name=name, random_encounter_type=random_encounter_type)
                    random_encounter.save()
            return HttpResponseRedirect(reverse('campaign:detail', args=(thing.name,)))
    else:
        form = EditEncountersForm({'name': name, 'encounters': '\n'.join([e.name for e in random_encounters])})

    context = {
        'thing': thing,
        'encounter_type': type_name,
        'form': form,
        'search_form': SearchForm()
    }
    return render(request, 'campaign/edit_encounters.html', context)


def edit_description(request, name):
    campaign = Campaign.objects.get(is_active=True)
    try:
        thing = Thing.objects.get(campaign=campaign, name=name)
    except Thing.DoesNotExist:
        raise Http404

    if request.method == 'POST':
        form = EditDescriptionForm(request.POST)
        if form.is_valid():
            thing.description = form.cleaned_data['description']
            thing.save()
            return HttpResponseRedirect(reverse('campaign:detail', args=(thing.name,)))
    else:
        form = EditDescriptionForm({'name': thing.name, 'description': thing.description})

    context = {
        'thing': thing,
        'form': form,
        'search_form': SearchForm()
    }
    return render(request, 'campaign/edit_description.html', context)


def set_attribute(request, name, attribute_name):
    campaign = Campaign.objects.get(is_active=True)
    thing = get_object_or_404(Thing, campaign=campaign, name=name)
    attribute = get_object_or_404(Attribute, thing_type=thing.thing_type, name=attribute_name)
    if request.method == 'POST':
        if attribute.name == 'Attitude' or attribute.name == 'Leader' or attribute.name == 'Power' or attribute.name == 'Reach':
            form = ChangeOptionAttributeForm(request.POST)
            form.refresh_fields(attribute.thing_type, attribute.name)
            if form.is_valid():
                attribute_value = AttributeValue.objects.filter(attribute=attribute, thing=thing)
                if attribute_value:
                    attribute_value = attribute_value[0]
                else:
                    attribute_value = AttributeValue(attribute=attribute, thing=thing)
                attribute_value.value = form.cleaned_data['value']
                attribute_value.save()
                return HttpResponseRedirect(reverse('campaign:detail', args=(thing.name,)))
        else:
            form = ChangeTextAttributeForm(request.POST)
            if form.is_valid():
                attribute_value = AttributeValue.objects.filter(attribute=attribute, thing=thing)
                if attribute_value:
                    attribute_value = attribute_value[0]
                else:
                    attribute_value = AttributeValue(attribute=attribute, thing=thing)
                attribute_value.value = form.cleaned_data['value']
                attribute_value.save()
                return HttpResponseRedirect(reverse('campaign:detail', args=(thing.name,)))
    else:
        attribute_value = AttributeValue.objects.filter(attribute=attribute, thing=thing)
        if attribute_value:
            attribute_value = attribute_value[0]
        else:
            attribute_value = AttributeValue(attribute=attribute, thing=thing, value='')
        if attribute.name == 'Attitude' or attribute.name == 'Leader' or attribute.name == 'Power' or attribute.name == 'Reach':
            form = ChangeOptionAttributeForm({'name': attribute.name, 'value': attribute_value.value})
            form.refresh_fields(attribute.thing_type, attribute.name)
        else:
            form = ChangeTextAttributeForm({'name': attribute.name, 'value': attribute_value.value})

    context = {
        'thing': thing,
        'attribute': attribute,
        'form': form,
        'search_form': SearchForm()
    }
    return render(request, 'campaign/set_attribute.html', context)


def change_campaign(request, name):
    new_campaign = get_object_or_404(Campaign, name=name)
    old_campaign = Campaign.objects.get(is_active=True)

    old_campaign.is_active = False
    old_campaign.save()
    new_campaign.is_active = True
    new_campaign.save()

    return HttpResponseRedirect(reverse('campaign:list_everything'))
