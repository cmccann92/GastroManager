import pytest
from datetime import timedelta
import os

from django.utils import timezone
from django.test import Client, TestCase
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.contrib.auth import get_user_model
from api.models import (
    Ingredient,
    IngredientInventory,
    Recipe,
    RecipeIngredient,
    IceCreamProduction,
    StockItem,
    IceCreamStockTakeOut,
    IngredientIncoming,
)
from django.test import Client

from api.forms import RecipeForm, ProductionCalculatorForm
from api.models import (
    Ingredient,
    IngredientInventory,
    Recipe,
    RecipeIngredient,
    IceCreamProduction,
    StockItem,
    IceCreamStockTakeOut,
    IngredientIncoming,
    UserProfile,
    WorkingHours,
    EmployeeBadge,
)


# fixture: These fixtures ensure that the test cases have consistent and controlled data to work with, improving the reliability of the tests.


@pytest.fixture
def test_create_ingredient():
    return Ingredient.objects.create(name="Chocolate", unit_of_measurement="grams")


@pytest.fixture
def test_create_user():
    user = get_user_model().objects.create_user(
        username="testuser", password="testpassword"
    )
    return user


@pytest.fixture
def test_create_recipe(create_ingredient):
    ingredient = create_ingredient
    recipe = Recipe.objects.create(flavor="Chocolate Ice Cream", is_base=False)
    RecipeIngredient.objects.create(
        recipe_name=recipe, ingredient=ingredient, quantity=100
    )
    return recipe


@pytest.fixture
def test_create_base_recipe():
    return Recipe.objects.create(flavor="Vanilla Base", is_base=True)


@pytest.fixture
def test_create_stock_item(create_recipe):
    recipe = create_recipe
    return StockItem.objects.create(recipe=recipe, size=0.5, quantity=100)


@pytest.fixture
def test_create_ice_cream_production(create_recipe, create_user):
    recipe = create_recipe
    user = create_user
    return IceCreamProduction.objects.create(
        recipe=recipe, container_size=0.5, quantity_produced=10, produced_by=user
    )


@pytest.fixture
def test_create_ice_cream_stock_take_out(create_stock_item, create_user):
    stock_item = create_stock_item
    user = create_user
    return IceCreamStockTakeOut.objects.create(
        ice_cream_production=stock_item, quantity_moved=10, moved_by=user
    )


@pytest.fixture
def test_client():
    return Client()


# Validation Test: Check that ingredient inventory updates correctly upon incoming ingredients.
@pytest.mark.django_db
def test_ingredient_inventory_update_on_incoming(create_ingredient):
    ingredient = create_ingredient()
    initial_quantity = 0
    incoming_quantity = 100
    IngredientInventory.update_or_create_inventory(ingredient, incoming_quantity)
    updated_inventory = IngredientInventory.objects.get(ingredient_name=ingredient)
    assert updated_inventory.quantity == initial_quantity + incoming_quantity


# Production and Inventory Test: Check ice cream production and inventory update.
@pytest.mark.django_db
def test_ice_cream_production_and_inventory_update(create_recipe, create_user):
    recipe = create_recipe()
    user = create_user()
    production = IceCreamProduction.objects.create(
        recipe=recipe, container_size=0.5, quantity_produced=10, produced_by=user
    )
    inventory = IngredientInventory.objects.get(
        ingredient_name=recipe.recipeingredient_set.first().ingredient
    )
    stock_item = StockItem.objects.get(recipe=recipe, size=0.5)

    assert inventory.quantity == 100 - (
        recipe.recipeingredient_set.first().quantity * production.quantity_produced
    )
    assert stock_item.quantity == production.quantity_produced


# Negative Production Test: Check that negative production quantities raise a ValidationError.
@pytest.mark.django_db
def test_negative_production(create_recipe, create_user):
    recipe = create_recipe()
    user = create_user()
    with pytest.raises(ValidationError):
        IceCreamProduction.objects.create(
            recipe=recipe, container_size=0.5, quantity_produced=200, produced_by=user
        )


