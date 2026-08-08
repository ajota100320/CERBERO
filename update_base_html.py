import re

file_path = r'C:\Users\hola\Documents\Mi segundo Cerebro\Nuevo proyecto ERP\templates\base.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern for the desktop Finanzas dropdown panel
desktop_pattern = r'(<div class="hidden absolute right-0 mt-1 w-44 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-50 nav-dropdown-panel">\s*)(.*?)(\s*</div>)'

def replace_desktop_inner(match):
    prefix = match.group(1)
    inner = match.group(2)
    suffix = match.group(3)
    # Add the new link if not already present
    if '/requerimientos' not in inner:
        # We'll add it at the end of the inner content, before the closing </div>
        new_inner = inner + '\n            <a href="/requerimientos" class="block px-4 py-2 text-sm text-gray-700 hover:bg-primary-50 hover:text-primary-700">Requerimientos</a>'
        return prefix + new_inner + suffix
    return match.group(0)

new_content = re.sub(desktop_pattern, replace_desktop_inner, content, flags=re.DOTALL)

# Pattern for the mobile Finanzas group
mobile_pattern = r'(<div class="pt-2">\s*<p class="px-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">Finanzas</p>\s*)(.*?)(\s*</div>)'

def replace_mobile_inner(match):
    prefix = match.group(1)
    inner = match.group(2)
    suffix = match.group(3)
    if '/requerimientos' not in inner:
        new_inner = inner + '\n                    <a href="/requerimientos" class="block px-3 py-2 rounded-md text-base font-medium text-gray-700 hover:bg-primary-50 hover:text-primary-700 transition-colors">Requerimientos</a>'
        return prefix + new_inner + suffix
    return match.group(0)

new_content = re.sub(mobile_pattern, replace_mobile_inner, new_content, flags=re.DOTALL)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print('Updated base.html with Requerimientos link in Finanzas dropdown.')