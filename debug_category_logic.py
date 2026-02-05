from apps.categories.models import Category
import uuid

try:
    print("Testing Category Creation...")
    name = f"Test Category {uuid.uuid4()}"
    cat = Category.objects.create(name=name, description="Test Desc", is_active=True)
    print(f"Created category: {cat.name}, active: {cat.is_active}")

    print("Testing Category Edit...")
    cat.is_active = False
    cat.save()
    cat.refresh_from_db()
    print(f"Edited category: {cat.name}, active: {cat.is_active}")
    
    cat.delete()
    print("Test Complete.")
except Exception as e:
    print(f"ERROR: {e}")
