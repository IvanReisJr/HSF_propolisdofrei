with open(r'templates\products\product_form.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find and fix broken tags across multiple lines
i = 0
while i < len(lines):
    line = lines[i]
    
    # Check if line has unclosed {% if but no %}
    if '{% if' in line and '%}' not in line:
        # Join with next line
        if i + 1 < len(lines):
            lines[i] = line.rstrip() + ' ' + lines[i+1].lstrip()
            lines.pop(i+1)
            print(f"✅ Juntou linhas {i+1} e {i+2}")
    
    # Check for broken {% endif %}
    if '{% endif' in line and '%}' not in line:
        if i + 1 < len(lines):
            lines[i] = line.rstrip() + lines[i+1].lstrip()
            lines.pop(i+1)
            print(f"✅ Juntou endif nas linhas {i+1} e {i+2}")
    
    i += 1

with open(r'templates\products\product_form.html', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("\n✅ Tags quebradas corrigidas!")
