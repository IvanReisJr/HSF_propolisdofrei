import re

# Fix product_form.html
with open(r'templates\products\product_form.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix category_id==cat.id
content = content.replace('product.category_id==cat.id', 'product.category_id == cat.id')

with open(r'templates\products\product_form.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ product_form.html fixed")

# Fix packaging_form.html
with open(r'templates\products\packaging_form.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Fix line 19-20: broken h1 tag
for i in range(len(lines)):
    if i == 18:  # Line 19 (0-indexed)
        lines[i] = '        <h1 style="font-size: 1.875rem; font-weight: 700;">{% if is_edit %}Editar Embalagem{% else %}Nova Embalagem{% endif %}</h1>\r\n'
        if i+1 < len(lines) and 'endif' in lines[i+1]:
            lines[i+1] = ''  # Remove the broken continuation
    elif i == 32:  # Line 33 (0-indexed)
        lines[i] = '            <input type="checkbox" name="is_active" id="is_active" {% if not is_edit or packaging.is_active %}checked{% endif %}>\r\n'
        if i+1 < len(lines) and 'endif' in lines[i+1]:
            lines[i+1] = ''

with open(r'templates\products\packaging_form.html', 'w', encoding='utf-8') as f:
    f.writelines([line for line in lines if line.strip()])  # Remove empty lines

print("✅ packaging_form.html fixed")
print("\n🎉 Todos os templates corrigidos!")
