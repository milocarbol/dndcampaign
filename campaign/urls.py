from django.urls import path

from . import views


app_name = 'campaign'
urlpatterns = [
    path('', views.index, name='index'),
    path('thing/<name>', views.detail, name='detail'),
    path('search', views.search, name='search'),
    path('export', views.export, name='export')
]