# Update Stock Test: Check that stock updates correctly when adding production to existing stock.
@pytest.mark.django_db
def test_update_stock_on_production_existing_stock_item(
    create_recipe, create_user, client
):
    recipe = create_recipe()
    user = create_user()
    StockItem.objects.create(recipe=recipe, size=0.5, quantity=5)  # Existing stock

    production = IceCreamProduction.objects.create(
        recipe=recipe, container_size=0.5, quantity_produced=10, produced_by=user
    )
    stock_item = StockItem.objects.get(recipe=recipe, size=0.5)

    assert stock_item.quantity == 15  # Check that stock is updated correctly


# Base Production and Inventory Test: Check base ice cream production and inventory update.
@pytest.mark.django_db
def test_base_production_and_inventory_update(create_base_recipe, create_user, client):
    recipe = create_base_recipe()
    user = create_user()
    production = IceCreamProduction.objects.create(
        recipe=recipe, container_size=0.5, quantity_produced=10, produced_by=user
    )
    inventory = IngredientInventory.objects.get(ingredient_name=recipe.flavor)

    assert inventory.quantity == production.quantity_produced


# Stock Takeout Test: Check stock takeout operation.
@pytest.mark.django_db
def test_stock_takeout(create_stock_item, create_user):
    stock_item = create_stock_item()
    user = create_user()
    quantity_taken = 10
    stock_takeout = IceCreamStockTakeOut.objects.create(
        ice_cream_production=stock_item, quantity_moved=quantity_taken, moved_by=user
    )
    stock_item.refresh_from_db()

    assert stock_takeout.quantity_moved == quantity_taken
    assert stock_item.quantity == 100 - quantity_taken


# Negative Stock Takeout Test: Check that negative stock takeout quantities raise a ValidationError.
@pytest.mark.django_db
def test_negative_stock_takeout(create_stock_item, create_user):
    stock_item = create_stock_item()
    user = create_user()
    with pytest.raises(ValidationError):
        IceCreamStockTakeOut.objects.create(
            ice_cream_production=stock_item, quantity_moved=200, moved_by=user
        )


# Insufficient Stock Takeout Test: Check that insufficient stock for takeout raises a ValidationError.
@pytest.mark.django_db
def test_stock_takeout_not_enough_stock(create_stock_item, create_user):
    stock_item = create_stock_item()
    user = create_user()
    new_stock_item = StockItem.objects.create(
        recipe=stock_item.recipe, size=0.5, quantity=5
    )  # Low stock

    with pytest.raises(ValidationError):
        IceCreamStockTakeOut.objects.create(
            ice_cream_production=new_stock_item, quantity_moved=10, moved_by=user
        )


# Ingredient Form Validation Test: Check ingredient form validation, including negative quantity.
@pytest.mark.django_db
def test_ingredient_form_validation():
    data = {
        "ingredient_name": "Chocolate",
        "quantity": -100,  # Test with negative quantity
        "unit_weight": "grams",
    }
    form = RecipeForm(data=data)
    assert not form.is_valid()  # Form should not be valid


# Production Calculator Form Validation Test: Check production calculator form validation, including negative quantity.
@pytest.mark.django_db
def test_production_calculator_form_validation():
    data = {
        "recipe": None,  # No recipe selected
        "desired_quantity": -100,  # Negative desired quantity
    }
    form = ProductionCalculatorForm(data=data)
    assert not form.is_valid()  # Form should not be valid


