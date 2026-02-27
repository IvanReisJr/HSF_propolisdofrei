import os

path = r'c:\IvanReis\Sistemas_HSF\HSF_propolisdofrei\templates\products\product_list.html'

with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    # Fix spaces around ==
    line = line.replace('selected_category==category.id|stringformat:"s"', 'selected_category == category.id|stringformat:"s"')
    line = line.replace('selected_status==\'all\'', 'selected_status == \'all\'')
    line = line.replace('selected_status==\'active\'', 'selected_status == \'active\'')
    line = line.replace('selected_status==\'inactive\'', 'selected_status == \'inactive\'')
    # Fix spaces around <
    line = line.replace('product.get_total_stock < product.min_stock', 'product.get_total_stock < product.min_stock') # Already has spaces, but just in case
    new_lines.append(line)

# Join and then fix the split tag
content = "".join(new_lines)
content = content.replace('selected{%\n                    endif %}', 'selected{% endif %}')
content = content.replace('selected{%\n                    endif %}', 'selected{% endif %}') # Duplicate check

with open(path, 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)

print("Fixed product_list.html")
