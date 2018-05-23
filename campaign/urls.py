from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from . import views


app_name = 'campaign'
urlpatterns = [
    path('', views.list_everything, name='list_everything'),
    path('thing/<name>', views.detail, name='detail'),
    path('search', views.search, name='search'),
    path('export', views.export, name='export'),
    path('import', views.import_campaign, name='import'),
    path('list/<thing_type>', views.list_all, name='list'),
    path('new/<thing_type>', views.new_thing, name='new_thing'),
    path('add_link/<name>', views.add_link, name='add_link'),
    path('edit_encounters/<name>/<type_name>', views.edit_random_encounters, name='edit_encounters'),
    path('edit_description/<name>', views.edit_description, name='edit_description'),
    path('change_campaign/<name>', views.change_campaign, name='change_campaign'),
    path('set_attribute/<name>/<attribute_name>', views.set_attribute, name='set_attribute'),
    path('remove_link/<name>/<link_name>', views.remove_link, name='remove_link'),
    path('edit_location/<name>', views.move_thing, name='move_thing'),
    path('random/<attribute>', views.get_random_attribute, name='get_random_attribute'),
    path('random/<attribute>/<category>', views.get_random_attribute_in_category, name='get_random_attribute_in_category'),
    path('manage/<thing_type>/<attribute>', views.manage_randomizer_options, name='manage_randomizer_options'),
    path('manage/<thing_type>/<attribute>/<category>', views.manage_randomizer_options_for_category, name='manage_randomizer_options_for_category')
]
