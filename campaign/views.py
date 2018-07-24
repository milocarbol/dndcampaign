import logging

from django.http import HttpResponseRedirect, Http404, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from .export_utils import get_campaign_json, get_settings_json, save_campaign, save_settings
from .forms import AddLinkForm, ChangeRequiredTextAttributeForm, SearchForm, UploadFileForm, NewLocationForm, NewFactionForm, NewNpcForm, NewItemForm, EditEncountersForm, EditDescriptionForm, ChangeTextAttributeForm, ChangeOptionAttributeForm, ChangeParentForm, EditOptionalTextFieldForm, SelectCategoryForAttributeForm, SelectGeneratorObject, SelectPreset, NewPreset, GeneratorObjectForm, SelectGeneratorObjectWithLocation
from .models import Thing, ThingType, Attribute, AttributeValue, UsefulLink, Campaign, RandomEncounter, RandomEncounterType, RandomizerAttribute, RandomizerAttributeCategory, RandomizerAttributeCategoryOption, RandomizerAttributeOption, RandomAttribute, GeneratorObject, GeneratorObjectContains, GeneratorObjectFieldToRandomizerAttribute, Weight, WeightPreset
from .randomizers import get_randomization_options_for_new_thing, get_random_attribute_in_category_raw, get_random_attribute_raw, generate_random_attributes_for_thing_raw
from .generator_utils import generate_thing, save_new_generator, edit_generator
from .thing_utils import get_details, get_list_data, get_filters, save_new_faction, save_new_location, save_new_npc, save_new_item, randomize_name_for_thing, update_thing_name_and_all_related


logger = logging.getLogger(__name__)

def build_context(context):
    campaign = Campaign.objects.get(is_active=True)
    attribute_settings = []
    bookmarks = []
    for thing_type in ThingType.objects.all().order_by('name'):
        attribute_settings.append({
            'name': thing_type.name,
            'attributes': [a.name for a in RandomizerAttribute.objects.filter(thing_type=thing_type)]
        })
        bookmarks.append({
            'name': thing_type.name,
            'things': [t.name for t in Thing.objects.filter(campaign=campaign, thing_type=thing_type, is_bookmarked=True).order_by('name')]
        })
    attribute_presets = []
    for preset in WeightPreset.objects.filter(campaign=campaign):
        attribute_presets.append(preset.attribute_name)
    attribute_presets = sorted(list(set(attribute_presets)))
    full_context = {
        'search_form': SearchForm(),
        'campaign': campaign.name,
        'campaigns': [c.name for c in Campaign.objects.all().order_by('name')],
        'attribute_settings': attribute_settings,
        'attribute_presets': attribute_presets,
        'bookmarks': bookmarks,
        'thing_types': [tt.name for tt in ThingType.objects.all().order_by('name')]
    }
    full_context.update(context)
    return full_context


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


def list_all(request, thing_type, bookmarks_only=False):
    campaign = Campaign.objects.get(is_active=True)

    list_data = get_list_data(campaign=campaign, thing_type=thing_type, bookmarks_only=bookmarks_only)

    context = {
        'types': list_data,
        'thing_link_marker': '@',
        'thing_url': '/campaign/thing/',
        'beyond_link_marker': '$',
        'beyond_url': 'https://www.dndbeyond.com/monsters/',
        'item_link_marker': '!',
        'item_url': 'https://www.dndbeyond.com/magic-items/',
        'filters': get_filters(list_data)
    }

    return render(request, 'campaign/list.html', build_context(context))


def list_everything(request):
    return list_all(request=request, thing_type=None)


def list_bookmarks(request):
    return list_all(request=request, thing_type=None, bookmarks_only=True)


