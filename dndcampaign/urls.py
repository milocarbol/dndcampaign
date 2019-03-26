from django.urls import include, path
from django.contrib import admin
from django.views.generic.base import RedirectView

urlpatterns = [
    path('campaign/', include('campaign.urls')),
    path('admin/', admin.site.urls),
    path('favicon.ico', RedirectView.as_view(url='/static/favicon.jpg', permanent=True))
]
