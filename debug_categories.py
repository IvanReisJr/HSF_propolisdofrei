
import os
import django
from django.conf import settings
from django.test import RequestFactory
from django.contrib.auth import get_user_model

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.categories.models import Category
from apps.products.views import product_create

def debug_categories():
    print("--- Debugging Categories ---")
    
    # 1. Check Database
    count = Category.objects.count()
    print(f"Total Categories in DB: {count}")
    
    if count > 0:
        print("Categories found:")
        for cat in Category.objects.all()[:5]:
            print(f" - ID: {cat.id}, Name: {cat.name}")
    else:
        print("⚠ NO CATEGORIES FOUND IN DATABASE!")
        print("   This explains why the dropdown is empty.")
        return

    # 2. Check View Context if DB has data
    print("\n--- Checking View Context ---")
    User = get_user_model()
    user = User.objects.first()
    factory = RequestFactory()
    request = factory.get('/products/new/')
    request.user = user
    request.session = {} 
    request._messages = [] # Mock messages
    
    try:
        response = product_create(request)
        if response.status_code == 200:
            # Inspect context data from response if possible (render returns HttpResponse)
            # Since we can't easily access context of a rendered response object without middleware tricks,
            # we rely on the code review we did earlier or just trust the DB check.
            # However, we can check if the response content contains the category names.
            content = response.content.decode('utf-8')
            found_any = False
            for cat in Category.objects.all()[:3]:
                if cat.name in content:
                    print(f"✔ Found category '{cat.name}' in rendered HTML.")
                    found_any = True
                else:
                    print(f"✘ Could NOT find category '{cat.name}' in rendered HTML.")
            
            if not found_any:
                print("⚠ View executed but categories are not in the HTML output.")
        else:
             print(f"✘ View returned status {response.status_code}")

    except Exception as e:
        print(f"✘ Error running view: {e}")

if __name__ == "__main__":
    debug_categories()