def detail(request, name):
    campaign = Campaign.objects.get(is_active=True)
    try:
        thing = Thing.objects.get(campaign=campaign, name=name)
    except Thing.DoesNotExist:
        return go_to_closest_thing(campaign=campaign, name=name)

    context = {
        'thing': get_details(campaign=campaign, thing=thing, get_child_detail_too=True),
        'thing_link_marker': '@',
        'thing_url': '/campaign/thing/',
        'beyond_link_marker': '$',
        'beyond_url': 'https://www.dndbeyond.com/monsters/',
        'item_link_marker': '!',
        'item_url': 'https://www.dndbeyond.com/magic-items/'
    }
    return render(request, 'campaign/detail.html', build_context(context))


def export(request):
    campaign = Campaign.objects.get(is_active=True)

    response = JsonResponse(get_campaign_json(campaign=campaign))
    response['Content-Disposition'] = 'attachment; filename="{0}.json"'.format(campaign.name.lower().replace(' ', '_'))

    return response


def import_campaign(request):
    campaign = Campaign.objects.get(is_active=True)
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            save_campaign(campaign=campaign, json_file=request.FILES['file'].read().decode('UTF-8'))
            return HttpResponseRedirect(reverse('campaign:list_bookmarks'))
        else:
            logger.info(form.errors)
    else:
        form = UploadFileForm()
    context = {
        'header': 'Upload campaign data for {0}'.format(campaign.name),
        'url': reverse('campaign:import'),
        'form': form
    }
    return render(request, 'campaign/edit_page.html', build_context(context))


def export_settings(request):
    response = JsonResponse(get_settings_json())
    response['Content-Disposition'] = 'attachment; filename="settings.json"'

    return response


