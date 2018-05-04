from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
from .forms import ChangeCampaignForm
from .models import ThingType, Thing, Attribute, AttributeValue, UsefulLink, Campaign, RandomEncounterType, RandomEncounter


class ThingAdmin(admin.ModelAdmin):
    list_display = ['name', 'campaign']
    ordering = ['name']
    actions = ['change_campaign']

    def change_campaign(self, request, queryset):
        if 'apply' in request.POST:
            form = ChangeCampaignForm(request.POST)
            if form.is_valid():
                queryset.update(campaign=form.cleaned_data['campaign'])
            messages.success(request, "Changed the campaign.")
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
    change_campaign.short_description = 'Change campaign'


admin.site.register(ThingType)
admin.site.register(Thing, ThingAdmin)
admin.site.register(Attribute)
admin.site.register(AttributeValue)
admin.site.register(UsefulLink)
admin.site.register(Campaign)
admin.site.register(RandomEncounterType)
admin.site.register(RandomEncounter)