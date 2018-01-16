from django.urls import path

from . import views


app_name = 'campaign'
urlpatterns = [
    path('', views.index, name='index'),
    path('<name>', views.detail, name='detail'),
]