def import_settings(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            save_settings(json_file=request.FILES['file'].read().decode('UTF-8'))
            return HttpResponseRedirect(reverse('campaign:list_bookmarks'))
        else:
            logger.info(form.errors)
    else:
        form = UploadFileForm()
    context = {
        'header': 'Import settings',
        'url': reverse('campaign:import_settings'),
        'form': form
    }
    return render(request, 'campaign/edit_page.html', build_context(context))


def change_parent(request, thing_type_name, name):
    campaign = Campaign.objects.get(is_active=True)
    thing_type = get_object_or_404(ThingType, name=thing_type_name)
    thing = get_object_or_404(Thing, campaign=campaign, name=name)

    if request.method == 'POST':
        form = ChangeParentForm(request.POST)
        if form.is_valid():
            for old_parent in Thing.objects.filter(campaign=campaign, children=thing, thing_type=thing_type):
                old_parent.children.remove(thing)
                old_parent.save()
            if not form.cleaned_data['clear_parent'] and form.cleaned_data['parent']:
                new_parent = get_object_or_404(Thing, campaign=campaign, thing_type=thing_type, name=form.cleaned_data['parent'])
                new_parent.children.add(thing)
                new_parent.save()
            return HttpResponseRedirect(reverse('campaign:detail', args=(thing.name,)))
    else:
        try:
            current_parent = Thing.objects.get(campaign=campaign, children=thing, thing_type=thing_type).pk
        except Thing.DoesNotExist:
            current_parent = None
        form = ChangeParentForm({'parent': current_parent})
        form.refresh_fields(thing_type=thing_type)

    context = {
        'thing': thing,
        'url': reverse('campaign:change_parent', args=(thing_type.name, thing.name)),
        'header': 'Change {0} for {1} '.format(thing_type.name, thing.name),
        'form': form
    }
    return render(request, 'campaign/edit_page.html', build_context(context))


def delete_thing(request, name):
    campaign = Campaign.objects.get(is_active=True)
    thing = get_object_or_404(Thing, campaign=campaign, name=name)
    delete_thing_and_children(thing)
    return HttpResponseRedirect(reverse('campaign:list_bookmarks'))


def delete_thing_and_children(thing):
    for child in thing.children.all():
        child.delete()
    thing.delete()


def new_thing(request, thing_type):
    if thing_type == 'Location':
        return create_new_location(request)
    elif thing_type == 'Faction':
        return create_new_faction(request)
    elif thing_type == 'NPC':
        return create_new_npc(request)
    elif thing_type == 'Item':
        return create_new_item(request)
    else:
        raise Http404


def create_new_location(request):
    campaign = Campaign.objects.get(is_active=True)
    if request.method == 'POST':
        form = NewLocationForm(request.POST)
        if form.is_valid():
            thing = save_new_location(campaign=campaign, form_data=form.cleaned_data)

            return HttpResponseRedirect(reverse('campaign:detail', args=(thing.name,)))
    else:
        form = NewLocationForm()

    form.refresh_fields()

    context = {
        'thing_form': form,
        'thing_type': 'Location'
    }
    context.update(get_randomization_options_for_new_thing(thing_type=ThingType.objects.get(name='Location')))
    return render(request, 'campaign/new_thing.html', build_context(context))


def create_new_faction(request):
    campaign = Campaign.objects.get(is_active=True)
    if request.method == 'POST':
        form = NewFactionForm(request.POST)
        if form.is_valid():
            thing = save_new_faction(campaign=campaign, form_data=form.cleaned_data)

            return HttpResponseRedirect(reverse('campaign:detail', args=(thing.name,)))
    else:
        form = NewFactionForm()

    form.refresh_fields()

    context = {
        'thing_form': form,
        'thing_type': 'Faction'
    }
    context.update(get_randomization_options_for_new_thing(thing_type=ThingType.objects.get(name='Faction')))
    return render(request, 'campaign/new_thing.html', build_context(context))


def create_new_npc(request):
    campaign = Campaign.objects.get(is_active=True)
    if request.method == 'POST':
        form = NewNpcForm(request.POST)
        if form.is_valid():
            thing = save_new_npc(campaign=campaign, form_data=form.cleaned_data)

            return HttpResponseRedirect(reverse('campaign:detail', args=(thing.name,)))
    else:
        form = NewNpcForm()

    form.refresh_fields()

    context = {
        'thing_form': form,
        'thing_type': 'NPC'
    }
    context.update(get_randomization_options_for_new_thing(thing_type=ThingType.objects.get(name='NPC')))
    return render(request, 'campaign/new_thing.html', build_context(context))


def create_new_item(request):
    campaign = Campaign.objects.get(is_active=True)
    if request.method == 'POST':
        form = NewItemForm(request.POST)
        if form.is_valid():
            thing = save_new_item(campaign=campaign, form_data=form.cleaned_data)

            return HttpResponseRedirect(reverse('campaign:detail', args=(thing.name,)))
    else:
        form = NewItemForm()

    context = {
        'thing_form': form,
        'thing_type': 'Item'
    }
    return render(request, 'campaign/new_thing.html', build_context(context))


def add_link(request, name):
    campaign = Campaign.objects.get(is_active=True)
    thing = get_object_or_404(Thing, campaign=campaign, name=name)

    if request.method == 'POST':
        form = AddLinkForm(request.POST)
        if form.is_valid():
            link = UsefulLink(thing=thing, name=form.cleaned_data['name'], value=form.cleaned_data['value'])
            link.save()
            return HttpResponseRedirect(reverse('campaign:detail', args=(thing.name,)))
    else:
        form = AddLinkForm()

    context = {
        'header': 'Add link to {0}'.format(thing.name),
        'url': reverse('campaign:add_link', args=(thing.name,)),
        'form': form
    }
    return render(request, 'campaign/edit_page.html', build_context(context))


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
        'header': 'Edit {0} encounters for {1}'.format(type_name, thing.name),
        'url': reverse('campaign:edit_encounters', args=(thing.name, type_name)),
        'form': form
    }
    return render(request, 'campaign/edit_page.html', build_context(context))


