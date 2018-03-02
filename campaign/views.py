import json

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, Http404, JsonResponse
from django.urls import reverse
from .models import Thing, ThingType, Attribute, AttributeValue
from .forms import SearchForm, UploadFileForm


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
        'form': SearchForm()
    }

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
        'attributes': get_attributes_to_display(thing)
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
        'form': SearchForm()
    }
    return render(request, 'campaign/detail.html', context)


def get_attributes_to_display(thing):
    attributes_to_display = []
    attribute_values = AttributeValue.objects.filter(thing=thing, attribute__display_in_summary=True).order_by('attribute__name')
    for attribute_value in attribute_values:
        attributes_to_display.append({
            'name': attribute_value.attribute.name,
            'value': attribute_value.value
        })

    parent_location = get_parent_location(thing)
    if parent_location:
        attributes_to_display.append({
            'name': 'Location',
            'value': parent_location
        })
    return attributes_to_display


def get_parent_location(thing):
    parents = Thing.objects.filter(children=thing, thing_type__name='Location').order_by('name')
    if len(parents) == 0:
        return None
    else:
        return parents[0].name


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
        thing_data.append({
            'name': thing.name,
            'description': thing.description,
            'thing_type': thing.thing_type.name,
            'children': [child.name for child in thing.children.all()],
            'attribute_values': attributes
        })

    data = {
        'things': thing_data,
    }

    return JsonResponse(data)


def import_campaign(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            save_campaign(request.FILES['file'].read().decode('UTF-8'))
            return HttpResponseRedirect('/')

    return HttpResponseRedirect('/')


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
        'form': SearchForm()
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
