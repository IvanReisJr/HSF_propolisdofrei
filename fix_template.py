import os

file_path = r'templates\products\product_list.html'

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix the syntax error
    content = content.replace(
        'selected_category==category.id|stringformat:"s"',
        'selected_category == category.id|stringformat:"s"'
    )
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✓ File fixed successfully!")
    
    # Verify the fix
    with open(file_path, 'r', encoding='utf-8') as f:
        if 'selected_category ==' in f.read():
            print("✓ Verification passed - spaces added")
        else:
            print("✗ Verification failed")
            
except Exception as e:
    print(f"Error: {e}")