def randomize_name(request, thing_type_name, name):
    campaign = Campaign.objects.get(is_active=True)
    thing = get_object_or_404(Thing, thing_type__name=thing_type_name, campaign=campaign, name__iexact=name)

    randomize_name_for_thing(thing=thing)

    return HttpResponseRedirect(reverse('campaign:detail', args=(thing.name,)))


def edit_name(request, name):
    campaign = Campaign.objects.get(is_active=True)
    thing = get_object_or_404(Thing, campaign=campaign, name=name)

    if request.method == 'POST':
        form = ChangeRequiredTextAttributeForm(request.POST)
        if form.is_valid():
            new_name = form.cleaned_data['value']
            update_thing_name_and_all_related(thing, new_name)
            return HttpResponseRedirect(reverse('campaign:detail', args=(thing.name,)))
    else:
        form = ChangeRequiredTextAttributeForm({'value': thing.name})

    context = {
        'form': form,
        'header': 'Edit name for {0}'.format(thing.name),
        'url': reverse('campaign:edit_name', args=(thing.name,))
    }
    return render(request, 'campaign/edit_page.html', build_context(context))


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
        'form': form,
        'header': 'Edit description for {0}'.format(thing.name),
        'url': reverse('campaign:edit_description', args=(thing.name,))
    }
    return render(request, 'campaign/edit_page.html', build_context(context))


def set_attribute(request, name, attribute_name):
    campaign = Campaign.objects.get(is_active=True)
    thing = get_object_or_404(Thing, campaign=campaign, name=name)
    attribute = get_object_or_404(Attribute, thing_type=thing.thing_type, name=attribute_name)
    if request.method == 'POST':
        if attribute.name == 'Attitude' or attribute.name == 'Leader' or attribute.name == 'Power' \
                or attribute.name == 'Reach' or attribute.name == 'Ruler':
            form = ChangeOptionAttributeForm(request.POST)
            form.refresh_fields(attribute.thing_type, attribute.name)
            if form.is_valid():
                try:
                    attribute_value = AttributeValue.objects.get(attribute=attribute, thing=thing)
                except AttributeValue.DoesNotExist:
                    attribute_value = AttributeValue(attribute=attribute, thing=thing)
                attribute_value.value = form.cleaned_data['value']
                attribute_value.save()
                return HttpResponseRedirect(reverse('campaign:detail', args=(thing.name,)))
        else:
            form = ChangeTextAttributeForm(request.POST)
            if form.is_valid():
                try:
                    attribute_value = AttributeValue.objects.get(attribute=attribute, thing=thing)
                    if form.cleaned_data['value']:
                        attribute_value.value = form.cleaned_data['value']
                        attribute_value.save()
                    else:
                        attribute_value.delete()
                except AttributeValue.DoesNotExist:
                    if form.cleaned_data['value']:
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
        if attribute.name == 'Attitude' or attribute.name == 'Leader' or attribute.name == 'Power' \
                or attribute.name == 'Reach' or attribute.name == 'Ruler':
            form = ChangeOptionAttributeForm({'name': attribute.name, 'value': attribute_value.value})
            form.refresh_fields(attribute.thing_type, attribute.name)
        else:
            form = ChangeTextAttributeForm({'name': attribute.name, 'value': attribute_value.value})

    context = {
        'thing': thing,
        'header': 'Change {0} for {1}'.format(attribute.name, thing.name),
        'url': reverse('campaign:set_attribute', args=(thing.name, attribute.name)),
        'attribute': attribute,
        'form': form
    }
    return render(request, 'campaign/edit_page.html', build_context(context))


def bookmark(request, name):
    campaign = Campaign.objects.get(is_active=True)
    thing = get_object_or_404(Thing, campaign=campaign, name=name)

    if thing.is_bookmarked:
        thing.is_bookmarked = False
        thing.save()
    else:
        thing.is_bookmarked = True
        thing.save()

    return HttpResponseRedirect(reverse('campaign:detail', args=(thing.name,)))


