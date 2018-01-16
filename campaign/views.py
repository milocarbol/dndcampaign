from django.shortcuts import render
from django.http import HttpResponse, Http404
from .models import Thing


def index(request):
    context = {
    }
    return render(request, 'campaign/index.html', context)


def detail(request, name):
    try:
        thing = Thing.objects.get(name=name)
        parents = [parent.name for parent in Thing.objects.filter(children=thing)]
        children = [child.name for child in thing.children.all()]

        context = {
            'name': thing.name,
            'desc': thing.description,
            'parents': sorted(parents),
            'children': sorted(children)
        }
        return render(request, 'campaign/detail.html', context)
    except Thing.DoesNotExist:
        raise Http404('That thing does not exist.')
