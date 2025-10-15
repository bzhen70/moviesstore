from django.contrib import admin
from .models import Order, Item, MovieLocationTrend

admin.site.register(Order)
admin.site.register(Item)
admin.site.register(MovieLocationTrend)