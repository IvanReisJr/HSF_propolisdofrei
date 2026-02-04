import os

file_path = r'templates\products\product_list.html'

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find and fix the broken line (around line 41-42)
    for i in range(len(lines)):
        if 'selected_category == category.id|stringformat:"s"' in lines[i]:
            # This line should be: <option value="{{ category.id }}" {% if selected_category == category.id|stringformat:"s" %}selected{% endif %}>{{ category.name }}</option>
            lines[i] = '                <option value="{{ category.id }}" {% if selected_category == category.id|stringformat:"s" %}selected{% endif %}>{{ category.name }}</option>\r\n'
            # Remove the next line if it's just the endif part
            if i+1 < len(lines) and 'endif' in lines[i+1] and '<option' not in lines[i+1]:
                lines[i+1] = ''
            break
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print("✓ Template fixed!")
    
except Exception as e:
    print(f"Error: {e}")