def get_random_attribute(request, thing_type, attribute):
    campaign = Campaign.objects.get(is_active=True)
    result = get_random_attribute_raw(campaign=campaign, thing_type=thing_type, attribute=attribute)
    if result:
        return JsonResponse({
            'name': result
        })
    else:
        return JsonResponse({})


def get_random_attribute_in_category(request, thing_type, attribute, category):
    result = get_random_attribute_in_category_raw(thing_type, attribute, category)
    if result:
        return JsonResponse({
            'name': result
        })
    else:
        return JsonResponse({})


def change_campaign(request, name):
    new_campaign = get_object_or_404(Campaign, name=name)
    old_campaign = Campaign.objects.get(is_active=True)

    old_campaign.is_active = False
    old_campaign.save()
    new_campaign.is_active = True
    new_campaign.save()

    return HttpResponseRedirect(reverse('campaign:list_bookmarks'))


def manage_randomizer_options(request, thing_type, attribute):
    randomizer_attribute = get_object_or_404(RandomizerAttribute, thing_type__name__iexact=thing_type, name__iexact=attribute)
    if request.method == 'POST':
        if len(RandomizerAttributeCategory.objects.filter(attribute=randomizer_attribute)) > 0:
            form = SelectCategoryForAttributeForm(request.POST)
            form.refresh_fields(thing_type, attribute)
            if form.is_valid():
                return HttpResponseRedirect(reverse('campaign:manage_randomizer_options_for_category', args=(thing_type, attribute, form.cleaned_data['category'])))
        else:
            form = EditOptionalTextFieldForm(request.POST)
            if form.is_valid():
                RandomizerAttributeOption.objects.filter(attribute=randomizer_attribute).delete()
                for option in set([o.strip() for o in form.cleaned_data['value'].split('\n')]):
                    if option:
                        randomizer_option = RandomizerAttributeOption(attribute=randomizer_attribute, name=option)
                        randomizer_option.save()
                return HttpResponseRedirect(reverse('campaign:list_bookmarks'))
    else:
        if len(RandomizerAttributeCategory.objects.filter(attribute=randomizer_attribute)) > 0:
            form = SelectCategoryForAttributeForm()
            form.refresh_fields(thing_type, attribute)
        else:
            options = [o.name for o in RandomizerAttributeOption.objects.filter(attribute=randomizer_attribute).order_by('name')]
            form = EditOptionalTextFieldForm({'value': '\n'.join(options)})

    context = {
        'form': form,
        'header': 'Edit options for {0} {1}'.format(thing_type.lower(), attribute.lower()),
        'url': reverse('campaign:manage_randomizer_options', args=(thing_type, attribute))
    }
    return render(request, 'campaign/edit_page.html', build_context(context))


def manage_randomizer_options_for_category(request, thing_type, attribute, category):
    randomizer_attribute = get_object_or_404(RandomizerAttribute, thing_type__name__iexact=thing_type, name__iexact=attribute)
    randomizer_attribute_category = get_object_or_404(RandomizerAttributeCategory,
                                                      attribute=randomizer_attribute,
                                                      name__iexact=category)
    if request.method == 'POST':
        form = EditOptionalTextFieldForm(request.POST)
        if form.is_valid():
            RandomizerAttributeCategoryOption.objects.filter(category=randomizer_attribute_category).delete()
            for option in set([o.strip() for o in form.cleaned_data['value'].split('\n')]):
                if option:
                    randomizer_attribute_category_option = RandomizerAttributeCategoryOption(category=randomizer_attribute_category,
                                                                                             name=option)
                    randomizer_attribute_category_option.save()
            return HttpResponseRedirect(reverse('campaign:list_bookmarks'))
    else:
        form = EditOptionalTextFieldForm({'value': '\n'.join([o.name for o in RandomizerAttributeCategoryOption.objects.filter(category=randomizer_attribute_category).order_by('name')])})

    context = {
        'form': form,
        'header': 'Edit options for {0} {1} randomizer'.format(category, attribute),
        'url': reverse('campaign:manage_randomizer_options_for_category', args=(thing_type, attribute, category))
    }
    return render(request, 'campaign/edit_page.html', build_context(context))


