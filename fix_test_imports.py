"""
fix_test_imports.py
-------------------
Fixes test files that reference inner classes from controllers.
Inner classes like LoginRequest must be imported as:
  import com.carddemo.controllers.AuthController.LoginRequest;
Run from: C:\Study\carddemo-online
"""
import os
import re
import glob

# Map of inner class names -> their controller class
INNER_CLASS_MAP = {
    'LoginRequest':    'AuthController',
    'ApiResponse':     'AuthController',
    'MenuOption':      'MenuController',
    'SelectRequest':   'MenuController',
    'TransactionPage': 'TransactionListController',
    'SelectTranRequest': 'TransactionListController',
    'AddTransactionRequest': 'TransactionAddController',
}

for f in glob.glob('src/test/java/com/carddemo/controllers/*.java'):
    content = open(f, encoding='utf-8').read()
    original = content
    added = []

    for inner_class, controller in INNER_CLASS_MAP.items():
        # Check if this inner class is used in the test
        if inner_class in content:
            import_stmt = f'import com.carddemo.controllers.{controller}.{inner_class};'
            if import_stmt not in content:
                # Insert after package declaration
                lines = content.splitlines()
                for i, line in enumerate(lines):
                    if line.startswith('package '):
                        lines.insert(i + 1, import_stmt)
                        content = '\n'.join(lines)
                        added.append(import_stmt)
                        break

    # Also add controller import itself
    ctrl_name = os.path.basename(f).replace('Test.java', '')
    ctrl_import = f'import com.carddemo.controllers.{ctrl_name};'
    if ctrl_import not in content and ctrl_name in content:
        lines = content.splitlines()
        for i, line in enumerate(lines):
            if line.startswith('package '):
                lines.insert(i + 1, ctrl_import)
                content = '\n'.join(lines)
                added.append(ctrl_import)
                break

    if content != original:
        open(f, 'w', encoding='utf-8').write(content)
        print(f'Fixed {os.path.basename(f)}:')
        for imp in added:
            print(f'  + {imp}')
    else:
        print(f'No changes needed: {os.path.basename(f)}')

print('\nDone! Now run: mvn compile')
