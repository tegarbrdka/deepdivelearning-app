import os
import re

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    new_content = content
    
    def repl(match):
        full_class = match.group(1)
        if re.search(r'bg-(indigo|violet|blue|red|teal|green|yellow|amber|rose|pink|purple)-\d+', full_class):
            return match.group(0) 
        new_class = re.sub(r'\btext-white\b', 'text-slate-900', full_class)
        return f'className="{new_class}"'

    new_content = re.sub(r'className="([^"]*?text-white[^"]*?)"', repl, new_content)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)

for root, dirs, files in os.walk('f:/educlasify/frontend/src'):
    for file in files:
        if file.endswith('.jsx'):
            process_file(os.path.join(root, file))
print('Done replacing text-white!')
