from django.contrib import admin
from .models import ThingType, Thing, Attribute, AttributeValue, UsefulLink


admin.site.register(ThingType)
admin.site.register(Thing)
admin.site.register(Attribute)
admin.site.register(AttributeValue)
admin.site.register(UsefulLink)