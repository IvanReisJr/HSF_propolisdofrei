import re

# Fix ALL remaining == without spaces in product_form.html
with open(r'templates\products\product_form.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix all == patterns
content = content.replace('product.packaging_id==pkg.id', 'product.packaging_id == pkg.id')
content = content.replace('product.status==', 'product.status == ')

# Also check for any other == patterns we might have missed
content = re.sub(r'(\w+)==(\w+)', r'\1 == \2', content)
content = re.sub(r"(\w+)=='(\w+)'", r"\1 == '\2'", content)

with open(r'templates\products\product_form.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Todos os == corrigidos em product_form.html")
