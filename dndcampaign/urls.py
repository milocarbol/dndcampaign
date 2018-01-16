from django.urls import include, path
from django.contrib import admin

urlpatterns = [
    path('campaign/', include('campaign.urls')),
    path('admin/', admin.site.urls),
]
