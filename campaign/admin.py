from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
from .forms import ChangeCampaignForm, CopyToCampaignForm
from .models import ThingType, Thing, Attribute, AttributeValue, UsefulLink, Campaign, RandomEncounterType, RandomEncounter, RandomizerAttribute, RandomizerAttributeOption, RandomizerAttributeCategoryOption, RandomizerAttributeCategory, RandomAttribute


class ThingAdmin(admin.ModelAdmin):
    list_display = ['campaign', 'name']
    ordering = ['campaign', 'name']
    actions = ['change_campaign', 'copy_to_campaign']

    def copy_thing(self, thing, old_campaign, new_campaign):
        thing.pk = None
        thing.campaign = new_campaign
        thing.save()

        old_thing = Thing.objects.get(name=thing.name, campaign=old_campaign)

        affected_tables = [
            AttributeValue.objects.filter(thing=old_thing),
            UsefulLink.objects.filter(thing=old_thing),
            RandomEncounter.objects.filter(thing=old_thing)
        ]

        for affected_table in affected_tables:
            for affected_row in affected_table:
                affected_row.pk = None
                affected_row.thing = thing
                affected_row.save()

    def change_campaign(self, request, queryset):
        if 'apply' in request.POST:
            form = ChangeCampaignForm(request.POST)
            if form.is_valid():
                queryset.update(campaign=form.cleaned_data['campaign'])
            messages.success(request, 'Changed the campaign.')
            return
        else:
            form = ChangeCampaignForm()
        return render(request,
                      'admin/set_campaign.html',
                      {
                          'title': 'Change campaign',
                          'things': queryset,
                          'path': request.get_full_path(),
                          'form': form
                      }
        )

    def copy_to_campaign(self, request, queryset):
        if 'apply' in request.POST:
            form = CopyToCampaignForm(request.POST)
            if form.is_valid():
                for thing in queryset:
                    old_campaign = thing.campaign
                    new_campaign = form.cleaned_data['campaign']
                    self.copy_thing(thing=thing, old_campaign=old_campaign, new_campaign=new_campaign)

                    if form.cleaned_data['copy_children']:
                        old_thing = Thing.objects.get(name=thing.name, campaign=old_campaign)
                        new_thing = Thing.objects.get(name=thing.name, campaign=new_campaign)
                        for child in old_thing.children.all():
                            self.copy_thing(thing=child, old_campaign=old_campaign, new_campaign=new_campaign)
                            new_thing.children.add(Thing.objects.get(name=child.name, campaign=new_campaign))
                        new_thing.save()

            messages.success(request, 'Copied to campaign.')
            return
        else:
            form = CopyToCampaignForm()
        return render(request,
                      'admin/copy_to_campaign.html',
                      {
                          'title': 'Copy to campaign',
                          'things': queryset,
                          'path': request.get_full_path(),
                          'form': form
                      }
        )

    change_campaign.short_description = 'Change campaign'
    copy_to_campaign.short_description = 'Copy to campaign'


admin.site.register(ThingType)
admin.site.register(Thing, ThingAdmin)
admin.site.register(Attribute)
admin.site.register(AttributeValue)
admin.site.register(UsefulLink)
admin.site.register(Campaign)
admin.site.register(RandomEncounterType)
admin.site.register(RandomEncounter)
admin.site.register(RandomizerAttribute)
admin.site.register(RandomizerAttributeOption)
admin.site.register(RandomizerAttributeCategory)
admin.site.register(RandomizerAttributeCategoryOption)
admin.site.register(RandomAttribute)