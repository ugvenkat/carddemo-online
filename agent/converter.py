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
                if result and not result.rstrip().endswith('}'):
                    logger.warning(f"  Output may be truncated — does not end with }}")
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