# Test case: Edit recipe with ingredients
@pytest.mark.django_db
def test_edit_recipe_with_ingredients(create_recipe, client):
    recipe = create_recipe()
    # Add more ingredients to the existing recipe
    recipe_ingredient_count = recipe.recipeingredient_set.count()
    data = {
        "flavor": "Updated Flavor",
    }
    response = client.post(reverse("update_recipe", args=[recipe.id]), data)
    assert response.status_code == 302  # Should redirect after editing
    assert (
        Recipe.objects.get(pk=recipe.id).flavor == "Updated Flavor"
    )  # Ensure the recipe is updated
    assert (
        recipe.recipeingredient_set.count() == recipe_ingredient_count
    )  # The ingredient count should not change
    # This test checks that editing a recipe only changes its name without affecting the number of ingredients.


# Test case: Create recipe with ingredients and quantities
@pytest.mark.django_db
def test_create_recipe_with_ingredients_and_quantities(create_ingredient, client):
    ingredient1 = create_ingredient()
    ingredient2 = create_ingredient()
    data = {
        "flavor": "New Recipe",
        "ingredients": [ingredient1.id, ingredient2.id],
        "ingredient_quantities": "100, 200",  # Corresponding quantities
    }
    response = client.post(reverse("create_recipe"), data)
    assert response.status_code == 302  # Should redirect after creation
    new_recipe = Recipe.objects.get(flavor="New Recipe")
    assert new_recipe.ingredients.count() == 2  # The recipe should have 2 ingredients
    assert (
        new_recipe.recipeingredient_set.get(ingredient=ingredient1).quantity == 100
    )  # Verify ingredient quantities
    assert new_recipe.recipeingredient_set.get(ingredient=ingredient2).quantity == 200
    # This test checks that a new recipe is created with specified ingredients and quantities.


# Test case: Unauthorized access to stock takeout view
@pytest.mark.django_db
def test_unauthorized_access_to_stock_takeout(client):
    response = client.get(reverse("stock_takeout"))
    assert response.status_code == 403  # Should receive a forbidden response
    # This test checks that unauthorized access to the stock takeout view returns a forbidden response.


# Test case: Unauthorized access to production calculator view
@pytest.mark.django_db
def test_unauthorized_access_to_production_calculator(client):
    response = client.get(reverse("production_calculator"))
    assert response.status_code == 403  # Should receive a forbidden response
    # This test checks that unauthorized access to the production calculator view returns a forbidden response.


# Test case: Unauthorized access to add ingredient view
@pytest.mark.django_db
def test_unauthorized_access_to_add_ingredient(client):
    response = client.get(reverse("add_ingredient"))
    assert response.status_code == 403  # Should receive a forbidden response
    # This test checks that unauthorized access to the add ingredient view returns a forbidden response.


# Test case: Stock update on adding a new recipe
@pytest.mark.django_db
def test_stock_update_on_adding_new_recipe(create_recipe, create_user, client):
    user = create_user()
    recipe = create_recipe()
    stock_item = StockItem.objects.create(recipe=recipe, size=0.5, quantity=10)

    new_recipe = Recipe.objects.create(flavor="New Flavor", is_base=False)
    production = IceCreamProduction.objects.create(
        recipe=new_recipe, container_size=0.5, quantity_produced=5, produced_by=user
    )
    stock_item.refresh_from_db()

    assert stock_item.quantity == 5  # Stock should be correctly updated
    # This test checks that stock quantity is updated when a new recipe is added and produced.


# Test case: Inventory update on recipe ingredient deletion
@pytest.mark.django_db
def test_inventory_update_on_recipe_ingredient_deletion(
    create_recipe, create_ingredient, client
):
    recipe = create_recipe()
    ingredient = create_ingredient()
    RecipeIngredient.objects.create(recipe=recipe, ingredient=ingredient, quantity=50)

    initial_inventory_quantity = ingredient.inventory.quantity
    response = client.post(
        reverse("update_recipe", args=[recipe.id]),
        {
            "recipeingredients_set-TOTAL_FORMS": 0,
            "recipeingredients_set-INITIAL_FORMS": 1,
        },
    )
    updated_inventory_quantity = IngredientInventory.objects.get(
        ingredient_name=ingredient
    ).quantity

    assert (
        initial_inventory_quantity == updated_inventory_quantity + 50
    )  # Inventory should decrease correctly
    # This test checks that the inventory is updated correctly when a recipe ingredient is removed.


