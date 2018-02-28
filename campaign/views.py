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
        return HttpResponseRedirect(reverse('campaign:detail', args=(form.cleaned_data['search_text'],)))
    else:
        return HttpResponseRedirect('/')


def detail(request, name):
    try:
        thing = Thing.objects.get(name__iexact=name)
        parents = [parent.name for parent in Thing.objects.filter(children=thing)]
        children = [child.name for child in thing.children.all()]

        context = {
            'name': thing.name,
            'desc': thing.description,
            'parents': sorted(parents),
            'children': sorted(children),
            'form': SearchForm()
        }
        return render(request, 'campaign/detail.html', context)
    except Thing.DoesNotExist:
        raise Http404('"{0}" does not exist.'.format(name))


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
