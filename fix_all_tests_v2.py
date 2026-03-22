"""
fix_all_tests_v2.py
-------------------
Fixes ALL test compilation errors based on actual controller field names.

Actual field names from controllers:
  AuthController.SignonScreenData    -> errorMessage (not message)
  MenuController.MenuResponse        -> errorMessage (not message)
  MenuController.MenuOption          -> optNum, optName, optPgmName, optUsrType
  MenuController.MenuSelectRequest   -> option (int, not String)
  TransactionViewResponse            -> tranAmt (String, not BigDecimal)
  TransactionListController.ApiResponse -> data is Object -> cast to Map<?,?>

Run from: C:\Study\carddemo-online
"""
import re
import glob
import os

fixes_applied = 0

for f in glob.glob('src/test/java/com/carddemo/controllers/*.java'):
    content = open(f, encoding='utf-8').read()
    original = content
    fname = os.path.basename(f)

    # -------------------------------------------------------
    # AuthControllerTest fixes
    # -------------------------------------------------------
    if 'AuthControllerTest' in fname:
        # screenData.message -> screenData.errorMessage
        # BUT only when screenData is SignonScreenData type
        content = re.sub(
            r'(screenData)\.message\b',
            r'\1.errorMessage',
            content
        )

    # -------------------------------------------------------
    # MenuControllerTest fixes
    # -------------------------------------------------------
    if 'MenuControllerTest' in fname:
        # response.message -> response.errorMessage (MenuResponse type)
        content = re.sub(
            r'(response)\.message\b(?!\s*=\s*null)',
            r'\1.errorMessage',
            content
        )
        content = re.sub(
            r'(response)\.message\s*=\s*null',
            r'\1.errorMessage = null',
            content
        )
        content = re.sub(
            r'(response)\.message\s*=\s*"([^"]*)"',
            r'\1.errorMessage = "\2"',
            content
        )
        # request.option = "5" -> request.option = 5 (int not String)
        content = re.sub(
            r'(request\.option)\s*=\s*"(\d+)"',
            r'\1 = \2',
            content
        )
        # MenuOption field: optionNum -> optNum
        content = content.replace('.optionNum', '.optNum')
        # MenuOption field: optionName -> optName
        content = content.replace('.optionName', '.optName')
        # MenuOption field: programName -> optPgmName
        content = content.replace('.programName', '.optPgmName')
        # MenuOption field: userType -> optUsrType
        content = content.replace('.userType', '.optUsrType')

    # -------------------------------------------------------
    # TransactionListControllerTest fixes
    # -------------------------------------------------------
    if 'TransactionListControllerTest' in fname:
        # Map<String,Object> cast -> Map<?,?>
        content = re.sub(r'\(Map<String,\s*Object>\)', '(Map<?,?>)', content)
        # apiResponse.message stays as message (ApiResponse.message is correct)

    # -------------------------------------------------------
    # TransactionViewControllerTest fixes
    # -------------------------------------------------------
    if 'TransactionViewControllerTest' in fname:
        # tranAmt is String in TransactionViewResponse, not BigDecimal
        # Fix: tran.tranAmt = new BigDecimal("125.99") -> tran.tranAmt = "125.99"
        content = re.sub(
            r'(\.tranAmt)\s*=\s*new BigDecimal\("([^"]+)"\)',
            r'\1 = "\2"',
            content
        )
        content = re.sub(
            r'(\.tranAmt)\s*=\s*BigDecimal\.valueOf\(([^)]+)\)',
            r'\1 = String.valueOf(\2)',
            content
        )
        # Fix assertEquals with BigDecimal vs String for tranAmt
        content = re.sub(
            r'assertEquals\(new BigDecimal\("([^"]+)"\),\s*([^)]*tranAmt[^)]*)\)',
            r'assertEquals("\1", \2)',
            content
        )
        # tranCatCd is int in TransactionViewResponse
        # Fix: assertEquals("5001", ...) -> assertEquals(5001, ...)
        content = re.sub(
            r'assertEquals\("(\d+)",\s*([^)]*tranCatCd[^)]*)\)',
            r'assertEquals(\1, \2)',
            content
        )
        # Fix String assigned to int tranCatCd
        content = re.sub(
            r'(\.tranCatCd)\s*=\s*"(\d+)"',
            r'\1 = \2',
            content
        )
        # UserSecurityData field names
        content = content.replace('.secUserId', '.secUsrId')
        content = content.replace('.secUserPwd', '.secUsrPwd')
        content = content.replace('.secUserType', '.secUsrType')

    # -------------------------------------------------------
    # TransactionAddControllerTest fixes
    # -------------------------------------------------------
    if 'TransactionAddControllerTest' in fname:
        # All TransactionAddRequest fields are String
        # Fix BigDecimal -> String
        content = re.sub(
            r'=\s*new BigDecimal\("([^"]+)"\)',
            r'= "\1"',
            content
        )
        content = re.sub(
            r'assertEquals\(new BigDecimal\("([^"]+)"\),\s*([^)]+)\)',
            r'assertEquals("\1", \2)',
            content
        )
        # Fix int/long literals for String fields
        content = re.sub(
            r'(request\.\w+)\s*=\s*(\d+)L?;',
            r'\1 = "\2";',
            content
        )
        # Fix .transactionType -> .typeCode
        content = content.replace('.transactionType', '.typeCode')

    if content != original:
        open(f, 'w', encoding='utf-8').write(content)
        fixes_applied += 1
        print(f'Fixed: {fname}')
    else:
        print(f'OK:    {fname}')

print(f'\nFixed {fixes_applied} file(s). Now run: mvn spring-boot:run')
