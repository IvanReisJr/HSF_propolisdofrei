
import re
import os

file_path = os.path.join('templates', 'products', 'product_form.html')

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

stack = []
for i, line in enumerate(lines):
    line_num = i + 1
    # Find all tags
    tags = re.findall(r'{%\s*(\w+)', line)
    for tag in tags:
        if tag in ['if', 'for', 'block', 'with']:
            stack.append((tag, line_num))
            print(f"Line {line_num}: Open {tag}")
        elif tag in ['endif', 'endfor', 'endblock', 'endwith']:
            if not stack:
                print(f"Line {line_num}: ERROR - Unexpected {tag}")
            else:
                last_tag, last_line = stack[-1]
                expected_close = 'end' + last_tag
                if tag == expected_close:
                    stack.pop()
                    print(f"Line {line_num}: Close {tag} (Matches {last_tag} from {last_line})")
                else:
                    print(f"Line {line_num}: ERROR - Found {tag} but expected {expected_close} (for {last_tag} from {last_line})")

if stack:
    print("\nUNCLOSED TAGS:")
    for tag, line_num in stack:
        print(f"Line {line_num}: {tag} was never closed")
else:
    print("\nAll block tags balanced.")
