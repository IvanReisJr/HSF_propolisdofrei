with open(r'templates\products\product_form.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Direct fix for line 51 (index 50)
for i, line in enumerate(lines):
    if 'product.category_id==cat.id' in line:
        lines[i] = line.replace('product.category_id==cat.id', 'product.category_id == cat.id')
        print(f"✅ Linha {i+1} corrigida: category_id")
    if 'product.packaging_id==pkg.id' in line:
        lines[i] = line.replace('product.packaging_id==pkg.id', 'product.packaging_id == pkg.id')
        print(f"✅ Linha {i+1} corrigida: packaging_id")
    if 'product.unit_fk_id==u.id' in line:
        lines[i] = line.replace('product.unit_fk_id==u.id', 'product.unit_fk_id == u.id')
        print(f"✅ Linha {i+1} corrigida: unit_fk_id")
    if 'product.unit==u.abbreviation' in line:
        lines[i] = line.replace('product.unit==u.abbreviation', 'product.unit == u.abbreviation')
        print(f"✅ Linha {i+1} corrigida: unit")
    if "product.status=='active'" in line:
        lines[i] = line.replace("product.status=='active'", "product.status == 'active'")
        print(f"✅ Linha {i+1} corrigida: status active")
    if "product.status=='inactive'" in line:
        lines[i] = line.replace("product.status=='inactive'", "product.status == 'inactive'")
        print(f"✅ Linha {i+1} corrigida: status inactive")

with open(r'templates\products\product_form.html', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("\n🎉 Todas as correções aplicadas!")
