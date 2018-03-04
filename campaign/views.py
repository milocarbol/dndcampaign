import json, re

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, Http404, JsonResponse
from django.urls import reverse
from operator import methodcaller

from .models import Thing, ThingType, Attribute, AttributeValue, UsefulLink
from .forms import AddLinkForm, SearchForm, UploadFileForm, NewLocationForm, NewFactionForm, NewNpcForm


def index(request):
    context = {
    }
    return render(request, 'campaign/index.html', context)


def search(request):
    form = SearchForm(request.POST)
    if form.is_valid():
        return go_to_closest_thing(form.cleaned_data['search_text'])


def go_to_closest_thing(name):
    results = Thing.objects.filter(name__icontains=name)
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
    if thing_type:
        types = [thing_type]
    else:
        types = [thing.name for thing in ThingType.objects.all()]

    list_data = []

    for t in types:
        data_for_type = []
        for thing in Thing.objects.filter(thing_type__name__iexact=t).order_by('name'):
            data_for_type.append({
                'name': thing.name,
                'description': thing.description,
                'attributes': get_attributes_to_display(thing)
            })
        list_data.append({
            'name': '{0}s'.format(t),
            'things': data_for_type
        })

    context = {
        'types': list_data,
        'filters': order_attribute_filters(get_attribute_filters(list_data)),
        'search_form': SearchForm()
    }

    print(context['filters'])

    return render(request, 'campaign/list.html', context)


def list_everything(request):
    return list_all(request, None)


def detail(request, name):
    try:
        thing = Thing.objects.get(name=name)
    except Thing.DoesNotExist:
        return go_to_closest_thing(name)

    parent_locations = []
    parent_factions = []
    for parent in Thing.objects.filter(children=thing).order_by('name'):
        if parent.thing_type.name == 'Location':
            parent_locations.append({
                'name': parent.name,
                'description': parent.description,
                'attributes': get_attributes_to_display(parent)
            })
        elif parent.thing_type.name == 'Faction':
            parent_factions.append({
                'name': parent.name,
                'description': parent.description,
                'attributes': get_attributes_to_display(parent)
            })

    child_locations = []
    child_factions = []
    child_npcs = []
    for child in thing.children.order_by('name'):
        if child.thing_type.name == 'Location':
            child_locations.append({
                'name': child.name,
                'description': child.description,
                'attributes': get_attributes_to_display(child)
            })
        elif child.thing_type.name == 'Faction':
            child_factions.append({
                'name': child.name,
                'description': child.description,
                'attributes': get_attributes_to_display(child)
            })
        elif child.thing_type.name == 'NPC':
            child_npcs.append({
                'name': child.name,
                'description': child.description,
                'attributes': get_attributes_to_display(child)
            })

    thing_info = {
        'name': thing.name,
        'description': thing.description,
        'attributes': get_attributes_to_display(thing),
        'useful_links': UsefulLink.objects.filter(thing=thing).order_by('name')
    }

    attribute_values = AttributeValue.objects.filter(thing=thing, attribute__display_in_summary=False).order_by('attribute__name')
    for attribute_value in attribute_values:
        thing_info[attribute_value.attribute.name.lower()] = attribute_value.value

    context = {
        'thing': thing_info,
        'parent_locations': parent_locations,
        'parent_factions': parent_factions,
        'child_locations': child_locations,
        'child_npcs': child_npcs,
        'child_factions': child_factions,
        'search_form': SearchForm()
    }
    return render(request, 'campaign/detail.html', context)


def get_attributes_to_display(thing):
    attributes_to_display = []
    attribute_values = AttributeValue.objects.filter(thing=thing, attribute__display_in_summary=True).order_by('attribute__name')
    for attribute_value in attribute_values:
        attributes_to_display.append({
            'name': attribute_value.attribute.name,
            'value': attribute_value.value,
            'can_link': attribute_value.attribute.is_thing,
            'js_class': get_js_class(attribute_value.attribute.name, attribute_value.value)
        })

    parent_location = get_parent_location(thing)
    if parent_location:
        attributes_to_display.append({
            'name': 'Location',
            'value': parent_location,
            'can_link': True,
            'js_class': get_js_class('Location', parent_location)
        })
    return attributes_to_display


