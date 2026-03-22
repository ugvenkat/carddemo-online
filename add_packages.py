"""
add_packages.py
---------------
Adds package declarations to all generated Java files.
Run from: C:\Study\carddemo-online
"""
import os
import glob

mappings = [
    ('src/main/java/com/carddemo/dto/*.java',          'com.carddemo.dto'),
    ('src/main/java/com/carddemo/controllers/*.java',  'com.carddemo.controllers'),
    ('src/test/java/com/carddemo/dto/*.java',          'com.carddemo.dto'),
    ('src/test/java/com/carddemo/controllers/*.java',  'com.carddemo.controllers'),
]

for pattern, pkg in mappings:
    for f in glob.glob(pattern):
        content = open(f, encoding='utf-8').read()
        if not content.lstrip().startswith('package'):
            content = f'package {pkg};\n\n' + content
            open(f, 'w', encoding='utf-8').write(content)
            print(f'Added package {pkg} to: {os.path.basename(f)}')
        else:
            print(f'Already has package: {os.path.basename(f)}')

print('\nDone!')
