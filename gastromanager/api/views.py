import cv2
from pyzbar.pyzbar import decode

from django.shortcuts import render, redirect, get_object_or_404
from .activities import (
    activity_staff_view,
    activity_edit_profile,
    scan_journal_log,
)
from .models import (
    UserProfile,
    Recipe,
    Ingredient,
    IngredientInventory,
    IngredientIncoming,
    RecipeIngredient,
    IceCreamProduction,
    StockItem,
    IceCreamStockTakeOut,
    Journal,
)
from .forms import (
    RecipeForm,
    ProductionCalculatorForm,
    CustomUserForm,
    IngredientInventoryUpdateForm,
    CustomUserNormalForm,
    ClockInOutForm,
)
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView
from django.forms import modelformset_factory
from django.db.models.signals import post_save
from django.dispatch import receiver
from .decorators import (
    manager_required,
    service_required,
    production_required,
    register_activity,
)
from django.utils.decorators import method_decorator
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.http import Http404, HttpResponseForbidden, HttpRequest
from django.contrib.auth import logout
from django.utils import timezone
from django.db.models import Q
from datetime import datetime
import os


from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.forms import modelformset_factory
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.decorators import method_decorator
from django.views.generic import ListView


from .models import (
    UserProfile,
    Recipe,
    Ingredient,
    IngredientInventory,
    IngredientIncoming,
    RecipeIngredient,
    IceCreamProduction,
    StockItem,
    IceCreamStockTakeOut,
    Journal,
    EmployeeBadge,
    WorkingHours,
)
from .forms import RecipeForm, ProductionCalculatorForm, ClockInOutForm
from .decorators import (
    manager_required,
    service_required,
    production_required,
    register_activity,
)

# Create a modelformset for RecipeIngredients
RecipeIngredientFormSet = modelformset_factory(
    RecipeIngredient, fields=("ingredient", "quantity"), extra=5
)


@login_required
def welcome_page(request):
    # Get access level from user
    user_level = request.user.level

    # Dictionary with options depending on access level.
    options = {
        "Manager": {
            "Clock in/out": "scan_qr_code",
            "Staff Management": "staff_view",
            "Ice Cream Stock": "stock_view",
            "Journal": "view_journal",
            "Recipes": "recipe_list",
            "Production": "production_view",
            "Stock Takeout": "stock_takeout_view",
            "Ingredient Incoming": "add_ingredient",
            "Production Calculator": "production_calculator",
            "Ingredient Inventory": "ingredient_inventory",
        },
        "Service": {
            "Clock in/out": "scan_qr_code",
            "Profile": "view_profile",
            "Ice Cream Stock": "stock_view",
            "Recipes": "recipe_list",
            "Stock Takeout": "stock_takeout_view",
            "Ingredient Incoming": "add_ingredient",
            "Ingredient Inventory": "ingredient_inventory",
        },
        "Production": {
            "Clock in/out": "scan_qr_code",
            "Profile": "view_profile",
            "Ice Cream Stock": "stock_view",
            "Recipes": "recipe_list",
            "Production": "production_view",
            "Production Calculator": "production_calculator",
            "Ingredient Incoming": "add_ingredient",
            "Ingredient Inventory": "ingredient_inventory",
        },
    }

    # Get specific option according to access level. This will be used in the main welcome template.
    user_options = options.get(user_level, {})

    return render(
        request,
        "welcome.html",
        {"user_level": user_level, "user_options": user_options},
    )


@login_required
def view_profile(request, user_id):
    user = get_object_or_404(UserProfile, id=user_id)

    context = {
        "user": user,
    }

    return render(request, "view_profile.html", context)


@login_required
@register_activity(activity_edit_profile)
def edit_profile(request, user_id=None):
    if user_id is not None:
        # Editing another user's profile
        if not request.user.level == "Manager":
            # Only administrators can edit other users' profiles
            return HttpResponseForbidden("Forbidden")

        user = get_object_or_404(get_user_model(), id=user_id)
    else:
        # Editing  own profile
        user = request.user

    if request.method == "POST":
        if user == request.user:
            # If the user is editing their own profile
            form = CustomUserNormalForm(request.POST, instance=user)
        else:
            # If a Manager is editing another user's profile or its own.
            form = CustomUserForm(request.POST, instance=user)

        if form.is_valid():
            form.save()
            if request.user.level == "Manager":
                messages.success(request, "User updated successfully.")
                # If the user is an manager, redirect to 'staff_view'
                return redirect("staff_view")
            else:
                messages.success(request, "User updated successfully.")
                # If the user is a normal user, redirect to 'edit_profile'
                return redirect("profile_view")

    else:
        # Display the appropriate form based on the user's role
        form = (
            CustomUserForm(instance=user)
            if request.user.level == "Manager" or user == request.user
            else CustomUserNormalForm(instance=user)
        )

    return render(request, "edit_profile.html", {"form": form, "user": user})


