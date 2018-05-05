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
    path('move/options/<name>', views.move_thing_options, name='move_options'),
    path('move/confirm/<name>/to/<new_location_name>', views.move_thing_confirm, name='move_confirm'),
    path('new/<thing_type>', views.new_thing, name='new_thing'),
    path('add_link/<name>', views.add_link, name='add_link'),
    path('edit_encounters/<name>/<type_name>', views.edit_random_encounters, name='edit_encounters'),
    path('change_campaign/<name>', views.change_campaign, name='change_campaign')
]
