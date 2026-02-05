
import os
import django
from django.conf import settings
from django.test import RequestFactory, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def debug_product_create_crash():
    print("--- Debugging Product Create View Crash ---")
    
    User = get_user_model()
    user = User.objects.first()
    print(f"User: {user}")
    
    client = Client(HTTP_HOST='127.0.0.1')
    client.force_login(user)
    
    try:
        url = '/products/new/'
        # Try to reverse if possible, but hardcode fallback
        try:
             url = reverse('product_create')
             print(f"Resolved URL: {url}")
        except:
             pass

        response = client.get(url)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print("✘ Error detected!")
            # If server error, printed response might not help if it's standard django error page, 
            # but usually it dumps traceback in console if debug is True, or content has error.
            print(response.content.decode('utf-8')[:1000]) # First 1000 chars
        else:
            print("✔ View returned 200 OK.")
            # Verify if content actually contains the form and expected debug category stuff
            content = response.content.decode('utf-8')
            if 'Nenhuma categoria encontrada no sistema' in content:
                print("✔ Debug fallback string found.")
            if 'categories.count' in content or 'disponíveis' in content:
                print("✔ Category count debug found.")
            
    except Exception as e:
        print(f"✘ CRITICAL EXCEPTION: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_product_create_crash()
