from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from . import views


app_name = 'campaign'
urlpatterns = [
    path('', views.index, name='index'),
    path('thing/<name>', views.detail, name='detail'),
    path('search', views.search, name='search'),
    path('export', views.export, name='export'),
    path('import', csrf_exempt(views.import_campaign), name='import'),
    path('list/<type>', views.list_all, name='list')
]