def get_parent_location(thing):
    parents = Thing.objects.filter(children=thing, thing_type__name='Location').order_by('name')
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
    thing_data = []
    for thing in Thing.objects.all():
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
        thing_data.append({
            'name': thing.name,
            'description': thing.description,
            'thing_type': thing.thing_type.name,
            'children': [child.name for child in thing.children.all()],
            'attribute_values': attributes,
            'links': links
        })

    data = {
        'things': thing_data,
    }

    response = JsonResponse(data)
    response['Content-Disposition'] = 'attachment; filename="campaign.json"'

    return response


def import_campaign(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            save_campaign(request.FILES['file'].read().decode('UTF-8'))
            return HttpResponseRedirect('/campaign')
        else:
            print(request.POST)
    else:
        context = {
            'search_form': SearchForm(),
            'form': UploadFileForm()
        }
        return render(request, 'campaign/import.html', context)


def save_campaign(json_file):
    Thing.objects.all().delete()
    AttributeValue.objects.all().delete()
    data = json.loads(json_file)
    for thing in data['things']:
        thing_object = Thing(name=thing['name'], description=thing['description'], thing_type=ThingType.objects.get(name=thing['thing_type']))
        thing_object.save()

        for attribute in thing['attribute_values']:
            attr_value_object = AttributeValue(thing=thing_object, attribute=Attribute.objects.get(name=attribute['attribute'], thing_type=thing_object.thing_type), value=attribute['value'])
            attr_value_object.save()

        for link in thing['links']:
            link_object = UsefulLink(thing=thing_object, name=link['name'], value=link['value'])
            link_object.save()

    for thing in data['things']:
        thing_object = Thing.objects.get(name=thing['name'])
        for child in thing['children']:
            thing_object.children.add(Thing.objects.get(name=child))
        thing_object.save()


def move_thing_options(request, name):
    try:
        thing = Thing.objects.get(name=name)
    except Thing.DoesNotExist:
        raise Http404

    current_locations = Thing.objects.filter(children=thing, thing_type__name='Location')
    if len(current_locations) == 0:
        current_location = None
    else:
        current_location = current_locations[0].name

    options = [location.name for location in Thing.objects.filter(thing_type__name='Location').order_by('name')]

    context = {
        'thing': {
            'name': thing.name,
            'location': current_location
        },
        'options': options,
        'search_form': SearchForm()
    }

    return render(request, 'campaign/move_options.html', context)


def move_thing_confirm(request, name, new_location_name):
    try:
        thing = Thing.objects.get(name=name)
        if new_location_name == 'CLEAR':
            new_location = None
        else:
            new_location = Thing.objects.get(name=new_location_name)
    except Thing.DoesNotExist:
        raise Http404

    for old_location in Thing.objects.filter(children=thing, thing_type__name='Location'):
        old_location.children.remove(thing)
        old_location.save()

    if new_location:
        new_location.children.add(thing)
        new_location.save()

    return HttpResponseRedirect(reverse('campaign:detail', args=(name,)))


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
    if request.method == 'POST':
        form = NewLocationForm(request.POST)
        if form.is_valid():
            thing = Thing(name=form.cleaned_data['name'], description=form.cleaned_data['description'], thing_type=ThingType.objects.get(name='Location'))
            thing.save()

            children = []
            children.extend(form.cleaned_data['factions'])
            children.extend(form.cleaned_data['npcs'])

            for child in children:
                current_parent_locations = Thing.objects.filter(children=child, thing_type__name='Location')
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

    context = {
        'search_form': SearchForm(),
        'thing_form': form,
        'thing_type': 'Location'
    }
    return render(request, 'campaign/new_thing.html', context)


def create_new_faction(request):
    if request.method == 'POST':
        form = NewFactionForm(request.POST)
        if form.is_valid():
            thing = Thing(name=form.cleaned_data['name'], description=form.cleaned_data['description'], thing_type=ThingType.objects.get(name='Faction'))
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

    context = {
        'search_form': SearchForm(),
        'thing_form': form,
        'thing_type': 'Faction'
    }
    return render(request, 'campaign/new_thing.html', context)


def create_new_npc(request):
    if request.method == 'POST':
        form = NewNpcForm(request.POST)
        if form.is_valid():
            thing = Thing(name=form.cleaned_data['name'], description=form.cleaned_data['description'], thing_type=ThingType.objects.get(name='NPC'))
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

    context = {
        'search_form': SearchForm(),
        'thing_form': form,
        'thing_type': 'NPC'
    }
    return render(request, 'campaign/new_thing.html', context)


def add_link(request, name):
    try:
        thing = Thing.objects.get(name=name)
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
        'search_form': SearchForm(),
        'form': form
    }
    return render(request, 'campaign/add_link.html', context)
