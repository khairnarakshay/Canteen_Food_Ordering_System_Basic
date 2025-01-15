from django.contrib import admin
from .models import FoodItem
from django.contrib import admin

admin.site.site_header = "WLCOME ADMIN "  # Change the header at the top
admin.site.site_title = "Admin Portal"  # Change the title in the browser tab
admin.site.index_title = "Welcome to Shety's Canteen"  # Change the dashboard text


# Register your models here.
@admin.register(FoodItem)
class FoodItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'price', 'description', 'image')