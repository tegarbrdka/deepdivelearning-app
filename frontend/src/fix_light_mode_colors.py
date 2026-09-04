import os
import re

def fix_colors_in_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find text-[color]-[200/300] that are NOT preceded by "dark:"
    # and replace them with text-[color]-700 dark:text-[color]-[200/300]
    
    # Pattern explanation:
    # (?<!dark:) -> Negative lookbehind for "dark:"
    # text- -> Literal "text-"
    # (red|amber|yellow|emerald|green|teal|cyan|blue|indigo|violet|purple|rose|pink) -> Color names
    # -([23]00) -> The shade (200 or 300)
    # (?!\/|0) -> Negative lookahead to prevent matching things like text-red-200/50 (opacity), we'll handle opacity separately if needed. 
    # Actually, let's include opacity if it exists.
    
    pattern = r"(?<!dark:)text-(red|amber|yellow|emerald|green|teal|cyan|blue|indigo|violet|purple|rose|pink)-([23]00)(/[0-9]+)?"
    
    def replacer(match):
        color = match.group(1)
        shade = match.group(2)
        opacity = match.group(3) or ""
        
        # Determine a good dark shade for light mode
        # 800 is usually good for contrast on light backgrounds
        dark_shade = "800"
        if shade == "200":
            dark_shade = "700"
            
        return f"text-{color}-{dark_shade}{opacity} dark:text-{color}-{shade}{opacity}"

    new_content = re.sub(pattern, replacer, content)

    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Fixed colors in: {filepath}")
        return True
    return False

def scan_and_fix(directory):
    fixed_count = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(('.jsx', '.js')):
                filepath = os.path.join(root, file)
                if fix_colors_in_file(filepath):
                    fixed_count += 1
    return fixed_count

if __name__ == "__main__":
    src_dir = r"f:\educlasify\frontend\src"
    print(f"Scanning {src_dir} for light-mode text contrast issues...")
    count = scan_and_fix(src_dir)
    print(f"Done! Fixed {count} files.")
