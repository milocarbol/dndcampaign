from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.urls import reverse
from .models import Thing
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