# Test case: Inventory update on ingredient addition
@pytest.mark.django_db
def test_inventory_update_on_ingredient_addition(create_ingredient, client):
    initial_inventory_quantity = create_ingredient().inventory.quantity
    data = {
        "ingredient_name": "New Ingredient",
        "quantity": 100,
        "unit_weight": "grams",
    }
    response = client.post(reverse("add_ingredient"), data)
    updated_inventory_quantity = IngredientInventory.objects.get(
        ingredient_name__name="New Ingredient"
    ).quantity

    assert (
        initial_inventory_quantity + 100 == updated_inventory_quantity
    )  # Inventory should increase correctly
    # This test checks that the inventory is updated correctly when a new ingredient is added.


pytest.mark.django_db


def test_add_ingredient_with_expiration_date(create_ingredient, client):
    initial_inventory_quantity = create_ingredient().inventory.quantity
    data = {
        "ingredient_name": "New Ingredient with Expiration Date",
        "quantity": 200,
        "unit_weight": "grams",
        "expiration_date": "2023-12-31",
    }
    response = client.post(reverse("add_ingredient"), data)
    updated_inventory_quantity = IngredientInventory.objects.get(
        ingredient_name__name="New Ingredient with Expiration Date"
    ).quantity

    assert (
        initial_inventory_quantity + 200 == updated_inventory_quantity
    )  # Inventory should increase correctly
    assert (
        IngredientIncoming.objects.filter(
            ingredient__name="New Ingredient with Expiration Date"
        ).count()
        == 1
    )  # There should be one ingredient incoming record
    # This test checks that adding an ingredient with an expiration date correctly updates the inventory and records the incoming ingredient.


@pytest.mark.django_db
def test_insufficient_stock_takeout(create_stock_item, create_user, client):
    stock_item = create_stock_item()
    user = create_user()
    quantity_taken = (
        stock_item.quantity + 1
    )  # Attempt to take more than what is available
    with pytest.raises(ValidationError):
        response = client.post(
            reverse("stock_takeout"),
            {"stock_item": stock_item.id, "quantity_moved": quantity_taken},
        )
    # This test checks that attempting to take more stock quantity than what is available raises a validation error.


class EmployeeBadgeTest(TestCase):
    def test_generate_badge(self):
        employee = EmployeeBadge(employee_name="John Doe", employee_id=12345)
        employee.save()

        badge_file = employee.generate_badge()

        self.assertIsNotNone(badge_file)
        os.remove(badge_file)

        logo_path = "api/media/green_scoop.png"
        self.assertTrue(os.path.isfile(logo_path))

        employee.delete()


class WorkingHoursTest(TestCase):
    def setUp(self):
        self.user_profile = UserProfile.objects.create(
            username="testuser", password="password"
        )

    def test_recorded_time(self):
        clock_in_time = timezone.now() - timedelta(hours=2)
        clock_out_time = timezone.now()
        working_hours = WorkingHours.objects.create(
            employee=self.user_profile,
            clock_in=clock_in_time,
            clock_out=clock_out_time,
        )

        time_difference = clock_out_time - clock_in_time
        hours, remainder = divmod(time_difference.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        expected_time = f"{time_difference.days} days {hours} hours {minutes} minutes {seconds} seconds"

        self.assertEqual(working_hours.recorded_time(), expected_time)

    def test_recorded_time_when_clock_out_is_none(self):
        clock_in_time = timezone.now() - timedelta(hours=2)
        working_hours = WorkingHours.objects.create(
            employee=self.user_profile,
            clock_in=clock_in_time,
            clock_out=None,
        )

        self.assertIsNone(working_hours.recorded_time())