def generate_random_attributes_for_thing(request, name, attribute):
    campaign = get_object_or_404(Campaign, is_active=True)
    thing = get_object_or_404(Thing, campaign=campaign, name__iexact=name)
    randomizer_attribute = get_object_or_404(RandomizerAttribute, thing_type=thing.thing_type, name__iexact=attribute)

    generate_random_attributes_for_thing_raw(campaign=campaign, thing=thing, attribute=randomizer_attribute)
    return HttpResponseRedirect(reverse('campaign:detail', args=(thing.name,)))


def add_random_attribute_for_thing(request, name):
    campaign = get_object_or_404(Campaign, is_active=True)
    thing = get_object_or_404(Thing, campaign=campaign, name=name)

    if request.method == 'POST':
        form = EditOptionalTextFieldForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['value']:
                random_attribute = RandomAttribute(thing=thing, text=form.cleaned_data['value'])
                random_attribute.save()
            return HttpResponseRedirect(reverse('campaign:detail', args=(thing.name,)))
    else:
        form = EditOptionalTextFieldForm()

    context = {
        'form': form,
        'header': 'Add random attribute for {0}'.format(thing.name),
        'url': reverse('campaign:add_one_random', args=(thing.name,))
    }
    return render(request, 'campaign/edit_page.html', build_context(context))


def edit_random_attribute_for_thing(request, name, random_attribute_id):
    campaign = get_object_or_404(Campaign, is_active=True)
    thing = get_object_or_404(Thing, campaign=campaign, name=name)
    random_attribute = get_object_or_404(RandomAttribute, thing=thing, pk=random_attribute_id)

    if request.method == 'POST':
        form = EditOptionalTextFieldForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['value']:
                random_attribute.text = form.cleaned_data['value']
                random_attribute.save()
            else:
                random_attribute.delete()
            return HttpResponseRedirect(reverse('campaign:detail', args=(thing.name,)))
    else:
        form = EditOptionalTextFieldForm({'value': random_attribute.text})

    context = {
        'form': form,
        'header': 'Edit random attribute for {0}'.format(thing.name),
        'url': reverse('campaign:edit_random', args=(thing.name, random_attribute_id))
    }
    return render(request, 'campaign/edit_page.html', build_context(context))


def delete_random_attribute_for_thing(request, name, random_attribute_id):
    campaign = get_object_or_404(Campaign, is_active=True)
    thing = get_object_or_404(Thing, campaign=campaign, name=name)

    try:
        RandomAttribute.objects.get(thing=thing, pk=random_attribute_id).delete()
    except RandomAttribute.DoesNotExist:
        logger.warn('Tried to delete a nonexistant random attribute from {0}.'.format(thing.name))

    return HttpResponseRedirect(reverse('campaign:detail', args=(thing.name,)))


def add_preset(request):
    campaign = get_object_or_404(Campaign, is_active=True)
    if request.method == 'POST':
        form = NewPreset(request.POST)
        form.refresh_fields()
        if form.is_valid():
            preset = WeightPreset(campaign=campaign, name=form.cleaned_data['name'], attribute_name=form.cleaned_data['attribute_name'])
            preset.save()
            return HttpResponseRedirect(reverse('campaign:manage_preset', args=(form.cleaned_data['name'], form.cleaned_data['attribute_name'])))
    else:
        form = NewPreset()
        form.refresh_fields()

    context = {
        'form': form,
        'header': 'Create a new preset',
        'url': reverse('campaign:add_preset')
    }
    return render(request, 'campaign/edit_page.html', build_context(context))


