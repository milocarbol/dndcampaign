from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, Http404, JsonResponse
from django.urls import reverse
from django.core import serializers
from .models import Thing, ThingType, Attribute, AttributeValue
from .forms import SearchForm


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

    thing_type_data = []
    for thing_type in ThingType.objects.all():
        thing_type_data.append({'name': thing_type.name})

    thing_data = []
    for thing in Thing.objects.all():
        thing_data.append({
            'name': thing.name,
            'description': thing.description,
            'thing_type': thing.thing_type.name,
            'children': [child.name for child in thing.children.all()]
        })

    attribute_data = []
    for attribute in Attribute.objects.all():
        attribute_data.append({
            'thing_type': attribute.thing_type.name,
            'name': attribute.name
        })

    attribute_value_data = []
    for attribute_value in AttributeValue.objects.all():
        attribute_value_data.append({
            'thing': attribute_value.thing.name,
            'attribute': attribute_value.attribute.name,
            'value': attribute_value.value
        })

    data = {
        'ThingTypes': thing_type_data,
        'Things': thing_data,
        'Attributes': attribute_data,
        'AttributeValues': attribute_value_data
    }

    return JsonResponse(data)
