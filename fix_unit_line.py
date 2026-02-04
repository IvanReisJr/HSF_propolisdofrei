import re

# Fix product_form.html - line 61-62
with open(r'templates\products\product_form.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the broken unit selection line
old_pattern = r'{% if product\.unit_fk_id==u\.id or product\.unit==u\.abbreviation\s+%}selected{% endif %}'
new_pattern = '{% if product.unit_fk_id == u.id or product.unit == u.abbreviation %}selected{% endif %}'
content = re.sub(old_pattern, new_pattern, content)

# Also fix direct string matches
content = content.replace(
    '{% if product.unit_fk_id==u.id or product.unit==u.abbreviation\n                        %}selected{% endif %}',
    '{% if product.unit_fk_id == u.id or product.unit == u.abbreviation %}selected{% endif %}'
)

# Simpler approach - just replace the problematic parts
content = content.replace('product.unit_fk_id==u.id', 'product.unit_fk_id == u.id')
content = content.replace('product.unit==u.abbreviation', 'product.unit == u.abbreviation')

with open(r'templates\products\product_form.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ product_form.html - linha 61-62 corrigida")
