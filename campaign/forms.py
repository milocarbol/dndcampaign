from django import forms
from django.shortcuts import get_object_or_404

from .models import Thing, Attribute, AttributeValue, Campaign, NpcOccupationType, NpcRace, RandomizerAttribute, RandomizerAttributeCategory


ATTITUDE_CHOICES = [
    ('Hostile', 'Hostile'),
    ('Neutral', 'Neutral'),
    ('Friendly', 'Friendly'),
    ('Loyal', 'Loyal')
]

MAGNITUDE_CHOICES = [
    ('Low', 'Low'),
    ('Moderate', 'Moderate'),
    ('High', 'High')
]


class SearchForm(forms.Form):
    search_text = forms.CharField(label='Search', max_length=50, widget=forms.TextInput(attrs={
        'class': 'form-control mr-sm-2',
        'type': 'search',
        'placeholder': 'Search',
        'aria-label': 'Search'
    }))


class UploadFileForm(forms.Form):
    file = forms.FileField()


class NewLocationForm(forms.Form):
    name = forms.CharField(label='Name')
    description = forms.CharField(label='Description', widget=forms.Textarea)
    location = forms.ModelChoiceField(label='Located in', queryset=Thing.objects.all(), required=False)
    factions = forms.ModelMultipleChoiceField(label='Factions', queryset=Thing.objects.all(), required=False)
    npcs = forms.ModelMultipleChoiceField(label='NPCs', queryset=Thing.objects.all(), required=False)

    def refresh_fields(self):
        self.fields['location'].queryset = Thing.objects.filter(campaign=Campaign.objects.get(is_active=True), thing_type__name='Location').order_by('name')
        self.fields['factions'].queryset = Thing.objects.filter(campaign=Campaign.objects.get(is_active=True), thing_type__name='Faction').order_by('name')
        self.fields['npcs'].queryset = Thing.objects.filter(campaign=Campaign.objects.get(is_active=True), thing_type__name='NPC').order_by('name')


class NewFactionForm(forms.Form):

    name = forms.CharField(label='Name')
    description = forms.CharField(label='Description', widget=forms.Textarea)
    location = forms.ModelChoiceField(label='Located in', queryset=Thing.objects.all(), required=False)
    npcs = forms.ModelMultipleChoiceField(label='NPCs', queryset=Thing.objects.all(), required=False)

    leader = forms.ModelChoiceField(label='Leader', queryset=Thing.objects.all())
    attitude = forms.ChoiceField(label='Attitude', choices=ATTITUDE_CHOICES)
    power = forms.ChoiceField(label='Power', choices=MAGNITUDE_CHOICES)
    reach = forms.ChoiceField(label='Reach', choices=MAGNITUDE_CHOICES)

    def refresh_fields(self):
        self.fields['location'].queryset = Thing.objects.filter(campaign=Campaign.objects.get(is_active=True), thing_type__name='Location').order_by('name')
        self.fields['npcs'].queryset = Thing.objects.filter(campaign=Campaign.objects.get(is_active=True), thing_type__name='NPC').order_by('name')
        self.fields['leader'].queryset = Thing.objects.filter(campaign=Campaign.objects.get(is_active=True), thing_type__name='NPC').order_by('name')


class NewNpcForm(forms.Form):
    name = forms.CharField(label='Name')
    race = forms.CharField(label='Race')
    occupation = forms.CharField(label='Occupation', required=False)
    description = forms.CharField(label='Description', widget=forms.Textarea)
    location = forms.ModelChoiceField(label='Located in', queryset=Thing.objects.all(), required=False)
    factions = forms.ModelMultipleChoiceField(label='Member of', queryset=Thing.objects.all(), required=False)
    attitude = forms.ChoiceField(label='Attitude', choices=ATTITUDE_CHOICES)
    link = forms.CharField(label='D&D Beyond URL', required=False)

    def refresh_fields(self):
        self.fields['location'].queryset = Thing.objects.filter(campaign=Campaign.objects.get(is_active=True), thing_type__name='Location').order_by('name')
        self.fields['factions'].queryset = Thing.objects.filter(campaign=Campaign.objects.get(is_active=True), thing_type__name='Faction').order_by('name')


class AddLinkForm(forms.Form):
    name = forms.CharField(label='Name')
    value = forms.CharField(label='URL')


class EditOptionalTextFieldForm(forms.Form):
    value = forms.CharField(label='Value', widget=forms.Textarea, required=False)


class EditEncountersForm(forms.Form):
    encounters = forms.CharField(label='Encounters', widget=forms.Textarea, required=False)


class EditDescriptionForm(forms.Form):
    description = forms.CharField(label='Description', widget=forms.Textarea)


class ChangeTextAttributeForm(forms.Form):
    value = forms.CharField(label='Value')


class ChangeOptionAttributeForm(forms.Form):
    value = forms.ChoiceField(label='Value', choices=[])

    def refresh_fields(self, thing_type, name):
        attribute = get_object_or_404(Attribute, thing_type=thing_type, name=name)
        if attribute.name == 'Attitude':
            self.fields['value'].choices = ATTITUDE_CHOICES
        elif attribute.name == 'Leader':
            choices = []
            for npc in Thing.objects.filter(campaign=Campaign.objects.get(is_active=True), thing_type__name='NPC').order_by('name'):
                choices.append((npc.name, npc.name),)
            self.fields['value'].choices = choices
        elif attribute.name == 'Power' or attribute.name == 'Reach':
            self.fields['value'].choices = MAGNITUDE_CHOICES


class ChangeLocationForm(forms.Form):
    location = forms.ModelChoiceField(label='Move to', queryset=Thing.objects.all(), required=False)
    clear_location = forms.BooleanField(label='Clear location', required=False)

    def refresh_fields(self):
        self.fields['location'].queryset = Thing.objects.filter(campaign=Campaign.objects.get(is_active=True), thing_type__name='Location').order_by('name')


class ChangeCampaignForm(forms.Form):
    campaign = forms.ModelChoiceField(queryset=Campaign.objects.all())


class CopyToCampaignForm(forms.Form):
    campaign = forms.ModelChoiceField(queryset=Campaign.objects.all())
    copy_children = forms.BooleanField(required=False)


class SelectCategoryForAttributeForm(forms.Form):
    category = forms.ChoiceField(label='Categories', choices=[])

    def refresh_fields(self, thing_type, attribute_name):
        attribute = get_object_or_404(RandomizerAttribute, thing_type__name__iexact=thing_type, name__iexact=attribute_name)
        choices = [(c.name, c.name) for c in RandomizerAttributeCategory.objects.filter(attribute=attribute).order_by('name')]
        self.fields['category'].choices = choices
