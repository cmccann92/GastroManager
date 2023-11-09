from django import forms
from .models import Recipe, Ingredient, UserProfile, IngredientInventory, Address
from django.core.exceptions import ValidationError


class RecipeForm(forms.ModelForm):
    class Meta:
        model = Recipe
        fields = ["flavor", "ingredients", "base_ingredients"]

    ingredients = forms.ModelMultipleChoiceField(
        queryset=Ingredient.objects.all(),
        widget=forms.CheckboxSelectMultiple,
    )

    base_ingredients = forms.ModelMultipleChoiceField(
        queryset=Ingredient.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    ingredient_quantities = forms.DecimalField(
        label="Ingredient Quantities (grams or units)",
        widget=forms.TextInput(
            attrs={"placeholder": "Enter quantities for selected ingredients"}
        ),
        required=False,
    )

    new_ingredient_name = forms.CharField(
        max_length=255,
        label="New Ingredient Name",
        required=False,
    )

    new_ingredient_quantity = forms.DecimalField(
        label="New Ingredient Quantity",
        required=False,
    )


class ProductionCalculatorForm(forms.Form):
    recipes = forms.ModelMultipleChoiceField(
        queryset=Recipe.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label="Select Recipes for Production",
    )
    desired_quantities = forms.CharField(
        label="Desired Quantities (kg)",
        help_text="Enter the desired quantities for the selected recipes, separated by commas",
    )


class CustomUserForm(forms.ModelForm):
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput,
        required=True,
        help_text="Enter password, can be anything.",
    )

    # Define the Address fields within the CustomUserForm
    line_1 = forms.CharField(max_length=255, label="Address Line 1")
    line_2 = forms.CharField(max_length=255, label="Address Line 2", required=False)
    city = forms.CharField(max_length=100)
    state = forms.CharField(max_length=100, required=False)
    postal_code = forms.CharField(max_length=20, label="Postal Code")
    country = forms.CharField(max_length=100)

    class Meta:
        model = UserProfile
        fields = (
            "username",
            "password",
            "first_name",
            "last_name",
            "email",
            "date_of_birth",
            "phone",
            "level",
            "is_active",
            "is_staff",
            "is_superuser",
        )

    def save(self, commit=True):
        # Save User data
        user = super().save(commit=False)

        # Save the Address data
        address = Address(
            line_1=self.cleaned_data.get("line_1"),
            line_2=self.cleaned_data.get("line_2"),
            city=self.cleaned_data.get("city"),
            state=self.cleaned_data.get("state"),
            postal_code=self.cleaned_data.get("postal_code"),
            country=self.cleaned_data.get("country"),
        )
        address.save()

        # Assign the address to the user
        user.address = address

        if commit:
            user.save()

        return user


class CustomUserNormalForm(forms.ModelForm):  # for all users
    # Address defined directly in CustomUserForm.
    line_1 = forms.CharField(max_length=255, label="Address Line 1")
    line_2 = forms.CharField(max_length=255, label="Address Line 2", required=False)
    city = forms.CharField(max_length=100)
    state = forms.CharField(max_length=100, required=False)
    postal_code = forms.CharField(max_length=20, label="Postal Code")
    country = forms.CharField(max_length=100)

    class Meta:
        model = UserProfile
        fields = (
            "first_name",
            "last_name",
            "email",
            "date_of_birth",
            "line_1",
            "line_2",
            "city",
            "state",
            "postal_code",
            "country",
            "phone",
        )

    def save(self, commit=True):
        # Save an "Address Form" in an instance of Address
        address = Address(
            line_1=self.cleaned_data.get("line_1"),
            line_2=self.cleaned_data.get("line_2"),
            city=self.cleaned_data.get("city"),
            state=self.cleaned_data.get("state"),
            postal_code=self.cleaned_data.get("postal_code"),
            country=self.cleaned_data.get("country"),
        )
        address.save()

        # Save User and assign new Address
        user = super().save(commit=False)
        user.address = address

        if commit:
            user.save()

        return user


# Ingredient Inventory Update Form
class IngredientInventoryUpdateForm(forms.ModelForm):
    class Meta:
        model = IngredientInventory
        fields = ("quantity",)

    def clean_quantity(self):
        quantity = self.cleaned_data.get("quantity")
        if quantity < 0:
            raise ValidationError("Quantity must be a positive number.")
        return quantity


class ClockInOutForm(forms.Form):
    clock_in = forms.BooleanField(widget=forms.HiddenInput, required=False)
    clock_out = forms.BooleanField(widget=forms.HiddenInput, required=False)
