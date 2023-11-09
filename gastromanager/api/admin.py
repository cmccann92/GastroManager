from django.contrib import admin

from .models import (
    Address,
    StockItem,
    IceCreamProduction,
    IceCreamStockTakeOut,
    Recipe,
    Ingredient,
    IngredientIncoming,
    IngredientInventory,
    RecipeIngredient,
    UserProfile,
    Journal,
)

"""from django.contrib.auth.admin import UserAdmin"""

"""

from django.contrib.auth.admin import UserAdmin



class UserProfileAdmin(UserAdmin):
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            "Personal info",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "email",
                    "date_of_birth",
                    "address",
                    "phone",
                    "level",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
        ("User status", {"fields": ("is_active", "is_staff", "is_superuser")}),
    )


# Define an inline model for RecipeIngredient
class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 5  # Adjust this number to control how many ingredients you can add at once


# Customize the Recipe model in the admin panel
class RecipeAdmin(admin.ModelAdmin):
    list_display = ("flavor", "is_base")
    list_filter = ("is_base",)
    search_fields = ("flavor",)
    inlines = [RecipeIngredientInline]  # Add the inline model to the Recipe admin


class IngredientIncomingAdmin(admin.ModelAdmin):
    list_display = ["ingredient", "quantity", "date_received"]
    raw_id_fields = ["ingredient"]  # allow to look for available ingredient by name.


# Register models with the custom admin views
class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 5


class RecipeAdmin(admin.ModelAdmin):
    list_display = ("flavor", "is_base")
    list_filter = ("is_base",)
    search_fields = ("flavor",)
    inlines = [RecipeIngredientInline]


class IngredientIncomingAdmin(admin.ModelAdmin):
    list_display = ["ingredient", "quantity", "date_received"]
    raw_id_fields = ["ingredient"]

"""

admin.site.register(Address)
admin.site.register(Ingredient)
admin.site.register(IngredientInventory)
admin.site.register(IngredientIncoming),  # IngredientIncomingAdmin)
admin.site.register(Recipe),  # RecipeAdmin)
admin.site.register(RecipeIngredient),
admin.site.register(IceCreamProduction),
admin.site.register(StockItem),
admin.site.register(IceCreamStockTakeOut),
admin.site.register(UserProfile),  # UserProfileAdmin)
admin.site.register(Journal)
