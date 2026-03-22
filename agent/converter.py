"""
converter.py
------------
Handles all Claude API calls for conversion.
ONLINE VERSION — converts CICS COBOL programs to Spring Boot REST API.

Key learnings baked into prompts:
  1. CICS programs are pseudo-conversational — convert to stateless REST
  2. EXEC CICS RECEIVE MAP = @PostMapping or @GetMapping request body
  3. EXEC CICS SEND MAP = return ResponseEntity<ApiResponse>
  4. EXEC CICS READ DATASET = HashMap.get(key)
  5. EXEC CICS WRITE DATASET = HashMap.put(key, record)
  6. EXEC CICS STARTBR/READNEXT/ENDBR = ArrayList pagination
  7. EXEC CICS XCTL PROGRAM = return redirect URL in response
  8. DFHCOMMAREA = Java session/request context object (CardDemoCommArea)
  9. COMMAREA fields = Java DTO fields
  10. EIBAID DFHENTER = POST request, DFHPF3 = back navigation
  11. BMS map fields (XXXXI/XXXXO) = Java DTO request/response fields
  12. Class name must match filename exactly
  13. Use jakarta.annotation (NOT javax.annotation) — Spring Boot 3 / Java 17
  14. TRAN-TYPE-CD is PIC X(02) = alphabetic (PU, SA) NOT numeric
  15. All DTO imports must be explicit — com.carddemo.dto.*
  16. Never redefine DTO classes inside controllers or tests
  17. isAdmin() and isRegularUser() are methods — call with parentheses
"""

import time
import logging
import re
import anthropic

logger = logging.getLogger("Converter")

# Claude model to use
MODEL = "claude-opus-4-5"

# Max tokens per response
MAX_TOKENS = 8192


