from decimal import Decimal

from django.core.management.base import BaseCommand

from store.models import Category, Product


class Command(BaseCommand):
    help = "Create a small, repeatable Northstar catalogue for local demonstrations."

    def handle(self, *args, **options):
        samples = {
            "Home objects": [
                ("Sculpted ceramic vase", "A hand-finished stoneware vessel with a quietly expressive silhouette.", "840.00", "https://images.unsplash.com/photo-1578500494198-246f612d3b3d?auto=format&fit=crop&w=900&q=80"),
                ("Oak catchall tray", "Solid oak keeps everyday essentials close and beautifully gathered.", "620.00", "https://images.unsplash.com/photo-1603006905003-be475563bc59?auto=format&fit=crop&w=900&q=80"),
                ("Linen table runner", "Washed natural linen with a relaxed texture for daily meals.", "1100.00", "https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?auto=format&fit=crop&w=900&q=80"),
            ],
            "Lighting": [
                ("Portable glow lamp", "A compact rechargeable lamp for a warm pool of light wherever you need it.", "2150.00", "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?auto=format&fit=crop&w=900&q=80"),
                ("Pleated bedside light", "Softly diffused light under a sculptural pleated shade.", "1780.00", "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?auto=format&fit=crop&w=900&q=80"),
            ],
            "Everyday carry": [
                ("Canvas market tote", "A sturdy, easy-carry tote cut from heavyweight cotton canvas.", "480.00", "https://images.unsplash.com/photo-1590874103328-eac38a683ce7?auto=format&fit=crop&w=900&q=80"),
                ("Pocket notebook set", "Three thread-bound notebooks for lists, sketches, and passing thoughts.", "260.00", "https://images.unsplash.com/photo-1544816155-12df9643f363?auto=format&fit=crop&w=900&q=80"),
            ],
        }
        count = 0
        for category_name, products in samples.items():
            category, _ = Category.objects.get_or_create(name=category_name, defaults={"description": f"Considered {category_name.lower()} for everyday living."})
            for name, description, price, image in products:
                _, created = Product.objects.get_or_create(name=name, defaults={
                    "category": category, "description": description, "price": Decimal(price),
                    "stock_quantity": 12, "image_url": image, "active": True,
                })
                count += int(created)
        self.stdout.write(self.style.SUCCESS(f"Demo catalogue ready; {count} new products created."))
