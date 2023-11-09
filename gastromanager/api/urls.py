from django.urls import path
from . import views


"""app_name = "api" """

urlpatterns = [
    path("welcome/", views.welcome_page, name="welcome"),
    path("staff/", views.staff_view, name="staff_view"),
    path("stock/", views.stock_view, name="stock_view"),
    path("journal/", views.view_journal, name="view_journal"),
    path("recipes/", views.RecipeListView.as_view(), name="recipe_list"),
    path("recipes/<int:pk>/", views.recipe_detail, name="recipe_detail"),
    path("recipes/create/", views.create_recipe, name="create_recipe"),
    path("recipes/update/<int:pk>/", views.update_recipe, name="update_recipe"),
    path("recipes/delete/<int:pk>/", views.delete_recipe, name="delete_recipe"),
    path("production/", views.production_view, name="production_view"),
    path("stock-takeout/", views.stock_takeout_view, name="stock_takeout_view"),
    path("add-ingredient/", views.add_ingredient, name="add_ingredient"),
    path(
        "production-calculator/",
        views.production_calculator_view,
        name="production_calculator",
    ),
    path("edit-profile/<int:user_id>", views.edit_profile, name="edit_profile"),
    path(
        "ingredient-inventory/",
        views.ingredient_inventory_view,
        name="ingredient_inventory",
    ),
    path("logout/", views.custom_logout, name="custom_logout"),
    path("profile/<int:user_id>/", views.view_profile, name="view_profile"),
    path("staff_members/", views.staff_member_list, name="staff_member_list"),
    # TODO: working_hours_list dose not exists
    # path(
    #     "working_hours/<int:staff_member_id>/",
    #     views.working_hours_list,
    #     name="working_hours_list",
    # ),
    path("scan/", views.scan_qr_code, name="scan_qr_code"),
    path("badge/", views.generate_employee_badge, name="badge_maker"),
    path(
        "working_hours/<int:staff_member_id>/",
        views.working_hours_list,
        name="working_hours_list",
    ),
]
