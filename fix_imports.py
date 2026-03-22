"""
fix_imports.py
--------------
Adds missing DTO import statements to all controller files.
Run from: C:\Study\carddemo-online
"""
import os
import glob

# All DTO classes that controllers might use
DTO_IMPORTS = """import com.carddemo.dto.CardDemoCommArea;
import com.carddemo.dto.TransactionRecord;
import com.carddemo.dto.AccountRecord;
import com.carddemo.dto.CardXrefRecord;
import com.carddemo.dto.CustomerRecord;
import com.carddemo.dto.UserSecurityData;
import com.carddemo.dto.TitleData;
import com.carddemo.dto.DateData;
import com.carddemo.dto.MessageData;
"""

for f in glob.glob('src/main/java/com/carddemo/controllers/*.java'):
    content = open(f, encoding='utf-8').read()

    # Find where to insert imports — after package declaration
    lines = content.splitlines()
    insert_idx = 0
    for i, line in enumerate(lines):
        if line.startswith('package '):
            insert_idx = i + 1
            break

    # Check if imports already exist
    if 'import com.carddemo.dto.CardDemoCommArea;' not in content:
        # Insert DTO imports after package line
        lines.insert(insert_idx, '')
        lines.insert(insert_idx + 1, DTO_IMPORTS)
        content = '\n'.join(lines)
        open(f, 'w', encoding='utf-8').write(content)
        print(f'Added DTO imports to: {os.path.basename(f)}')
    else:
        print(f'Already has imports: {os.path.basename(f)}')

print('\nDone! Now run: mvn compile')