def select_preset(request, attribute_name):
    campaign = get_object_or_404(Campaign, is_active=True)
    if request.method == 'POST':
        form = SelectPreset(request.POST)
        form.refresh_fields(attribute_name, campaign)
        if form.is_valid():
            return HttpResponseRedirect(reverse('campaign:manage_preset', args=(form.cleaned_data['preset'], attribute_name)))
    else:
        form = SelectPreset()
        form.refresh_fields(attribute_name, campaign)

    context = {
        'form': form,
        'header': 'Select a {0} preset to edit'.format(attribute_name),
        'url': reverse('campaign:select_preset', args=(attribute_name,))
    }
    return render(request, 'campaign/edit_page.html', build_context(context))


def manage_weights(request, preset_name, attribute_name):
    campaign = get_object_or_404(Campaign, is_active=True)
    weight_preset = get_object_or_404(WeightPreset, campaign=campaign, name=preset_name, attribute_name=attribute_name)

    if request.method == 'POST':
        form = EditOptionalTextFieldForm(request.POST)
        if form.is_valid():
            Weight.objects.filter(weight_preset=weight_preset).delete()
            for weighted_name in form.cleaned_data['value'].split('\n'):
                parts = weighted_name.split('*')
                if len(parts) == 2:
                    weight = Weight(weight_preset=weight_preset, name_to_weight=parts[0].strip(), weight=int(parts[1]))
                    weight.save()
            return HttpResponseRedirect(reverse('campaign:list_bookmarks'))
    else:
        existing_weights = ['{0}*{1}'.format(w.name_to_weight, w.weight) for w in Weight.objects.filter(weight_preset=weight_preset)]
        form = EditOptionalTextFieldForm({'value': '\n'.join(existing_weights)})

    context = {
        'form': form,
        'header': 'Manage {0} preset for {1}'.format(attribute_name, preset_name),
        'url': reverse('campaign:manage_preset', args=(preset_name, attribute_name))
    }
    return render(request, 'campaign/edit_page.html', build_context(context))


def select_object_to_generate(request, thing_type):
    thing_type = get_object_or_404(ThingType, name__iexact=thing_type)
    if request.method == 'POST':
        form = SelectGeneratorObjectWithLocation(request.POST)
        form.refresh_fields(thing_type)
        if form.is_valid():
            if form.cleaned_data['parent']:
                return HttpResponseRedirect(reverse('campaign:generate_in_location',
                                                    args=(form.cleaned_data['parent'],
                                                          form.cleaned_data['generator_object'])))
            else:
                return HttpResponseRedirect(reverse('campaign:generate', args=(form.cleaned_data['generator_object'],)))
    else:
        form = SelectGeneratorObjectWithLocation()
        form.refresh_fields(thing_type)
    context = {
        'form': form,
        'header': 'Select a thing to generate',
        'url': reverse('campaign:select_generator', args=(thing_type.name,))
    }
    return render(request, 'campaign/edit_page.html', build_context(context))


def generate_object(request, name):
    generator_object = get_object_or_404(GeneratorObject, name=name)
    campaign = get_object_or_404(Campaign, is_active=True)
    thing = generate_thing(generator_object, campaign)
    return HttpResponseRedirect(reverse('campaign:detail', args=(thing.name,)))


def generate_object_in_location(request, location_name, generator_name):
    generator_object = get_object_or_404(GeneratorObject, name=generator_name)
    campaign = get_object_or_404(Campaign, is_active=True)
    parent = get_object_or_404(Thing, thing_type__name='Location', name__iexact=location_name)
    thing = generate_thing(generator_object, campaign, parent)
    if thing:
        parent.children.add(thing)
        parent.save()
        return HttpResponseRedirect(reverse('campaign:detail', args=(thing.name,)))
    else:
        return HttpResponseRedirect(reverse('campaign:detail', args=(parent.name,)))


