import re

file_path = r'templates\products\product_list.html'

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix all == without spaces in template tags
    content = re.sub(r"selected_status=='all'", "selected_status == 'all'", content)
    content = re.sub(r"selected_status=='active'", "selected_status == 'active'", content)
    content = re.sub(r"selected_status=='inactive'", "selected_status == 'inactive'", content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✓ All template syntax fixed!")
    
except Exception as e:
    print(f"Error: {e}")
