from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import IceCreamProduction, StockItem


"""@receiver(post_save, sender=IngredientIncoming)
def update_inventory(sender, instance, created, **kwargs):
    if created:
        # Update or create the inventory entry for the received ingredient
        IngredientInventory.update_or_create_inventory(
            instance.ingredient, instance.quantity
        )"""


@receiver(post_save, sender=IceCreamProduction)
def update_stock_on_production(sender, instance, created, **kwargs):
    if created:
        stock_item, created = StockItem.objects.get_or_create(
            recipe=instance.recipe, size=instance.container_size
        )
        stock_item.quantity += instance.quantity_produced
        stock_item.added_by = instance.produced_by
        stock_item.save()
