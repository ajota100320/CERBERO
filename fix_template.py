# Script to fix the requerimientos.html template
import re

file_path = r'C:\Users\hola\Documents\Mi segundo Cerebro\Nuevo proyecto ERP\templates\requerimientos.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: Change total_estimado to total_proyectado in the header
# We need to be careful to only change the one in the header, not any other occurrences
# Looking at the structure, the header is in the div with class "px-6 py-4 border-b border-gray-200"
# We'll replace the specific pattern

# Pattern to find the header div content and replace total_estimado with total_proyectado
# But simpler: replace all instances of total_estimado with total_proyectado since that's what we want
# However, let's check if there are other uses - from the content, it seems only in those two places
# And we are removing one of them.

# First, fix the variable name
content = content.replace('total_estimado', 'total_proyectado')

# Now, fix the duplicate/malformed section
# We need to remove the erroneous block between the header and the table
# Looking at the structure:
# After the header div (which ends at line 87 in the original), there should be the table div
# But instead, we have:
#   <div class="overflow-x-auto">Lista de Requerimientos</h2>
#       <p>...</p>
#   </div>
#   <div class="overflow-x-auto">
#       <table>...
#
# We want to remove lines 88-90 (approximately) and ensure the table div starts right after the header div.

# Let's find the pattern of the incorrect duplicated header
# From the content we saw:
# After: </div>\n        <div class="overflow-x-auto">Lista de Requerimientos</h2>\n
# We want to remove from that point until the next </div> that closes that erroneous div, 
# but before the next <div class="overflow-x-auto"> that starts the table.

# Actually, let's look for the specific erroneous block:
# It starts with: '<div class="overflow-x-auto">Lista de Requerimientos</h2>'
# and ends with: '</div>\n        <div class="overflow-x-auto">' (which is the start of the table div)

# But to be safe, we can do:
# Remove the block that starts with '<div class="overflow-x-auto">Lista de Requerimientos</h2>' 
# and ends with the next '</div>' that is followed by whitespace and then '<div class="overflow-x-auto">'

# However, given the exact content we saw earlier, we can do a direct replacement of the known problematic section.

# Let's split the content and look for the problematic lines
lines = content.split('\n')
new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    # Detect the start of the erroneous block
    if '<div class="overflow-x-auto">Lista de Requerimientos</h2>' in line:
        # Skip this line and the next lines until we find the closing </div> of this div
        # and then skip the following line which is the start of the table div (we'll add it back later?)
        # Actually, we want to remove this entire erroneous block and let the next proper table div take over.
        # So we skip until we find the closing </div> of this erroneous div.
        i += 1  # move to next line
        # Skip until we find a line that contains '</div>' and is likely the end of this div
        while i < len(lines) and '</div>' not in lines[i]:
            i += 1
        # Now we are at the line with '</div>'
        i += 1  # skip this closing div line
        # The next line should be the start of the table div: '<div class="overflow-x-auto">'
        # We'll let the loop continue and process that line normally.
        continue
    else:
        new_lines.append(line)
        i += 1

# Join back
content = '\n'.join(new_lines)

# Write back
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed requerimientos.html: changed variable name and removed duplicate header')