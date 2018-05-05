from django import forms

from .models import Thing, UsefulLink, Campaign


ATTITUDE_CHOICES = [
    ('Hostile', 'Hostile'),
    ('Neutral', 'Neutral'),
    ('Friendly', 'Friendly'),
    ('Loyal', 'Loyal')
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
    MAGNITUDE_CHOICES = [
        ('Low', 'Low'),
        ('Moderate', 'Moderate'),
        ('High', 'High')
    ]

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
    description = forms.CharField(label='Description', widget=forms.Textarea)
    location = forms.ModelChoiceField(label='Located in', queryset=Thing.objects.all(), required=False)
    factions = forms.ModelMultipleChoiceField(label='Member of', queryset=Thing.objects.all(), required=False)

    race = forms.CharField(label='Race')
    attitude = forms.ChoiceField(label='Attitude', choices=ATTITUDE_CHOICES)
    occupation = forms.CharField(label='Occupation', required=False)
    link = forms.CharField(label='D&D Beyond URL', required=False)

    def refresh_fields(self):
        self.fields['location'].queryset = Thing.objects.filter(campaign=Campaign.objects.get(is_active=True), thing_type__name='Location').order_by('name')
        self.fields['factions'].queryset = Thing.objects.filter(campaign=Campaign.objects.get(is_active=True), thing_type__name='Faction').order_by('name')


class AddLinkForm(forms.Form):
    name = forms.CharField(label='Name')
    value = forms.CharField(label='URL')


class EditEncountersForm(forms.Form):
    name = forms.HiddenInput()
    encounters = forms.CharField(label='Encounters', widget=forms.Textarea, required=False)


class ChangeCampaignForm(forms.Form):
    campaign = forms.ModelChoiceField(queryset=Campaign.objects.all())