@login_required
# @manager_required
@register_activity(activity_staff_view)
def staff_view(request):
    if request.user.level != "Manager":
        return HttpResponseForbidden("Forbidden")

    users = get_user_model().objects.all()
    user_form = None

    if request.method == "POST":
        if "add_user" in request.POST:
            user_form = CustomUserForm(request.POST)
            if user_form.is_valid():
                user = user_form.save(commit=False)
                password = request.POST.get("password")
                user.set_password(password)
                user.save()
                messages.success(request, "User added successfully.")
                return redirect("staff_view")
        elif "delete_user" in request.POST:
            user_id = request.POST.get("user_id")
            if user_id:
                user = get_user_model().objects.filter(id=user_id).first()
                if user:
                    deleted_username = user.username  # get name before deleting
                    user.delete()
                    # Register name and action in Journal. (must be registered directly in the view because the user name wont be in the DB anymore.)
                    Journal.objects.create(
                        user=request.user, action=f"User deleted: {deleted_username}"
                    )
                    messages.success(request, "User deleted successfully.")

    user_form = CustomUserForm()

    users = get_user_model().objects.all()
    print(users)

    return render(
        request,
        "staff_view.html",
        {"user_form": user_form, "users": users},
    )


@login_required
def stock_view(request):
    stock_items = StockItem.objects.all()
    return render(request, "stock_view.html", {"stock_items": stock_items})


def view_journal(request):
    # Get the filter parameter from the request
    filter_type = request.GET.get("filter", "all")

    # Set the filter range based on the filter parameter
    today = timezone.now()
    if filter_type == "today":
        start_date = today.date()
        end_date = today.date() + timezone.timedelta(days=1)
    elif filter_type == "this_week":
        start_date = today - timezone.timedelta(days=today.weekday())
        end_date = start_date + timezone.timedelta(days=7)
    elif filter_type == "this_month":
        start_date = today.replace(day=1)
        end_date = (today + timezone.timedelta(days=32)).replace(day=1)
    elif filter_type == "last_three_months":
        start_date = today.replace(day=1) - timezone.timedelta(days=90)
        end_date = today
    else:
        # Filter for all entries
        start_date = None
        end_date = None

    # Get the search terms from the request
    search_term = request.GET.get("search", "")
    search_terms = search_term.split()  # Split the search term into individual words

    # Create a list of Q objects for OR search on each word
    search_queries = [Q(action__icontains=word) for word in search_terms]

    # Combine the Q objects with the OR operator
    combined_query = search_queries.pop() if search_queries else Q()
    for query in search_queries:
        combined_query |= query

    # Query the journal based on the filter and combined search query
    journal = Journal.objects.filter(
        Q(timestamp__gte=start_date, timestamp__lt=end_date)
        if start_date is not None
        else Q(),
        combined_query,
    ).order_by("-timestamp")

    return render(
        request,
        "journal.html",
        {"journal": journal, "filter_type": filter_type, "search_term": search_term},
    )


# had to change auth decorator to use a class based view!
@method_decorator(login_required, name="dispatch")
class RecipeListView(ListView):
    model = Recipe
    template_name = "recipe_list.html"
    context_object_name = "recipes"

    # list if recipes
    def get_queryset(self):
        # include ingredients related to that recipe.
        return Recipe.objects.prefetch_related("ingredients")


