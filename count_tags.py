with open(r'templates\products\product_form.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

ifs = []
endifs = []

for i, line in enumerate(lines, 1):
    if '{% if' in line:
        ifs.append(i)
    if '{% endif' in line:
        endifs.append(i)

print(f"Total {% if: {len(ifs)}")
print(f"Linhas com {% if: {ifs}")
print(f"\nTotal {% endif: {len(endifs)}")
print(f"Linhas com {% endif: {endifs}")
print(f"\nDiferença: {len(ifs) - len(endifs)}")

if len(ifs) > len(endifs):
    print(f"\n❌ Faltam {len(ifs) - len(endifs)} {% endif %}")
    print("\nVerificando cada {% if:")
    for line_num in ifs:
        print(f"  Linha {line_num}: {lines[line_num-1].strip()[:80]}")