def new_generator_object(request, thing_type_name):
    thing_type = get_object_or_404(ThingType, name=thing_type_name)

    if request.method == 'POST':
        form = GeneratorObjectForm(request.POST)
        form.refresh_fields(thing_type)
        if form.is_valid():
            generator_object = save_new_generator(thing_type=thing_type, form_data=form.cleaned_data)
            return HttpResponseRedirect(reverse('campaign:list_bookmarks'))
        else:
            logger.info(form.errors)
    else:
        form = GeneratorObjectForm()
        form.refresh_fields(thing_type)

    context = {
        'form': form,
        'header': 'Create a new generator',
        'url': reverse('campaign:new_generator', args=(thing_type.name,))
    }

    return render(request, 'campaign/edit_page.html', build_context(context))


def edit_generator_object(request, name):
    generator_object = get_object_or_404(GeneratorObject, name__iexact=name)

    if request.method == 'POST':
        form = GeneratorObjectForm(request.POST)
        form.refresh_fields(generator_object.thing_type)
        if form.is_valid():
            generator_object = edit_generator(generator_object, form.cleaned_data)
            return HttpResponseRedirect(reverse('campaign:list_bookmarks'))
        else:
            logger.info(form.errors)
    else:
        contains = ''
        for container in GeneratorObjectContains.objects.filter(generator_object=generator_object):
            if container.percent_chance_for_one:
                contains += '{0}% {1}.{2}\n'.format(container.percent_chance_for_one,
                                                    container.contained_object.thing_type.name,
                                                    container.contained_object.name)
            elif container.min_objects == 1 and container.max_objects == 1:
                contains += '{0}.{1}\n'.format(container.contained_object.thing_type.name,
                                               container.contained_object.name)
            else:
                contains += '{0}-{1} {2}.{3}\n'.format(container.min_objects, container.max_objects,
                                                     container.contained_object.thing_type.name,
                                                     container.contained_object.name)
        mappings = ''
        for mapping in GeneratorObjectFieldToRandomizerAttribute.objects.filter(generator_object=generator_object):
            if mapping.field_name:
                if mapping.randomizer_attribute_category:
                    mappings += '{0}: {1}.{2}\n'.format(mapping.field_name,
                                                      mapping.randomizer_attribute_category.attribute.name,
                                                      mapping.randomizer_attribute_category.name)
                elif mapping.randomizer_attribute:
                    mappings += '{0}: {1}\n'.format(mapping.field_name,
                                                  mapping.randomizer_attribute.name)
            elif mapping.randomizer_attribute_category:
                mappings += '{0}.{1}\n'.format(mapping.randomizer_attribute_category.attribute.name,
                                             mapping.randomizer_attribute_category.name)
            elif mapping.randomizer_attribute:
                mappings += '{0}\n'.format(mapping.randomizer_attribute.name)
        form = GeneratorObjectForm({
            'name': generator_object.name,
            'inherit_settings_from': generator_object.inherit_settings_from,
            'attribute_for_container': generator_object.attribute_for_container,
            'contains': contains,
            'mappings': mappings
        })

    context = {
        'form': form,
        'header': 'Edit {0} generator'.format(generator_object.name),
        'url': reverse('campaign:edit_generator', args=(generator_object.name,))
    }

    return render(request, 'campaign/edit_page.html', build_context(context))


def select_generator_to_edit(request, thing_type_name):
    thing_type = get_object_or_404(ThingType, name__iexact=thing_type_name)

    if request.method == 'POST':
        form = SelectGeneratorObject(request.POST)
        form.refresh_fields(thing_type)

        if form.is_valid():
            return HttpResponseRedirect(reverse('campaign:edit_generator', args=(form.cleaned_data['generator_object'],)))
    else:
        form = SelectGeneratorObject()
        form.refresh_fields(thing_type)

    context = {
        'form': form,
        'header': 'Select {0} generator to edit'.format(thing_type.name),
        'url': reverse('campaign:manage_generators', args=(thing_type.name,))
    }

    return render(request, 'campaign/edit_page.html', build_context(context))
