import os
import re

def fix_contrast(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    new_content = content

    # 1. StatCard defaults and prop overrides
    new_content = re.sub(r"color = 'text-white'", "color = 'text-slate-900'", new_content)
    new_content = re.sub(r'color="text-white"', 'color="text-slate-900"', new_content)
    new_content = re.sub(r"color: 'text-white'", "color: 'text-slate-900'", new_content)

    # 2. Text colors on light backgrounds (excluding those already handled in Replace_text if any)
    # Be careful not to replace text-white on btn-primary or other dark backgrounds.
    # Replace the light colored texts (-300, -400) which are used for stats
    replacements = {
        'text-teal-300': 'text-teal-600',
        'text-teal-400': 'text-teal-600',
        'text-blue-300': 'text-blue-600',
        'text-blue-400': 'text-blue-600',
        'text-amber-300': 'text-amber-600',
        'text-amber-400': 'text-amber-600',
        'text-red-300': 'text-red-600',
        'text-red-400': 'text-red-600',
        'text-violet-300': 'text-violet-600',
        'text-violet-400': 'text-violet-600',
        'text-orange-400': 'text-orange-600',
        'text-emerald-400': 'text-emerald-600',
        'text-teal-200': 'text-teal-700',
        'text-blue-200': 'text-blue-700',
        'text-amber-200': 'text-amber-700',
        'text-red-200': 'text-red-700',
    }

    for old, new in replacements.items():
        new_content = new_content.replace(old, new)

    # 3. Chart config replacements (Recharts)
    # XAxis, YAxis, PolarAngleAxis ticks
    new_content = new_content.replace("fill: '#e2e8f0'", "fill: '#64748b'")
    new_content = new_content.replace("fill: '#cbd5e1'", "fill: '#64748b'")
    new_content = new_content.replace("fill: '#94a3b8'", "fill: '#64748b'")
    
    # PolarGrid stroke
    new_content = new_content.replace('stroke="#162d57"', 'stroke="#e2e8f0"')
    
    # CartesianGrid stroke
    new_content = new_content.replace('stroke="#162d57"', 'stroke="#e2e8f0"')

    # Tooltip background
    new_content = new_content.replace("background: '#0f2040'", "background: '#ffffff'")
    new_content = new_content.replace("border: '1px solid #162d57'", "border: '1px solid #e2e8f0'")
    new_content = new_content.replace("border: '1px solid #162d57', borderRadius: 12, fontSize: 12", "border: '1px solid #e2e8f0', borderRadius: 12, fontSize: 12, color: '#0f172a'")

    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Fixed contrast in {os.path.basename(filepath)}")

admin_dir = 'f:/educlasify/frontend/src/pages/admin'
for file in os.listdir(admin_dir):
    if file.endswith('.jsx'):
        fix_contrast(os.path.join(admin_dir, file))

print("All done!")
