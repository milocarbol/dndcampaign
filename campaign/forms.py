from django import forms

from .models import Thing


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
    location = forms.ModelChoiceField(label='Located in', queryset=Thing.objects.filter(thing_type__name='Location').order_by('name'), required=False)
    factions = forms.ModelMultipleChoiceField(label='Factions', queryset=Thing.objects.filter(thing_type__name='Faction').order_by('name'), required=False)
    npcs = forms.ModelMultipleChoiceField(label='NPCs', queryset=Thing.objects.filter(thing_type__name='NPC').order_by('name'), required=False)


class NewFactionForm(forms.Form):
    MAGNITUDE_CHOICES = [
        ('Low', 'Low'),
        ('Moderate', 'Moderate'),
        ('High', 'High')
    ]

    name = forms.CharField(label='Name')
    description = forms.CharField(label='Description', widget=forms.Textarea)
    location = forms.ModelChoiceField(label='Located in', queryset=Thing.objects.filter(thing_type__name='Location').order_by('name'), required=False)
    npcs = forms.ModelMultipleChoiceField(label='NPCs', queryset=Thing.objects.filter(thing_type__name='NPC').order_by('name'), required=False)

    leader = forms.ModelChoiceField(label='Leader', queryset=Thing.objects.filter(thing_type__name='NPC').order_by('name'))
    attitude = forms.ChoiceField(label='Attitude', choices=ATTITUDE_CHOICES)
    power = forms.ChoiceField(label='Power', choices=MAGNITUDE_CHOICES)
    reach = forms.ChoiceField(label='Reach', choices=MAGNITUDE_CHOICES)


class NewNpcForm(forms.Form):
    name = forms.CharField(label='Name')
    description = forms.CharField(label='Description', widget=forms.Textarea)
    location = forms.ModelChoiceField(label='Located in', queryset=Thing.objects.filter(thing_type__name='Location').order_by('name'), required=False)
    factions = forms.ModelMultipleChoiceField(label='Member of', queryset=Thing.objects.filter(thing_type__name='Faction').order_by('name'), required=False)

    race = forms.CharField(label='Race')
    attitude = forms.ChoiceField(label='Attitude', choices=ATTITUDE_CHOICES)
    occupation = forms.CharField(label='Occupation', required=False)
    link = forms.CharField(label='D&D Beyond URL', required=False)
