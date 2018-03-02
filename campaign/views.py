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


def list_all(request, type):
    things = Thing.objects.filter(thing_type__name__iexact=type).order_by('name')
    list_data = []

    for thing in things:
        list_data.append({
            'name': thing.name,
            'description': thing.description
        })

    context = {
        'things': list_data,
        'heading': '{0}s'.format(type),
        'form': SearchForm()
    }

    return render(request, 'campaign/list.html', context)


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
                'description': parent.description
            })
        elif parent.thing_type.name == 'Faction':
            parent_factions.append({
                'name': parent.name,
                'description': parent.description
            })

    child_locations = []
    child_factions = []
    child_npcs = []
    for child in thing.children.order_by('name'):
        if child.thing_type.name == 'Location':
            child_locations.append({
                'name': child.name,
                'description': child.description
            })
        elif child.thing_type.name == 'Faction':
            child_factions.append({
                'name': child.name,
                'description': child.description
            })
        elif child.thing_type.name == 'NPC':
            child_npcs.append({
                'name': child.name,
                'description': child.description
            })

    thing_info = {
        'name': thing.name,
        'description': thing.description
    }

    attribute_values = AttributeValue.objects.filter(thing=thing)
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
