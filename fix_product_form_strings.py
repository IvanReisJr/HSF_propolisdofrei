
import os

file_path = os.path.join('templates', 'products', 'product_form.html')

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replacements
replacements = [
    ('product.category_id==cat.id', 'product.category_id == cat.id'),
    ('product.unit_fk_id==u.id', 'product.unit_fk_id == u.id'),
    ('product.unit==u.abbreviation', 'product.unit == u.abbreviation'),
    ('product.distributor_id==dist.id', 'product.distributor_id == dist.id'),
    ('product.packaging_id==pkg.id', 'product.packaging_id == pkg.id'),
    ("product.status=='active'", "product.status == 'active'"),
    ("product.status=='inactive'", "product.status == 'inactive'"),
    # Fix multi-line tag for unit
    ('{% if product.unit_fk_id==u.id or product.unit==u.abbreviation\n                        %}selected{% endif %}', 
     '{% if product.unit_fk_id == u.id or product.unit == u.abbreviation %}selected{% endif %}')
]

new_content = content
# First apply the multi-line fix first to ensure it matches before other sub-replacements (though specific enough)
# Actually, the string replace above targets the exact multi-line mess.
# But wait, did I already run the script and partially fix the spaces?
# If I ran it in Step 594, maybe some spaces are already fixed?
# I should check if the file content already has ' == ' in some places.
# To be safe, I will try to match BOTH versions (with and without fixed spaces) or partial matches.

# Let's try to match the "split" pattern regardless of spacing if possible, or just exact known state.
# I just ran the script, so 'product.unit_fk_id==u.id' became 'product.unit_fk_id == u.id'.
# So the file likely has:
# {% if product.unit_fk_id == u.id or product.unit == u.abbreviation
#                        %}selected{% endif %}
# So I should target THAT.

replacements = [
    ('product.category_id==cat.id', 'product.category_id == cat.id'), # Re-run safe
    # ... others ...
    # The Unit Tag Joiner - assuming previous script ran:
    ('{% if product.unit_fk_id == u.id or product.unit == u.abbreviation\n                        %}selected{% endif %}', 
     '{% if product.unit_fk_id == u.id or product.unit == u.abbreviation %}selected{% endif %}'),
    # Fallback if previous script didn't run or missed:
    ('{% if product.unit_fk_id==u.id or product.unit==u.abbreviation\n                        %}selected{% endif %}', 
     '{% if product.unit_fk_id == u.id or product.unit == u.abbreviation %}selected{% endif %}')
]
for old, new in replacements:
    new_content = new_content.replace(old, new)

if new_content != content:
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("✔ Successfully fixed product_form.html")
else:
    print("⚠ No changes made. Maybe strings were not found exactly as expected?")
    # Print near miss if possible?
    if 'product.category_id' in content:
        print("Found product.category_id nearby:")
        start = content.find('product.category_id')
        print(content[start:start+50])