# View for displaying recipe details
@login_required
# @manager_required
# @production_required
def recipe_detail(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    return render(request, "recipe_detail.html", {"recipe": recipe})


@login_required
# @manager_required
@register_activity
def create_recipe(request):
    if request.method == "POST":
        # Create a RecipeForm instance from the POST data
        form = RecipeForm(request.POST)
        # Create a RecipeIngredientFormSet instance from the POST data
        formset = RecipeIngredientFormSet(
            request.POST, queryset=RecipeIngredient.objects.none()
        )

        if form.is_valid() and formset.is_valid():
            # Save the recipe
            recipe = form.save()

            # Associate the recipe with ingredients and quantities
            instances = formset.save(commit=False)
            for instance in instances:
                instance.recipe = recipe
                instance.save()

            return redirect("recipe_detail", pk=recipe.pk)
    else:
        # Create a RecipeForm instance for rendering the recipe form
        form = RecipeForm()
        # Create a RecipeIngredientFormSet instance for rendering the ingredient formset
        formset = RecipeIngredientFormSet(queryset=RecipeIngredient.objects.none())

    # Render the recipe form and the ingredient formset
    return render(request, "create_recipe.html", {"form": form, "formset": formset})


# This view allows a manager to update an existing recipe.
@login_required
# @manager_required
# @register_activity
def update_recipe(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    if request.method == "POST":
        form = RecipeForm(request.POST, instance=recipe)

        if form.is_valid():
            recipe = form.save()

            # Check if a new ingredient is being added to the recipe
            new_ingredient_name = form.cleaned_data.get("new_ingredient_name")
            new_ingredient_quantity = form.cleaned_data.get("new_ingredient_quantity")

            if new_ingredient_name and new_ingredient_quantity:
                # Create a new ingredient if it doesn't exist
                new_ingredient, created = Ingredient.objects.get_or_create(
                    name=new_ingredient_name,
                    defaults={"unit_of_measurement": Ingredient.GRAMS},
                )

                # Add the new ingredient to the recipe
                RecipeIngredient.objects.create(
                    recipe=form.instance,
                    ingredient=new_ingredient,
                    quantity=new_ingredient_quantity,
                )

            return redirect("recipe_detail", pk=recipe.pk)
    else:
        # Create a form to render the recipe form with the existing data
        form = RecipeForm(instance=recipe)
    return render(request, "update_recipe.html", {"form": form})


@login_required
# @manager_required
# @register_activity
def delete_recipe(request, pk):
    try:
        recipe = Recipe.objects.get(pk=pk)
    except Recipe.DoesNotExist:
        raise Http404("Recipe does not exist")

    if request.method == "POST":
        recipe.delete()
        return redirect("recipe_list")

    return render(request, "delete_recipe.html", {"recipe": recipe})


@login_required
# @manager_required
# @register_activity
def create_recipe(request):
    if request.method == "POST":
        form = RecipeForm(request.POST)

        if form.is_valid():
            recipe = form.save()

            # Check if a new ingredient is being added to the recipe
            new_ingredient_name = form.cleaned_data.get("new_ingredient_name")
            new_ingredient_quantity = form.cleaned_data.get("new_ingredient_quantity")

            if new_ingredient_name and new_ingredient_quantity:
                # Create a new ingredient if it doesn't exist
                new_ingredient, created = Ingredient.objects.get_or_create(
                    name=new_ingredient_name,
                    defaults={"unit_of_measurement": Ingredient.GRAMS},
                )

                # Add the new ingredient to the recipe
                RecipeIngredient.objects.create(
                    recipe=form.instance,
                    ingredient=new_ingredient,
                    quantity=new_ingredient_quantity,
                )

            return redirect("recipe_detail", pk=recipe.pk)
    else:
        # Create a form to render the recipe form
        form = RecipeForm()

    return render(request, "create_recipe.html", {"form": form})


@login_required
# @manager_required
# @production_required
# @register_activity
def production_view(request):
    if request.method == "POST":
        recipe_id = request.POST["recipe"]
        quantity_produced = request.POST["quantity_produced"]
        container_size = request.POST["container_size"]
        produced_by = request.user
        recipe = Recipe.objects.get(pk=recipe_id)
        recipe_ingredients = RecipeIngredient.objects.filter(recipe=recipe)

        try:
            # Check ingredient availability in inventory, and catch any ValidationErrors
            check_ingredient_availability(
                recipe_ingredients, quantity_produced, container_size
            )

            # Create production
            production = create_production(
                recipe,
                container_size,
                recipe_ingredients,
                quantity_produced,
                produced_by,
            )

            # Check if the recipe is marked as a base
            if recipe.is_base:
                # add base to inventory
                add_base_to_inventory(recipe, quantity_produced)
            else:
                # add ice cream to Stock
                update_stock(recipe, production, produced_by)
        except ValidationError as e:
            messages.error(request, e)
            return redirect("production_view")

    return redirect("production_view")


@login_required
# @manager_required
# @production_required
def check_ingredient_availability(
    recipe_ingredients, quantity_produced, container_size
):
    for recipe_ingredient in recipe_ingredients:
        required_quantity = (
            float(recipe_ingredient.quantity) * quantity_produced * container_size
        )
        inventory = recipe_ingredient.ingredient.inventory

        if inventory.quantity < required_quantity:
            raise ValidationError(
                f"Ingredient {recipe_ingredient.ingredient.name} is not available in sufficient quantity."
            )


@login_required
# @manager_required
# @production_required
# @register_activity
def create_production(
    recipe, container_size, recipe_ingredients, quantity_produced, produced_by
):
    # Check if the recipe is marked as a base
    if recipe.is_base:
        # For base recipes, we treat them as a single ingredient
        # Calculate the total quantity required based on quantity produced
        total_quantity_required = quantity_produced

        # Create production
        production = IceCreamProduction.objects.create(
            recipe=recipe, quantity_produced=quantity_produced, produced_by=produced_by
        )

        # Update inventory for the base (recipe itself)
        base_ingredient, created = Ingredient.objects.get_or_create(
            name=recipe.flavor, defaults={"unit_of_measurement": Ingredient.GRAMS}
        )

        base_ingredient.inventory.quantity += total_quantity_required
        base_ingredient.inventory.save()
    else:
        # If it's not a base, then we consider the container size
        # Obtain the quantity factor based on the selected container size
        if container_size == 0.5:
            quantity_factor = 0.5
        elif container_size == 3:
            quantity_factor = 3
        elif container_size == 6:
            quantity_factor = 6
        else:
            raise ValueError("Invalid container size selected")

        # Calculate the total quantity required based on quantity factor and quantity produced
        total_quantity_required = quantity_factor * quantity_produced

        # Create production
        IceCreamProduction.objects.create(
            recipe=recipe,
            container_size=container_size,
            quantity_produced=quantity_produced,
            produced_by=produced_by,
        )

    # Update ingredient inventory
    for recipe_ingredient in recipe_ingredients:
        required_quantity = float(recipe_ingredient.quantity) * total_quantity_required
        inventory = recipe_ingredient.ingredient.inventory
        inventory.quantity -= required_quantity
        inventory.save()


def add_base_to_inventory(recipe, quantity_produced):
    # Create the base ingredient
    base_ingredient, created = Ingredient.objects.get_or_create(
        name=recipe.flavor, defaults={"unit_of_measurement": Ingredient.GRAMS}
    )

    # Update inventory for the base
    base_ingredient.inventory.quantity += float(quantity_produced)
    base_ingredient.inventory.save()

    # Update the inventory for the ingredients used to produce the base
    for ingredient in recipe.base_ingredients.all():
        required_quantity = float(
            ingredient.recipeingredient_set.get(recipe=recipe).quantity
        ) * float(quantity_produced)
        inventory_entry = IngredientInventory.objects.get(ingredient_name=ingredient)
        inventory_entry.quantity -= required_quantity
        inventory_entry.save()


@receiver(post_save, sender=IceCreamProduction)
def update_stock(sender, instance, created, **kwargs):
    if created:
        # Update ice cream stock
        stock_item, created = StockItem.objects.get_or_create(
            recipe=instance.recipe, size=instance.container_size
        )
        stock_item.quantity += instance.quantity_produced
        stock_item.added_by = instance.produced_by
        stock_item.save()


@login_required
# @manager_required
# @service_required
# @register_activity
def stock_takeout_view(request):
    if request.method == "POST":
        stock_item_id = request.POST["stock_item"]
        quantity_moved = request.POST["quantity_moved"]
        date_moved = request.POST["date_moved"]
        moved_by = request.user

        # Validation: Check if there is enough ice cream in stock
        stock_item = StockItem.objects.get(pk=stock_item_id)

        if float(quantity_moved) <= 0:
            raise ValidationError("Must be positive number")

        if stock_item.quantity < float(quantity_moved):
            raise ValidationError("Not enough in Stock")

        # Register the stock movement
        IceCreamStockTakeOut.objects.create(
            ice_cream_production=stock_item,
            quantity_moved=quantity_moved,
            date_moved=date_moved,
            moved_by=moved_by,
        )

        return redirect("stock_takeout_view")


@login_required
# @register_activity
def add_ingredient(request):
    if request.method == "POST":
        ingredient_name = request.POST["ingredient_name"]
        quantity = float(request.POST["quantity"])  # Convert the quantity to a float
        unit_weight = request.POST["unit_weight"]
        lot_number = request.POST.get("lot_number", None)
        expiration_date = request.POST.get("expiration_date", None)
        temperature = request.POST.get("temperature", None)
        observations = request.POST.get("observations", None)

        received_by = request.user  # User receiving

        try:
            ingredient = Ingredient.objects.get(name=ingredient_name)
        except Ingredient.DoesNotExist:
            messages.error(request, "Ingredients doesnt exist")
            return redirect("add_ingredient")

        if quantity <= 0:
            raise ValidationError("quantity must be a positive number.")

        # Call a function to add the ingredient to inventory
        if ingredient.is_base:
            add_base_to_inventory(ingredient, quantity)
        else:
            add_to_inventory(ingredient, quantity)

        # Register the ingredient incoming
        register_ingredient_incoming(
            ingredient,
            quantity,
            lot_number,
            unit_weight,
            expiration_date,
            temperature,
            observations,
            received_by,
        )

        messages.success(request, "Ingredient register succesfully.")
        return redirect("ingredient_inventory")


def add_to_inventory(ingredient, quantity):
    # Get or create the inventory entry
    inventory_entry, created = IngredientInventory.objects.get_or_create(
        ingredient_name=ingredient
    )

    # Update the existing quantity with the new quantity if not there than creates it.
    if not created:
        inventory_entry.quantity += quantity
        inventory_entry.save()


def register_ingredient_incoming(
    ingredient,
    quantity,
    lot_number,
    unit_weight,
    expiration_date,
    temperature,
    observations,
    received_by,
):
    # Register for IngredientIncoming
    IngredientIncoming.objects.create(
        ingredient=ingredient,
        quantity=quantity,
        lot_number=lot_number,
        unit_weight=unit_weight,
        expiration_date=expiration_date,
        temperature=temperature,
        observations=observations,
        received_by=received_by,
    )


@login_required
def ingredient_inventory_view(request):
    ingredients_inventory = IngredientInventory.objects.all()
    if request.user.level == "Manager":  # only manager can make changes.
        if request.method == "POST":
            # do manual changes en inventory
            form = IngredientInventoryUpdateForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Changes done successfully.")

    # if there are mistakes in the formulary
    else:
        form = IngredientInventoryUpdateForm()

    return render(
        request,
        "ingredient_inventory.html",
        {"ingredients_inventory": ingredients_inventory, "form": form},
    )


@login_required
# @manager_required
# @production_required
def production_calculator_view(request):
    if request.method == "POST":
        form = ProductionCalculatorForm(request.POST)
        if form.is_valid():
            recipes = form.cleaned_data["recipes"]
            desired_quantities = form.cleaned_data["desired_quantities"]

            # Parse desired quantities and recipes
            desired_quantities = [
                float(q.strip()) for q in desired_quantities.split(",")
            ]

            # Dictionary to store ingredient quantities
            total_ingredient_quantities = {}

            try:
                # Calculate and check availability for each recipe
                for recipe, desired_quantity in zip(recipes, desired_quantities):
                    calculate_production(
                        recipe, desired_quantity, total_ingredient_quantities
                    )
            except ValidationError as e:
                form.add_error(None, e)
            else:
                # Total quantities calculation is successful
                print("Calculations done correctly")
                print(total_ingredient_quantities)

    else:
        form = ProductionCalculatorForm()

    return render(request, "production_calculator.html", {"form": form})


def calculate_production(recipe, desired_quantity, total_ingredient_quantities):
    recipe_ingredients = RecipeIngredient.objects.filter(recipe=recipe)

    for recipe_ingredient in recipe_ingredients:
        # Get the ingredient and its quantity in the recipe
        ingredient = recipe_ingredient.ingredient
        quantity_in_recipe = float(recipe_ingredient.quantity)  # Quantity per kg

        # Calculate the total quantity needed based on the desired quantity
        total_quantity_needed = quantity_in_recipe * desired_quantity

        # Update or initialize the total_ingredient_quantities dictionary
        if ingredient.id in total_ingredient_quantities:
            total_ingredient_quantities[ingredient.id] += total_quantity_needed
        else:
            total_ingredient_quantities[ingredient.id] = total_quantity_needed

        # Check ingredient availability in inventory
        check_inventory_availability(ingredient, total_quantity_needed)

        # Check if the recipe's base ingredients need to be added
        if recipe.is_base:
            add_base_ingredients(recipe, desired_quantity, total_ingredient_quantities)


# Function to check if base ingredients need to be added
def add_base_ingredients(recipe, desired_quantity, total_ingredient_quantities):
    for base_ingredient in recipe.base_ingredients.all():
        # Get the base ingredient's quantity in the recipe
        recipe_ingredient = base_ingredient.recipeingredient_set.get(recipe=recipe)
        quantity_in_recipe = float(recipe_ingredient.quantity)  # Quantity per kg

        # Calculate the total quantity needed based on the desired quantity
        total_quantity_needed = quantity_in_recipe * desired_quantity

        # Update or initialize the total_ingredient_quantities dictionary for base ingredients
        if base_ingredient.id in total_ingredient_quantities:
            total_ingredient_quantities[base_ingredient.id] += total_quantity_needed
        else:
            total_ingredient_quantities[base_ingredient.id] = total_quantity_needed

        # Check ingredient availability in inventory
        check_inventory_availability(base_ingredient, total_quantity_needed)


# Function to verify inventory availability
def check_inventory_availability(ingredient, total_quantity_needed):
    inventory = ingredient.inventory

    if inventory.quantity < total_quantity_needed:
        raise ValidationError(
            f"Ingredient {ingredient.name} is not available in sufficient quantity. Current quantity: {inventory.quantity} kg, Required quantity: {total_quantity_needed} kg"
        )


# simple logout, it redirects you to login site.
def custom_logout(request):
    logout(request)
    return redirect("/")


# combined version
def scan_qr_code(request):
    if request.method == "POST":
        form = ClockInOutForm(request.POST)

        if form.is_valid():
            cap = cv2.VideoCapture(0)

            while True:
                ret, frame = cap.read()
                decoded_objects = decode(frame)

                for obj in decoded_objects:
                    data = obj.data.decode("utf-8")

                    try:
                        staff_member = UserProfile.objects.get(id=data)
                        cv2.destroyAllWindows()

                        # Check if the staff member is already clocked in
                        try:
                            last_clock_in = WorkingHours.objects.filter(
                                employee=staff_member, clock_out__isnull=True
                            ).latest("clock_in")
                            last_clock_in.clock_out = datetime.now()
                            last_clock_in.save()
                            clock_out_formatted = last_clock_in.clock_out.strftime(
                                "%Y-%m-%d %H:%M"
                            )
                            messages.success(
                                request,
                                f"{staff_member.username} - Clocked Out at {clock_out_formatted}",
                            )
                            return redirect("welcome")

                        except WorkingHours.DoesNotExist:
                            # Clock staff member in
                            working_hours = WorkingHours(
                                employee=staff_member, clock_in=datetime.now()
                            )
                            working_hours.save()
                            clock_in_formatted = working_hours.clock_in.strftime(
                                "%Y-%m-%d %H:%M"
                            )
                            messages.success(
                                request,
                                f"{staff_member.username} - Clocked In at {clock_in_formatted}",
                            )
                            return redirect("welcome")

                    except UserProfile.DoesNotExist:
                        cap.release()
                        cv2.destroyAllWindows()
                        return redirect("welcome")

                cv2.imshow("QR Code Scanner    Press q to exit", frame)

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

            cap.release()
            cv2.destroyAllWindows()
            return redirect("welcome")
        else:
            return redirect("welcome")
    else:
        form = ClockInOutForm()

    return render(request, "welcome.html", {"form": form})


def staff_member_list(request):
    staff_members = UserProfile.objects.all()
    data = [{"name": staff.username, "email": staff.email} for staff in staff_members]
    return JsonResponse(data, safe=False)


def generate_employee_badge(request):
    employees = UserProfile.objects.all()

    if request.method == "POST":
        employee_id = request.POST.get("employee_id")
        selected_employee = UserProfile.objects.get(id=employee_id)

        # Generate the badge for the selected employee
        badge = EmployeeBadge(
            employee_name=selected_employee.username, employee_id=selected_employee.id
        )
        file_name = badge.generate_badge()

        if file_name:
            with open(file_name, "rb") as badge_file:
                response = HttpResponse(
                    badge_file.read(), content_type="application/pdf"
                )
                response[
                    "Content-Disposition"
                ] = f'attachment; filename="{file_name.replace("api/badges/", "")}"'
                os.remove(file_name)
                return response
        else:
            return HttpResponse("Badge not generated.")

    return render(request, "api/employee_list.html", {"employees": employees})


def working_hours_list(request, staff_member_id):
    working_hours = WorkingHours.objects.filter(employee_id=staff_member_id)
    data = [
        {
            "clock_in": wh.clock_in,
            "clock_out": wh.clock_out,
            "recorded_time": wh.recorded_time(),
        }
        for wh in working_hours
    ]
    return JsonResponse(data, safe=False)
