from django.contrib import admin
from . models import Customer
from . models import Restaurant
from . models import Item
from . models import Cart

# Register your models here.
admin.site.register(Customer)
admin.site.register(Restaurant)
admin.site.register(Item)
admin.site.register(Cart)