class Converter:

    def __init__(self, api_key: str, rate_limit_delay: int = 5):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.delay  = rate_limit_delay

    # -----------------------------------------------------------------------
    # PHASE 1: Convert COBOL Copybook -> Java DTO/Model class
    # -----------------------------------------------------------------------
    def convert_copybook(self, filename: str, source: str) -> str:
        """Converts a COBOL copybook to a Java DTO or model class."""

        # Lookup exact class name for this copybook
        copybook_class_map = {
            "COCOM01Y":  "CardDemoCommArea",
            "CVCUS01Y":  "CustomerRecord",
            "CVTRA05Y":  "TransactionRecord",
            "CVACT01Y":  "AccountRecord",
            "CVACT03Y":  "CardXrefRecord",
            "COTTL01Y":  "TitleData",
            "CSDAT01Y":  "DateData",
            "CSMSG01Y":  "MessageData",
            "CSUSR01Y":  "UserSecurityData",
        }
        stem = filename.replace(".cpy", "").replace(".CPY", "").upper()
        exact_class_name = copybook_class_map.get(stem, stem.title().replace("_",""))

        prompt = f"""You are an expert mainframe modernization engineer converting COBOL copybooks to Java.

Convert the following COBOL copybook to a Java class for use in a Spring Boot REST API.

COPYBOOK FILENAME: {filename}
COPYBOOK SOURCE:
{source}

STRICT RULES:

0. CLASS NAMING — MOST CRITICAL RULE:
   The class name MUST be exactly: {exact_class_name}
   The file will be saved as {exact_class_name}.java
   DO NOT use any other name. DO NOT expand abbreviations differently.

1. CLASS TYPE — choose the most appropriate:
   - If it's a communication area (COMMAREA) or session context -> plain Java class with public fields
   - If it's a data record (account, customer, transaction) -> plain Java class with public fields
   - If it's working storage (dates, messages, titles) -> plain Java class with public fields
   - Add @JsonProperty annotations on fields that have unusual names
   - NO package declaration
   - NO JPA annotations (@Entity etc) — these are plain data transfer objects
   - Import: import com.fasterxml.jackson.annotation.JsonProperty; if needed

2. FIELD MAPPING:
   - PIC X(n)       -> public String fieldName;    initialized to ""
   - PIC 9(n) n<=4  -> public int fieldName;       initialized to 0
   - PIC 9(n) n>4   -> public long fieldName;      initialized to 0L
   - PIC S9(n)V99   -> public java.math.BigDecimal fieldName; initialized to BigDecimal.ZERO
   - FILLER         -> SKIP — do not create a field
   - 88 level items -> public static final String CONSTANT = "value";
   - OCCURS n TIMES -> use List<SubType> or String[] — choose appropriate
   - Group items (05, 10 level) -> flatten into individual fields OR create inner static class

3. COMMAREA SPECIAL HANDLING (COCOM01Y -> CardDemoCommArea):
   - This is the session context passed between CICS programs
   - In REST API it becomes a session/context object
   - All fields become public with defaults
   - Add helper methods: isAdmin(), isRegularUser()

4. CONSTRUCTOR and METHODS:
   - Default no-arg constructor initializing all String fields to ""
   - toString() for debugging

5. COMMAREA HELPER METHODS (COCOM01Y -> CardDemoCommArea only):
   Add these exact methods — controllers call them as methods NOT fields:
   public boolean isAdmin() {{
       return "A".equals(cdemoUserType != null ? cdemoUserType.trim() : "");
   }}
   public boolean isRegularUser() {{
       return "U".equals(cdemoUserType != null ? cdemoUserType.trim() : "");
   }}

6. USER SECURITY (CSUSR01Y):
   - Contains SEC-USER-DATA with user ID, password, type fields
   - Convert to UserSecurityData class with secUsrId, secUsrPwd, secUsrType fields

Return ONLY the Java class code. No explanation, no markdown, no ```java blocks.
Start directly with the import statements (if any) and end with the closing brace.
"""
        return self._call_api(prompt, f"copybook {filename}")

    # -----------------------------------------------------------------------
    # PHASE 2: Convert CICS COBOL Program -> Spring Boot REST Controller
    # -----------------------------------------------------------------------
    def convert_cobol(self, filename: str, source: str,
                      used_copybooks: dict, converted_records: dict,
                      java_class_content: dict = None) -> str:
        """Converts a CICS COBOL program to a Spring Boot REST controller."""

        # Build context from actual generated Java classes
        copybook_section = ""
        if java_class_content:
            copybook_section += "ACTUAL JAVA DTO CLASSES — use EXACT field names shown below:\n"
            for java_class_name, java_src in java_class_content.items():
                fields = re.findall(r"public\s+(?:static\s+final\s+)?\w+\s+\w+[^(]", java_src)
                copybook_section += f"\n=== {java_class_name}.java ===\n"
                for f in fields[:30]:
                    copybook_section += f"  {f.strip()};\n"
        else:
            for cpy_name, cpy_source in used_copybooks.items():
                java_class = converted_records.get(cpy_name, cpy_name)
                copybook_section += f"\n--- {cpy_name}.cpy (Java class: {java_class}) ---\n{cpy_source}\n"

        # Exact service class name mapping
        service_map = {
            "COSGN00C": "AuthController",
            "COMEN01C": "MenuController",
            "COTRN00C": "TransactionListController",
            "COTRN01C": "TransactionViewController",
            "COTRN02C": "TransactionAddController",
        }
        stem = filename.replace(".cbl","").replace(".CBL","").upper()
        exact_class_name = service_map.get(stem, stem.title() + "Controller")

        prompt = f"""You are an expert mainframe modernization engineer converting CICS COBOL programs to Spring Boot REST API.

Convert the following CICS COBOL program to a Spring Boot REST controller.

COBOL FILENAME: {filename}
COBOL SOURCE:
{source}

JAVA DTO CLASSES AVAILABLE (use EXACT field names shown):
{copybook_section if copybook_section else "None"}

STRICT RULES — CICS to Spring Boot conversion:

0. CLASS NAMING — CRITICAL:
   The class name MUST be exactly: {exact_class_name}
   File will be saved as {exact_class_name}.java
   MAPPING:
     COSGN00C.cbl  -> AuthController
     COMEN01C.cbl  -> MenuController
     COTRN00C.cbl  -> TransactionListController
     COTRN01C.cbl  -> TransactionViewController
     COTRN02C.cbl  -> TransactionAddController

1. CLASS STRUCTURE:
   - No package declaration — standalone file
   - Annotate with @RestController
   - Annotate with @RequestMapping("/api/[resource]"):
       AuthController         -> /api/auth
       MenuController         -> /api/menu
       TransactionListController  -> /api/transactions
       TransactionViewController  -> /api/transactions
       TransactionAddController   -> /api/transactions
   - Import: org.springframework.web.bind.annotation.*
   - Import: org.springframework.http.*
   - Import: java.util.*
   - Import: java.math.BigDecimal
   - Import: java.time.*
   - Import: jakarta.annotation.PostConstruct;   (NEVER use javax.annotation — Spring Boot 3 uses jakarta)
   - Import ALL DTO classes used in this controller:
       import com.carddemo.dto.CardDemoCommArea;
       import com.carddemo.dto.TransactionRecord;
       import com.carddemo.dto.AccountRecord;
       import com.carddemo.dto.CardXrefRecord;
       import com.carddemo.dto.CustomerRecord;
       import com.carddemo.dto.UserSecurityData;
   - ALWAYS add these imports even if you think they might not be needed
   - Controllers are in package com.carddemo.controllers
   - DTOs are in package com.carddemo.dto — they MUST be imported explicitly
   - NEVER define CardDemoCommArea, TransactionRecord, AccountRecord, CardXrefRecord,
     CustomerRecord, or UserSecurityData as inner classes inside a controller
   - These classes ONLY exist in com.carddemo.dto — always import and use from there
   - The controller package is com.carddemo.controllers — add NO package declaration
     (it is added automatically by the build process)

2. CICS COMMAND MAPPING — CRITICAL:
   - EXEC CICS SEND MAP / RECEIVE MAP  -> REST endpoint method (GET/POST)
   - EXEC CICS READ DATASET            -> load from in-memory HashMap (simulate file I/O)
   - EXEC CICS WRITE DATASET           -> save to in-memory HashMap
   - EXEC CICS STARTBR/READNEXT/ENDBR  -> list/paginate from HashMap values
   - EXEC CICS READPREV                -> reverse iterate HashMap values
   - EXEC CICS XCTL PROGRAM(x)         -> include "redirect" field in response JSON
   - EXEC CICS RETURN TRANSID          -> return ResponseEntity with session data
   - EXEC CICS ASSIGN APPLID/SYSID     -> return hardcoded "CARDDEMO" / "SYS1"
   - DFHRESP(NORMAL)                   -> operation succeeded (key found)
   - DFHRESP(NOTFND)                   -> return 404 / error message
   - DFHRESP(ENDFILE)                  -> end of list / empty result
   - DFHRESP(DUPKEY/DUPREC)            -> return 409 conflict

3. PSEUDO-CONVERSATIONAL -> STATELESS REST:
   - EIBCALEN = 0 means first call (no session) -> handle as fresh request
   - EIBCALEN > 0 means returning call with COMMAREA -> accept as request body
   - EIBAID DFHENTER -> POST request body
   - EIBAID DFHPF3   -> "action": "back" in request or separate GET endpoint
   - EIBAID DFHPF7   -> "action": "previous" (page back)
   - EIBAID DFHPF8   -> "action": "next" (page forward)
   - COMMAREA (CARDDEMO-COMMAREA) -> CardDemoCommArea object in request/response

4. ENDPOINT DESIGN:
   For COSGN00C (Login):
     POST /api/auth/login  body: {{userId, password}}  returns: {{success, userType, commArea, redirect}}
   For COMEN01C (Main Menu):
     GET  /api/menu        header: session  returns: {{menuOptions[], commArea}}
     POST /api/menu/select body: {{option, commArea}}  returns: {{redirect, commArea}}
   For COTRN00C (Transaction List):
     GET  /api/transactions?page=1  returns: {{transactions[], pageNum, hasNextPage}}
     POST /api/transactions/select  body: {{tranId, commArea}}  returns: {{redirect, commArea}}
   For COTRN01C (Transaction View):
     GET  /api/transactions/{{id}}  returns: {{transaction}}
   For COTRN02C (Transaction Add):
     POST /api/transactions  body: {{transaction fields}}  returns: {{success, tranId, message}}

   MENU REDIRECT VALUES — CRITICAL:
   MenuController must return COBOL program names in redirect field, NOT API paths:
     WRONG: response.redirect = "/api/transactions"
     RIGHT:  response.redirect = "COTRN00C"
   Use these exact redirect values:
     Transaction List -> redirect = "COTRN00C"
     Transaction View -> redirect = "COTRN01C"
     Transaction Add  -> redirect = "COTRN02C"
     Sign Off/Login   -> redirect = "COSGN00C"

5. FILE ACCESS SIMULATION:
   - Use a static HashMap<String, RecordType> to simulate VSAM files
   - Initialize with sample data in a @PostConstruct method (import jakarta.annotation.PostConstruct — NOT javax.annotation)
   - EXEC CICS READ -> map.get(key), return 404 if null
   - EXEC CICS WRITE -> map.put(key, record)
   - EXEC CICS STARTBR/READNEXT -> new ArrayList<>(map.values())
   - Pagination: 10 records per page (matching original screen size)
   - SAMPLE DATA for COTRN02C TransactionAddController:
     Use these card numbers in sample xref data:
       xref1.xrefCardNum = "4111111111111111"; (Visa test card)
       xref1.xrefAcctId = 80000001001L;
     Use ALPHABETIC type codes in sample transactions:
       tran.tranTypeCd = "PU";  (Purchase — NOT "01")
       tran.tranTypeCd = "SA";  (Sale — NOT "02")

6. VALIDATION:
   - Preserve ALL validation from VALIDATE-INPUT-KEY-FIELDS and VALIDATE-INPUT-DATA-FIELDS
   - Return 400 Bad Request with error message for validation failures
   - Return {{success: false, message: "..."}} in JSON body
   - CRITICAL — FIELD TYPE RULES for COTRN02C (TransactionAddController):
     TRAN-TYPE-CD  is PIC X(02) — ALPHABETIC (e.g. "PU", "SA") — NOT numeric
     TRAN-CAT-CD   is PIC 9(04) — NUMERIC (e.g. 5001)
     TRAN-SOURCE   is PIC X(10) — ALPHABETIC
     TRAN-CARD-NUM is PIC X(16) — ALPHANUMERIC (digits only but stored as String)
     TRAN-MERCHANT-ID is PIC 9(09) — NUMERIC
     DO NOT validate TRAN-TYPE-CD as numeric — it is a 2-char alpha code like "PU", "SA", "CR"
     DO NOT validate TRAN-CARD-NUM as numeric — treat as String

7. RESPONSE FORMAT — use ApiResponse wrapper:
   Use this inner class in each controller:
   public static class ApiResponse {{
       public boolean success;
       public String message;
       public Object data;
       public String redirect;
       public CardDemoCommArea commArea;
       public ApiResponse(boolean success, String message, Object data) {{
           this.success = success; this.message = message; this.data = data;
       }}
   }}

8. FIELD ACCESS:
   - Use EXACT field names from the DTO classes shown above
   - All fields are public — access directly, NO getters
   - WRONG: record.getTranId()  RIGHT: record.tranId

9. COBOL paragraph -> Java method mapping:
   - MAIN-PARA           -> @PostMapping or @GetMapping method
   - PROCESS-ENTER-KEY   -> private processEnterKey() method
   - SEND-XXX-SCREEN     -> private buildResponse() method
   - RECEIVE-XXX-SCREEN  -> handled by @RequestBody parameter
   - READ-XXXX-FILE      -> private readXxxFile(key) method
   - WRITE-XXXX-FILE     -> private writeXxxFile(record) method
   - STARTBR/READNEXT    -> private List<T> browseFile(startKey, maxRecs)
   - POPULATE-HEADER-INFO -> add date/time to response
   - RETURN-TO-PREV-SCREEN -> set redirect field in response

10. FIELD ACCESS AND METHOD CALLS:
    All DTO fields are public. Access them directly — NO getters:
    WRONG: commArea.getUserId()    RIGHT: commArea.cdemoUserId
    WRONG: tran.getTranId()        RIGHT: tran.tranId

    EXCEPTION — CardDemoCommArea has TWO helper methods, call with parentheses:
    RIGHT: commArea.isAdmin()        (method — needs parentheses)
    RIGHT: commArea.isRegularUser()  (method — needs parentheses)
    WRONG: commArea.isAdmin          (missing parentheses — will not compile)

Return ONLY the Java class code. No explanation, no markdown, no ```java blocks.
Start directly with the import statements and end with the closing brace.
"""
        return self._call_api(prompt, f"COBOL {filename}")


    # -----------------------------------------------------------------------
    # PHASE 3: Convert BMS Mapset -> React Component
    # -----------------------------------------------------------------------
    def convert_bms_to_react(self, filename: str, bms_source: str,
                              api_endpoint: str, cobol_source: str = "") -> str:
        """Converts a BMS mapset to a React functional component."""

        component_map = {
            "COSGN00": "LoginPage",
            "COMEN01": "MenuPage",
            "COTRN00": "TransactionListPage",
            "COTRN01": "TransactionViewPage",
            "COTRN02": "TransactionAddPage",
        }
        stem = filename.replace(".bms","").replace(".BMS","").upper()
        component_name = component_map.get(stem, stem.title() + "Page")

        # Build field-specific context from BMS analysis
        field_context = {
            "COSGN00": """
INPUT FIELDS FROM BMS:
- USERID: ATTRB=(FSET,IC,NORM,UNPROT) COLOR=GREEN LENGTH=8 -> <input autoFocus maxLength={8} />
- PASSWD: ATTRB=(DRK,FSET,UNPROT) COLOR=GREEN LENGTH=8 -> <input type="password" maxLength={8} />
- ERRMSG: ATTRB=(ASKIP,BRT,FSET) COLOR=RED LENGTH=78 POS=(23,1) -> error div, red text
FUNCTION KEYS: ENTER=Sign-on F3=Exit
ASCII ART: Show the credit card art from BMS lines 7-15 in a pre element
NAVIGATION: On login success navigate to /menu (user) or /admin (admin)
""",
            "COMEN01": """
INPUT FIELDS FROM BMS:
- OPTION: ATTRB=(FSET,IC,NORM,NUM,UNPROT) LENGTH=2 POS=(20,41) -> <input type="number" autoFocus maxLength={2} />
  Label: "Please select an option :" at POS=(20,15)
DISPLAY FIELDS:
- OPTN001-OPTN012: 12 menu option text slots POS=(6,20) to (17,20) LENGTH=40
  Display as numbered list, each clickable
- ERRMSG: COLOR=RED POS=(23,1) -> error div
FUNCTION KEYS: ENTER=Continue F3=Exit
NAVIGATION: On option select call POST /api/menu/select then navigate based on redirect
""",
            "COTRN00": """
INPUT FIELDS FROM BMS:
- TRNIDINI: ATTRB=(FSET,NORM,UNPROT) LENGTH=16 POS=(6,21) -> Search Tran ID input
  Label: "Search Tran ID:" at POS=(6,5)
- SEL0001-SEL0010: ATTRB=(FSET,NORM,UNPROT) LENGTH=1 POS=(10-19,3) -> selection field per row
  User types "S" to select a transaction
DISPLAY FIELDS (10 rows):
- TRNID01-TRNID10: Transaction IDs COLOR=BLUE LENGTH=16
- TDATE01-TDATE10: Dates COLOR=BLUE LENGTH=8
- TDESC01-TDESC10: Descriptions COLOR=BLUE LENGTH=26
- TAMT001-TAMT010: Amounts COLOR=BLUE LENGTH=12
- PAGENUM: Page number display POS=(4,71)
- ERRMSG: COLOR=RED POS=(23,1)
FUNCTION KEYS: ENTER=Continue F3=Back F7=Backward F8=Forward
TABLE: Show as table with columns: Sel | Transaction ID | Date | Description | Amount
SELECTION: Click row or type S in sel field -> navigate to /transactions/:id
PAGINATION: PF7=prev page (GET ?page=N-1) PF8=next page (GET ?page=N+1)
""",
            "COTRN01": """
INPUT FIELDS FROM BMS:
- TRNIDINI: ATTRB=(FSET,IC,NORM,UNPROT) LENGTH=16 POS=(6,21) -> Tran ID search, autoFocus
  Label: "Enter Tran ID:" at POS=(6,6)
DISPLAY FIELDS (all read-only after fetch):
- TRNID: Transaction ID POS=(10,22) LENGTH=16
- CARDNUM: Card Number POS=(10,58) LENGTH=16
- TTYPCD: Type Code POS=(12,15) LENGTH=2
- TCATCD: Category Code POS=(12,36) LENGTH=4
- TRNSRC: Source POS=(12,54) LENGTH=10
- TDESC: Description POS=(14,19) LENGTH=60
- TRNAMT: Amount POS=(16,14) LENGTH=12
- TORIGDT: Orig Date POS=(16,42) LENGTH=10
- TPROCDT: Proc Date POS=(16,68) LENGTH=10
- MID: Merchant ID POS=(18,19) LENGTH=9
- MNAME: Merchant Name POS=(18,48) LENGTH=30
- MCITY: Merchant City POS=(20,21) LENGTH=25
- MZIP: Merchant Zip POS=(20,67) LENGTH=10
- ERRMSG: COLOR=RED POS=(23,1)
FUNCTION KEYS: ENTER=Fetch F3=Back F4=Clear F5=Browse Tran.
FLOW: Type ID -> press Enter/Fetch button -> display all fields
F5 -> navigate to /transactions list
""",
            "COTRN02": """
INPUT FIELDS FROM BMS (all UNPROT = editable):
- ACTIDIN: LENGTH=11 POS=(6,21) autoFocus -> Account ID OR
- CARDNIN: LENGTH=16 POS=(6,55) -> Card Number (one or the other)
  Show both with "(or)" between them
- TTYPCD: LENGTH=2 POS=(10,15) -> Type Code (ALPHABETIC: PU, SA, CR etc - NOT numeric)
- TCATCD: LENGTH=4 POS=(10,36) -> Category Code
- TRNSRC: LENGTH=10 POS=(10,54) -> Source
- TDESC: LENGTH=60 POS=(12,19) -> Description
- TRNAMT: LENGTH=12 POS=(14,14) -> Amount format hint: (-99999999.99) shown at POS=(15,13)
- TORIGDT: LENGTH=10 POS=(14,42) -> Orig Date format hint: (YYYY-MM-DD) shown at POS=(15,41)
- TPROCDT: LENGTH=10 POS=(14,68) -> Proc Date format hint: (YYYY-MM-DD) shown at POS=(15,67)
- MID: LENGTH=9 POS=(16,19) -> Merchant ID (numeric)
- MNAME: LENGTH=30 POS=(16,48) -> Merchant Name
- MCITY: LENGTH=25 POS=(18,21) -> Merchant City
- MZIP: LENGTH=10 POS=(18,67) -> Merchant Zip
- CONFIRM: LENGTH=1 POS=(21,63) -> Confirm Y/N
  Label: "You are about to add this transaction. Please confirm :"
  Hint: (Y/N) shown at POS=(21,66)
- ERRMSG: COLOR=RED POS=(23,1)
FUNCTION KEYS: ENTER=Continue F3=Back F4=Clear F5=Copy Last Tran.
F4=Clear: reset all fields to empty
F5=Copy Last Tran: call POST /api/transactions/copy {cardNumber} to prefill form
SUBMIT FLOW: All fields filled -> Confirm=Y -> POST /api/transactions -> show success with Tran ID
"""
        }

        specific_context = field_context.get(stem, "")

        prompt = f"""You are an expert mainframe modernization engineer converting CICS BMS mapsets to React components.

Convert the following BMS mapset to a complete, working React functional component.

BMS FILENAME: {filename}
COMPONENT NAME: {component_name}
REST API ENDPOINT: {api_endpoint}

BMS SOURCE (exact screen layout):
{bms_source}

SPECIFIC FIELD MAPPING FOR THIS SCREEN:
{specific_context}

COBOL BUSINESS LOGIC (for validation reference):
{cobol_source[:1500] if cobol_source else "Not provided"}

STRICT RULES:

0. COMPONENT NAME: {component_name}
   export default {component_name};

1. IMPORTS (required):
   import React, {{ useState, useEffect }} from 'react';
   import {{ useNavigate, useParams }} from 'react-router-dom';
   import api from '../services/api';
   CRITICAL: NEVER import or use BrowserRouter in page components.
   BrowserRouter exists ONLY in App.jsx. Page components use useNavigate() hook.
   WRONG: import {{ BrowserRouter }} from 'react-router-dom';
   RIGHT:  import {{ useNavigate }} from 'react-router-dom';

2. STATE VARIABLES — one per input field:
   const [userId, setUserId] = useState('');
   const [password, setPassword] = useState('');
   const [errorMsg, setErrorMsg] = useState('');
   const [loading, setLoading] = useState(false);

3. BMS FIELD -> HTML MAPPING:
   ATTRB=(UNPROT) = <input> user can type
   ATTRB=(DRK) = <input type="password">
   ATTRB=(NUM,UNPROT) = <input type="number">
   ATTRB=(ASKIP) or (PROT) = <span> display only
   ATTRB=(IC) = autoFocus prop
   LENGTH(n) = maxLength={{n}}
   COLOR=GREEN = class "terminal-input"
   COLOR=RED = class "terminal-error"
   COLOR=YELLOW = class "terminal-title"
   COLOR=TURQUOISE = class "terminal-label"
   COLOR=BLUE = class "terminal-display"

4. LAYOUT — reproduce 3270 screen faithfully:
   - Header row 1: Tran name (left) | Title01 (center) | Date (right)
   - Header row 2: Prog name (left) | Title02 (center) | Time (right)
   - Main content matching BMS field positions
   - Error message near bottom (red)
   - Function key bar at very bottom (yellow)

5. STYLING — all inline or style object, NO external CSS imports except index.css:
   const styles = {{
     screen: {{ background: '#000033', color: '#00ff00', fontFamily: 'Courier New, monospace',
               minHeight: '100vh', padding: '8px' }},
     header: {{ display: 'flex', justifyContent: 'space-between', color: '#4488ff' }},
     title: {{ color: '#ffff00', textAlign: 'center' }},
     label: {{ color: '#00ffff' }},
     input: {{ background: 'transparent', border: 'none', borderBottom: '1px solid #00ff00',
              color: '#00ff00', fontFamily: 'inherit', outline: 'none', padding: '0 4px' }},
     error: {{ color: '#ff0000', fontWeight: 'bold' }},
     fkeyBar: {{ color: '#ffff00', borderTop: '1px solid #444', paddingTop: '4px', marginTop: '8px' }},
   }}

6. API CALLS — use EXACT method names, NEVER use api.get() or api.post() directly:
   api.auth.login(userId, password)          -> POST /api/auth/login
   api.auth.logout()                         -> POST /api/auth/logout
   api.menu.post(commArea)                   -> POST /api/menu (load menu)
   api.menu.select(optionNum, commArea)      -> POST /api/menu/select
   api.transactions.list(pageNum)            -> GET /api/transactions?page=N
   api.transactions.get(tranId)              -> GET /api/transactions/:id
   api.transactions.add(formData)            -> POST /api/transactions
   api.transactions.copy(cardNumber)         -> POST /api/transactions/copy
   api.session.getCommArea()                 -> reads from localStorage
   api.session.saveCommArea(commArea)        -> saves to localStorage

   CRITICAL API RESPONSE STRUCTURE — ApiResponse fields are TOP LEVEL:
     result.success    (boolean) — NOT result.data.success
     result.message    (string)  — NOT result.data.message
     result.redirect   (string)  — NOT result.data.redirect
     result.commArea   (object)  — NOT result.data.commArea
     result.data       (object)  — contains page-specific data

   MENU PAGE SPECIFIC:
     result.data.transactionName  (NOT trnName)
     result.data.programName      (NOT pgmName)
     result.data.menuOptions      (NOT options, NOT menuOptionTexts)
     result.data.currentDate
     result.data.currentTime
     result.data.errorMessage

   TRANSACTION LIST SPECIFIC:
     result.data.transactions     (array of items — NOT result.data itself)
     result.data.hasNextPage      (boolean)
     result.data.pageNum
     Each item: tranId, tranDate, tranDesc, tranAmt
     WRONG: setTransactions(result.data || [])
     RIGHT:  setTransactions(result.data?.transactions || [])
     WRONG: setTotalPages(result.totalPages || 1)
     RIGHT:  setTotalPages(result.data?.hasNextPage ? pageNum + 1 : pageNum)
     WRONG: transaction.description    RIGHT: transaction.tranDesc
     WRONG: transaction.amount         RIGHT: transaction.tranAmt
     WRONG: setErrorMsg(result.message) on every result
     RIGHT:  if (!result.success) setErrorMsg(result.message)
   TRANSACTION LIST COLUMN SPACING — always add paddingLeft to date column:
     colTranId: {{ width: '160px', paddingLeft: '8px', overflow: 'hidden' }}
     colDate:   {{ width: '80px',  paddingLeft: '12px' }}
     colDesc:   {{ width: '220px' }}
     colAmount: {{ width: '110px', textAlign: 'right' }}

   TRANSACTION VIEW SPECIFIC (TransactionViewResponse fields):
     result.data.tranId           (NOT transactionId)
     result.data.cardNum          (NOT cardNumber)
     result.data.tranTypeCd       (NOT typeCode)
     result.data.tranCatCd        (NOT categoryCode)
     result.data.tranSource       (NOT source)
     result.data.tranDesc         (NOT description)
     result.data.tranAmt          (NOT amount)
     result.data.tranOrigTs       (NOT origDate)
     result.data.tranProcTs       (NOT procDate)
     result.data.merchantId
     result.data.merchantName
     result.data.merchantCity
     result.data.merchantZip

   MENU NAVIGATION — always use routeMap to convert COBOL names to React routes:
     const routeMap = {{
       'COTRN00C': '/transactions',
       'COTRN01C': '/transactions',
       'COTRN02C': '/transactions/add',
       'COSGN00C': '/login',
       '/api/transactions': '/transactions',
       '/api/transactions/add': '/transactions/add',
     }};
     const route = routeMap[result.redirect] || '/menu';
     navigate(route);

   ALWAYS check only result.success (not result.data):
     WRONG: if (result.data && result.success)
     RIGHT:  if (result.success)

   NEVER show errorMsg on success:
     WRONG: setErrorMsg(result.message)  <- shown even on success
     RIGHT:  if (!result.success) setErrorMsg(result.message)

   LOGIN navigation — always go to /menu (menu handles access control):
     WRONG: if (result.userType === "admin") navigate("/admin")
     RIGHT:  navigate("/menu")

7. KEYBOARD SHORTCUTS:
   - Enter key submits form (onKeyDown for PF keys)
   - F3 key -> navigate back
   - F7 key -> previous page
   - F8 key -> next page
   - F4 key -> clear form
   - F5 key -> copy last tran / browse

8. REAL-TIME CLOCK: Show current date/time in header updating every second
   useEffect(() => {{
     const timer = setInterval(() => setCurrentTime(new Date()), 1000);
     return () => clearInterval(timer);
   }}, []);

9. COMMAREA SESSION:
   - Read on mount: const commArea = api.session.getCommArea();
   - Pass in requests: await api.menu.select(option, commArea)
   - Save after login: api.session.saveCommArea(result.commArea)
   - CRITICAL: CommArea userId field is cdemoUserId (NOT userId):
     WRONG: commArea?.userId       RIGHT: commArea?.cdemoUserId
     WRONG: commArea.userId        RIGHT: commArea.cdemoUserId

Return ONLY the React JSX code.
No explanation, no markdown, no backtick blocks.
Start with import statements, end with: export default {component_name};
"""
        return self._call_api(prompt, f"BMS {filename} -> React {component_name}")

    # -----------------------------------------------------------------------
    # Generate React API Service
    # -----------------------------------------------------------------------
    def generate_api_service(self) -> str:
        prompt = """You are an expert React developer creating an API service layer.

Create api.js that calls the CardDemo Spring Boot REST API at http://localhost:8080

ENDPOINTS:
  POST /api/auth/login          body: {userId, password}
  POST /api/auth/logout
  GET  /api/auth/screen
  GET  /api/menu
  POST /api/menu                body: commArea
  POST /api/menu/select         body: {option, commArea}
  GET  /api/transactions        query: ?page=1
  GET  /api/transactions/:id
  GET  /api/transactions/add
  POST /api/transactions        body: transaction fields
  POST /api/transactions/select body: {tranId, commArea}
  POST /api/transactions/copy   body: {cardNumber}

RULES:
1. Use fetch() — no axios
2. Export default api object
3. Each method is async, returns parsed JSON, throws on error
4. Include error handling: if (!response.ok) throw new Error(data.message)
5. Session helpers using localStorage:
   getCommArea() -> JSON.parse(localStorage.getItem('commArea')) || null
   saveCommArea(commArea) -> localStorage.setItem('commArea', JSON.stringify(commArea))
   clearCommArea() -> localStorage.removeItem('commArea')
6. Console log requests for debugging

STRUCTURE:
const BASE_URL = 'http://localhost:8080';

const api = {
  auth: { login, logout, getScreen },
  menu: { get, select },
  transactions: { list, get, add, select, copy, getAddForm },
  session: { getCommArea, saveCommArea, clearCommArea }
};

export default api;

Return ONLY JavaScript. No explanation, no markdown.
"""
        return self._call_api(prompt, "React api.js")

    # -----------------------------------------------------------------------
    # Generate App.jsx with routing
    # -----------------------------------------------------------------------
    def generate_app_jsx(self) -> str:
        prompt = """Create App.jsx for CardDemo React frontend.

ROUTES:
  / -> redirect to /login
  /login -> LoginPage
  /menu -> MenuPage (protected)
  /transactions -> TransactionListPage (protected)
  /transactions/add -> TransactionAddPage (protected)
  /transactions/:id -> TransactionViewPage (protected)

RULES:
1. Use react-router-dom v6 (BrowserRouter, Routes, Route, Navigate, Outlet)
2. App.jsx is the ONLY place with BrowserRouter — index.js does NOT have BrowserRouter
3. ProtectedRoute: check api.session.getCommArea(), redirect to /login if null
4. Import all page components from ./pages/
5. Import api from ./services/api
6. Simple navbar: show userId from commArea, current time
   CRITICAL: CommArea field is cdemoUserId NOT userId:
     WRONG: commArea?.userId
     RIGHT:  commArea?.cdemoUserId
   Example navbar — use marginRight style for spacing between user and time:
     <span className="navbar-user" style={{{{marginRight: '12px'}}}}>
       CardDemoUser: {{commArea?.cdemoUserId || 'N/A'}}
     </span>
     <span className="navbar-time">{{currentTime}}</span>
7. Global dark terminal styling applied via className

IMPORTS:
import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import MenuPage from './pages/MenuPage';
import TransactionListPage from './pages/TransactionListPage';
import TransactionViewPage from './pages/TransactionViewPage';
import TransactionAddPage from './pages/TransactionAddPage';
import api from './services/api';

Return ONLY JSX code. No explanation, no markdown.
Start with imports, end with: export default App;
"""
        return self._call_api(prompt, "React App.jsx")

    # -----------------------------------------------------------------------
    # Generate package.json
    # -----------------------------------------------------------------------
    def generate_package_json(self) -> str:
        prompt = """Create package.json for carddemo-frontend React app.

DEPENDENCIES:
- react: ^18.2.0
- react-dom: ^18.2.0
- react-router-dom: ^6.22.0
- react-scripts: 5.0.1

SCRIPTS: start, build, test
PROXY: http://localhost:8080
NAME: carddemo-frontend

Return ONLY the JSON. No explanation, no markdown.
"""
        return self._call_api(prompt, "package.json")

    # -----------------------------------------------------------------------
    # Generate src/index.js entry point
    # -----------------------------------------------------------------------
    def generate_index_js(self) -> str:
        prompt = """Create src/index.js for React 18 app.

RULES:
1. Use ReactDOM.createRoot
2. Import React, ReactDOM, App, index.css
3. DO NOT import or use BrowserRouter here — App.jsx already contains BrowserRouter
4. Render App directly to document.getElementById('root')
5. Wrap only in React.StrictMode

CORRECT EXAMPLE:
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

Return ONLY JavaScript. No explanation, no markdown.
"""
        return self._call_api(prompt, "src/index.js")

    # -----------------------------------------------------------------------
    # Generate public/index.html
    # -----------------------------------------------------------------------
    def generate_index_html(self) -> str:
        prompt = """Create public/index.html for CardDemo React app.

RULES:
1. Standard CRA structure
2. Title: CardDemo - Mainframe Modernization
3. body background: #000033
4. <div id="root"></div>
5. Standard viewport and charset meta tags

Return ONLY HTML. No explanation, no markdown.
"""
        return self._call_api(prompt, "public/index.html")

    # -----------------------------------------------------------------------
    # Generate src/index.css terminal theme
    # -----------------------------------------------------------------------
    def generate_index_css(self) -> str:
        prompt = """Create src/index.css for mainframe terminal themed React app.

THEME: Authentic IBM 3270 mainframe terminal
- Dark navy background #000033
- Green text #00ff00 (primary)
- Blue text #4488ff (labels/display)
- Yellow text #ffff00 (titles/function keys)
- Cyan/turquoise text #00ffff (instructions)
- Red text #ff0000 (errors)
- Monospace font: Courier New

CSS CLASSES NEEDED:
* { box-sizing: border-box; }
body { background #000033, color #00ff00, font-family Courier New, margin 0 }
.screen { minHeight 100vh, padding 8px }
.header-row { display flex, justify-between, marginBottom 4px }
.title { color #ffff00 }
.label { color #00ffff }
.display-field { color #4488ff }
.terminal-input { background transparent, border none, borderBottom 1px solid #00ff00,
  color #00ff00, fontFamily inherit, fontSize inherit, outline none }
.terminal-input:focus { borderColor white }
.error-msg { color #ff0000, fontWeight bold, minHeight 1.2em }
.fkey-bar { color #ffff00, borderTop 1px solid #333, marginTop 8px, paddingTop 4px }
.btn { background #000033, border 1px solid #4488ff, color #4488ff,
  cursor pointer, fontFamily inherit, padding 2px 8px, margin 0 4px }
.btn:hover { background #001166 }
.tran-table { width 100%, borderCollapse collapse }
.tran-row { cursor pointer }
.tran-row:hover { background #001144 }
.tran-cell { padding 1px 4px, color #4488ff }
.sel-cell { color #00ff00 }

Return ONLY CSS. No explanation, no markdown.
"""
        return self._call_api(prompt, "src/index.css")

    # -----------------------------------------------------------------------
    # Generate CorsConfig.java for Spring Boot
    # -----------------------------------------------------------------------
    def generate_cors_config(self) -> str:
        prompt = """Create CorsConfig.java for Spring Boot to allow React frontend on port 3000.

PACKAGE: com.carddemo
CLASS: CorsConfig

RULES:
1. @Configuration annotation
2. @Bean WebMvcConfigurer corsConfigurer()
3. Allow origins: http://localhost:3000, http://localhost:3001, http://127.0.0.1:3000
4. Allow methods: GET, POST, PUT, DELETE, OPTIONS
5. Allow all headers: *
6. allowCredentials: true
7. maxAge: 3600
8. Map: /api/**

Return ONLY the Java class. No explanation, no markdown.
"""
        return self._call_api(prompt, "CorsConfig.java")

    # -----------------------------------------------------------------------
    # Generate JUnit Test
    # -----------------------------------------------------------------------
    def generate_junit_test(self, class_name: str, java_source: str, kind: str) -> str:
        """Generates a JUnit 5 test class."""

        prompt = f"""You are an expert Java developer writing JUnit 5 tests for Spring Boot REST controllers.

Write a JUnit 5 test class for the following Java {'DTO' if kind == 'record' else 'REST controller'}.

CLASS NAME: {class_name}
KIND: {kind}
JAVA SOURCE:
{java_source[:3000]}

RULES:
1. Use JUnit 5 (@Test, @BeforeEach, Assertions.*)
2. No package declaration — it will be added automatically
3. IMPORTS — CRITICAL for test classes:
   - import org.junit.jupiter.api.*;
   - Import the controller being tested: import com.carddemo.controllers.ClassName;
   - Import ALL inner classes used from the controller:
       import com.carddemo.controllers.AuthController.LoginRequest;
       import com.carddemo.controllers.AuthController.ApiResponse;
       import com.carddemo.controllers.MenuController.MenuOption;
       import com.carddemo.controllers.TransactionListController.TransactionPage;
       (use whichever are relevant to the controller being tested)
   - Import ALL DTO classes needed:
       import com.carddemo.dto.CardDemoCommArea;
       import com.carddemo.dto.TransactionRecord;
       import com.carddemo.dto.AccountRecord;
       import com.carddemo.dto.CardXrefRecord;
       import com.carddemo.dto.UserSecurityData;
4. For DTO classes:
   - Test field initialization (defaults to "" or 0)
   - Test field assignment and retrieval
5. For REST controllers:
   - Instantiate controller directly: AuthController controller = new AuthController();
   - Call endpoint methods directly and check response
   - Test happy path — valid input returns success=true
   - Test validation failures return error message
   - Test not found returns error message
6. Use descriptive test method names
7. Keep tests simple — no Spring context needed, no MockMvc
8. NEVER define any DTO class (CardDemoCommArea, TransactionRecord etc) at the bottom
   of the test file — they already exist in com.carddemo.dto, just import them
   WRONG: class CardDemoCommArea {{ public String cdemoUserId; }}  <- never do this
   RIGHT: import com.carddemo.dto.CardDemoCommArea;                <- always import

9. EXACT FIELD NAMES — use these in tests, never guess:
   CRITICAL — inner class field distinctions:
   ApiResponse fields: success, message (NOT errorMessage), data, redirect, commArea
     WRONG: response.errorMessage    RIGHT: response.message
   MenuResponse fields: title01, title02, transactionName, programName,
     currentDate, currentTime, menuOptions, errorMessage (MenuResponse HAS errorMessage)
     WRONG: menuResponse.message     RIGHT: menuResponse.errorMessage
   TransactionRecord.tranAmt is BigDecimal (PIC S9(09)V99):
     WRONG: record.tranAmt = "100.50"              RIGHT: record.tranAmt = new BigDecimal("100.50")
     WRONG: assertEquals("100.50", record.tranAmt) RIGHT: assertEquals(new BigDecimal("100.50"), record.tranAmt)
   AccountRecord.acctCurrBal, acctCreditLimit are BigDecimal:
     WRONG: account.acctCurrBal = "1000.00"        RIGHT: account.acctCurrBal = new BigDecimal("1000.00")
   TransactionAddRequest ALL fields are String (never BigDecimal/int/long):
     WRONG: request.amount = BigDecimal.ZERO        RIGHT: request.amount = "0.00"
     WRONG: request.amount = new BigDecimal("100")  RIGHT: request.amount = "100.00"
   ApiResponse.data is Object — always cast safely:
     WRONG: Map<String,Object> data = apiResponse.data
     RIGHT:  Map<?,?> data = (Map<?,?>) apiResponse.data
     ALWAYS check: assertTrue(apiResponse.data instanceof Map) before casting
   UserSecurityData fields: secUsrId, secUsrPwd, secUsrType, secUsrFname, secUsrLname
     WRONG: user.secUserId    RIGHT: user.secUsrId
     WRONG: user.secUserPwd   RIGHT: user.secUsrPwd
     WRONG: user.secUserType  RIGHT: user.secUsrType

   ApiResponse fields: success, message, data, redirect, commArea
     WRONG: apiResponse.errorMessage   RIGHT: apiResponse.message

   TransactionAddRequest fields: ALL are String type — never use int, long, BigDecimal:
     accountId (String), cardNumber (String), typeCode (String), categoryCode (String),
     source (String), description (String), amount (String), origDate (String),
     procDate (String), merchantId (String), merchantName (String),
     merchantCity (String), merchantZip (String), confirm (String)
     WRONG: request.transactionType    RIGHT: request.typeCode
     WRONG: request.amount = new BigDecimal("100")  RIGHT: request.amount = "100.00"
     WRONG: request.categoryCode = 5001  RIGHT: request.categoryCode = "5001"
     WRONG: request.merchantId = 12345L  RIGHT: request.merchantId = "12345"
     WRONG: assertEquals(new BigDecimal("100"), request.amount)
     RIGHT:  assertEquals("100.00", request.amount)

   TransactionRecord fields:
     tranTypeCd (NOT tranType), tranCatCd, tranId, tranAmt, tranCardNum
     WRONG: record.tranType    RIGHT: record.tranTypeCd

   MenuController.MenuResponse fields (use exactly):
     errorMessage (NOT message), title01, title02, transactionName,
     programName, currentDate, currentTime, menuOptions (List<String>)
     WRONG: response.message      RIGHT: response.errorMessage

   AuthController.SignonScreenData fields (use exactly):
     errorMessage (NOT message), title01, title02, tranName, pgmName,
     curDate, curTime, applId, sysId
     WRONG: screenData.message    RIGHT: screenData.errorMessage

   MenuController.MenuOption fields (use exactly):
     optNum (int), optName, optPgmName, optUsrType
     WRONG: option.optionNum      RIGHT: option.optNum
     WRONG: option.optionName     RIGHT: option.optName

   MenuController.MenuSelectRequest fields:
     option (int NOT String), action (String), commArea
     WRONG: request.option = "5"  RIGHT: request.option = 5

   TransactionViewController.TransactionViewResponse fields:
     tranAmt (String NOT BigDecimal), tranCatCd (int)
     WRONG: assertEquals(new BigDecimal("100"), tran.tranAmt)
     RIGHT:  assertEquals("100.00", tran.tranAmt)

   data field is Object type — cast carefully:
     WRONG: (Map<String,Object>) apiResponse.data
     RIGHT:  (Map<?,?>) apiResponse.data

   NEVER use raw int/long literals for String fields:
     WRONG: request.categoryCode = 5001
     RIGHT:  request.categoryCode = "5001"

Return ONLY the Java test class code. No explanation, no markdown blocks.
"""
        return self._call_api(prompt, f"JUnit test for {class_name}")

    # -----------------------------------------------------------------------
    # Internal API call with retry
    # -----------------------------------------------------------------------
    def _call_api(self, prompt: str, description: str) -> str:
        max_retries = 3
        retry_delay = 30

        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"  API call for {description} (attempt {attempt}/{max_retries})")

                message = self.client.messages.create(
                    model=MODEL,
                    max_tokens=MAX_TOKENS,
                    messages=[{"role": "user", "content": prompt}]
                )

                result = message.content[0].text.strip()
                result = self._strip_code_fences(result)

                logger.info(f"  API call successful — {len(result)} chars returned")
                # Smart truncation check based on file type
                last = result.rstrip()
                is_jsx = any(x in description for x in ["BMS", "React", "api.js", "index.js", "App.jsx"])
                is_other = any(x in description for x in ["index.html", "index.css", "package.json"])
                if not is_jsx and not is_other and not last.endswith("}"):
                    logger.warning(f"  Java output may be truncated — last: {last[-40:]}")
                return result

            except anthropic.RateLimitError:
                logger.warning(f"  Rate limit hit! Waiting {retry_delay}s before retry...")
                time.sleep(retry_delay)
                retry_delay *= 2

            except anthropic.APIError as e:
                logger.error(f"  API error on attempt {attempt}: {e}")
                if attempt < max_retries:
                    time.sleep(self.delay * 2)
                else:
                    logger.error(f"  All retries exhausted for {description}")
                    return None

        return None

    def _strip_code_fences(self, text: str) -> str:
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        return "\n".join(lines)
