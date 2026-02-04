with open(r'templates\products\product_form.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Print current problematic line
lines = content.split('\n')
for i, line in enumerate(lines, 1):
    if 'category_id==cat.id' in line or 'packaging_id==pkg.id' in line:
        print(f"Linha {i}: {line[:100]}")

# Replace ALL instances
replacements = [
    ('product.category_id==cat.id', 'product.category_id == cat.id'),
    ('product.packaging_id==pkg.id', 'product.packaging_id == pkg.id'),
    ('product.unit_fk_id==u.id', 'product.unit_fk_id == u.id'),
    ('product.unit==u.abbreviation', 'product.unit == u.abbreviation'),
    ("product.status=='active'", "product.status == 'active'"),
    ("product.status=='inactive'", "product.status == 'inactive'"),
]

for old, new in replacements:
    if old in content:
        content = content.replace(old, new)
        print(f"✅ Substituído: {old} → {new}")

with open(r'templates\products\product_form.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("\n✅ Arquivo salvo!")

# Verify
with open(r'templates\products\product_form.html', 'r', encoding='utf-8') as f:
    verify = f.read()
    if 'category_id==cat.id' in verify:
        print("❌ ERRO: category_id==cat.id ainda presente!")
    else:
        print("✅ VERIFICADO: category_id corrigido")
