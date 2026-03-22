# CardDemo Online Modernization — Developer README

**Project:** AWS CardDemo Online CICS Modernization  
**Repo:** https://github.com/ugvenkat/carddemo-online  
**Source:** https://github.com/aws-samples/aws-mainframe-modernization-carddemo (Apache 2.0)  
**Author:** ugvenkat  
**Last Updated:** March 2026

---

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [Architecture](#2-architecture)
3. [What Each Controller Does](#3-what-each-controller-does)
4. [Repository Structure](#4-repository-structure)
5. [Prerequisites](#5-prerequisites)
6. [Quick Start](#6-quick-start)
7. [Running the Agentic AI Converter](#7-running-the-agentic-ai-converter)
8. [Building and Running the Spring Boot App](#8-building-and-running-the-spring-boot-app)
9. [Testing All REST Endpoints](#9-testing-all-rest-endpoints)
10. [Troubleshooting](#10-troubleshooting)
11. [Key Technical Notes](#11-key-technical-notes)

---

## 1. Project Overview

This project modernizes the **online (CICS)** portion of the AWS CardDemo mainframe application from:

| From (Mainframe) | To (Modern) |
|---|---|
| CICS COBOL programs (`.cbl`) | Spring Boot REST API controllers |
| COBOL copybooks (`.cpy`) | Java DTO classes |
| BMS mapsets (`.bms`) | JSON request/response objects |
| CICS COMMAREA | `CardDemoCommArea` session object |
| CICS VSAM file I/O | In-memory `HashMap` simulation |

The result is a fully functional **Spring Boot REST API** running on port 8080 that mirrors all the business logic of the original CICS screens.

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    MAINFRAME (Original)                      │
│                                                              │
│  CICS Transaction  COBOL Program    BMS Screen              │
│  ───────────────   ─────────────    ──────────              │
│  CC00           -> COSGN00C     ->  COSGN00 (Login)         │
│  CM00           -> COMEN01C     ->  COMEN01 (Menu)          │
│  CT00           -> COTRN00C     ->  COTRN00 (Tran List)     │
│  CT01           -> COTRN01C     ->  COTRN01 (Tran View)     │
│  CT02           -> COTRN02C     ->  COTRN02 (Tran Add)      │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ Modernization via Agentic AI
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                 MODERN (Spring Boot REST API)                │
│                                                              │
│  REST Endpoint              Controller          DTO          │
│  ─────────────              ──────────          ───          │
│  POST /api/auth/login    -> AuthController   -> LoginRequest │
│  GET  /api/menu          -> MenuController   -> CardDemoCommArea │
│  GET  /api/transactions  -> TranListController-> TransactionRecord │
│  GET  /api/transactions/{id}-> TranViewController            │
│  POST /api/transactions  -> TranAddController -> AddRequest  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                 CICS to REST Mapping                         │
│                                                              │
│  CICS Concept              REST Equivalent                   │
│  ─────────────             ───────────────                   │
│  EXEC CICS RECEIVE MAP  -> @PostMapping / request body       │
│  EXEC CICS SEND MAP     -> ResponseEntity<ApiResponse>       │
│  EXEC CICS READ         -> HashMap.get(key)                  │
│  EXEC CICS WRITE        -> HashMap.put(key, record)          │
│  EXEC CICS STARTBR/     -> ArrayList pagination              │
│    READNEXT/ENDBR                                            │
│  EXEC CICS XCTL         -> "redirect" field in response      │
│  DFHCOMMAREA            -> CardDemoCommArea object           │
│  EIBAID DFHENTER        -> POST request                      │
│  EIBAID DFHPF3          -> "action: back" / GET endpoint     │
│  EIBAID DFHPF7/PF8      -> page prev/next parameters         │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                 AGENTIC AI CONVERTER                         │
│                                                              │
│  src/ (CICS COBOL source)                                    │
│         │                                                    │
│         ▼                                                    │
│  agent/agent.py (orchestrator)                               │
│         │                                                    │
│         ├── Phase 1: Copybooks -> Java DTO classes           │
│         └── Phase 2: COBOL    -> Spring Boot controllers     │
│                                                              │
│         ▼                                                    │
│  converted-usingAgent/                                       │
│    java/dto/          (9 Java DTO classes)                   │
│    java/controllers/  (5 Spring Boot controllers)            │
│    tests/             (JUnit 5 tests)                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. What Each Controller Does

### AuthController (from COSGN00C.cbl)
**CICS Transaction:** CC00 — Sign-on Screen  
**Endpoints:**
- `GET  /api/auth/screen` — Returns empty signon screen data
- `POST /api/auth/login`  — Authenticates user, returns session commArea
- `POST /api/auth/logout` — Logs out, returns thank-you message

**Business Logic:**
- Validates userId and password are not empty
- Looks up user in `UserSecurityData` HashMap (simulates USRSEC VSAM file)
- Returns `redirect: COADM01C` for admin users, `redirect: COMEN01C` for regular users
- Populates `CardDemoCommArea` with userId, userType, fromTranId

**Sample Users (hardcoded in-memory):**

| userId | password | userType |
|---|---|---|
| `USER0001` | `USER1234` | `U` (Regular) |
| `ADMIN001` | `ADMIN123` | `A` (Admin) |

---

### MenuController (from COMEN01C.cbl)
**CICS Transaction:** CM00 — Main Menu  
**Endpoints:**
- `GET  /api/menu`        — Returns menu (requires commArea session)
- `POST /api/menu`        — Returns menu with commArea in request body
- `POST /api/menu/select` — Selects a menu option, returns redirect

**Business Logic:**
- Requires authenticated `CardDemoCommArea` session (returns 401 if missing)
- Returns list of menu options with program names and user type restrictions
- Admin options only accessible when `commArea.isAdmin() = true`
- Regular user options accessible when `commArea.isRegularUser() = true`

---

### TransactionListController (from COTRN00C.cbl)
**CICS Transaction:** CT00 — Transaction List  
**Endpoints:**
- `GET  /api/transactions`         — Lists transactions (10 per page)
- `GET  /api/transactions?page=2`  — Page 2 of transactions
- `POST /api/transactions/select`  — Selects a transaction, returns redirect to view

**Business Logic:**
- Reads TRANSACT VSAM file sequentially (simulated as sorted HashMap)
- Shows 10 transactions per page (matching original BMS screen)
- Supports forward (PF8) and backward (PF7) paging
- Formats amounts and dates for display

---

### TransactionViewController (from COTRN01C.cbl)
**CICS Transaction:** CT01 — Transaction View  
**Endpoints:**
- `GET /api/transactions/{id}` — Returns full transaction details

**Business Logic:**
- Reads single transaction by ID from TRANSACT VSAM file
- Returns all transaction fields: ID, card number, type, category, source, amount, dates, merchant info
- Returns 404 if transaction not found

---

### TransactionAddController (from COTRN02C.cbl)
**CICS Transaction:** CT02 — Transaction Add  
**Endpoints:**
- `GET  /api/transactions/add`   — Returns empty add form with header info
- `POST /api/transactions`       — Validates and adds new transaction
- `POST /api/transactions/copy`  — Copies last transaction as template

**Business Logic:**
- Validates account ID or card number (looks up in CCXREF VSAM)
- Validates all required fields are non-empty
- Validates amount format, date format (YYYY-MM-DD)
- Validates merchant ID is numeric
- Requires confirm=Y to actually write the transaction
- Auto-generates next transaction ID (max existing + 1)
- `TRAN-TYPE-CD` is **alphabetic** (e.g. `PU`, `SA`) — NOT numeric

---

## 4. Repository Structure

```
carddemo-online/
├── src/                              ← ORIGINAL MAINFRAME SOURCE
│   ├── cobol/
│   │   ├── COMEN01C.cbl              ← Main Menu (CICS)
│   │   ├── COSGN00C.cbl              ← Sign-on Screen (CICS)
│   │   ├── COTRN00C.cbl              ← Transaction List (CICS)
│   │   ├── COTRN01C.cbl              ← Transaction View (CICS)
│   │   └── COTRN02C.cbl              ← Transaction Add (CICS)
│   └── copybooks/
│       ├── COCOM01Y.cpy              ← COMMAREA (session context)
│       ├── CVCUS01Y.cpy              ← Customer record
│       ├── CVTRA05Y.cpy              ← Transaction record
│       ├── CVACT01Y.cpy              ← Account record
│       ├── CVACT03Y.cpy              ← Card xref record
│       ├── COTTL01Y.cpy              ← Screen title data
│       ├── CSDAT01Y.cpy              ← Date working storage
│       ├── CSMSG01Y.cpy              ← Message working storage
│       ├── CSUSR01Y.cpy              ← User security data
│       ├── COMEN01.bms               ← BMS mapset (screen layout)
│       ├── COSGN00.bms               ← BMS mapset
│       ├── COTRN00.bms               ← BMS mapset
│       ├── COTRN01.bms               ← BMS mapset
│       └── COTRN02.bms               ← BMS mapset
│
├── converted-usingAgent/             ← AGENT-GENERATED OUTPUT
│   ├── java/
│   │   ├── dto/                      ← 9 Java DTO classes
│   │   │   ├── CardDemoCommArea.java  ← Session context (COMMAREA)
│   │   │   ├── TransactionRecord.java
│   │   │   ├── AccountRecord.java
│   │   │   ├── CardXrefRecord.java
│   │   │   ├── CustomerRecord.java
│   │   │   ├── UserSecurityData.java
│   │   │   ├── TitleData.java
│   │   │   ├── DateData.java
│   │   │   └── MessageData.java
│   │   └── controllers/              ← 5 Spring Boot controllers
│   │       ├── AuthController.java
│   │       ├── MenuController.java
│   │       ├── TransactionListController.java
│   │       ├── TransactionViewController.java
│   │       └── TransactionAddController.java
│   └── tests/
│       └── java/
│           ├── dto/                  ← JUnit 5 DTO tests
│           └── controllers/          ← JUnit 5 controller tests
│
├── src/main/java/com/carddemo/       ← MAVEN PROJECT SOURCE
│   ├── CardDemoApplication.java      ← Spring Boot main class
│   ├── dto/                          ← DTO classes (copied from above)
│   └── controllers/                  ← Controllers (copied from above)
│
├── src/test/java/com/carddemo/       ← MAVEN TEST SOURCE
│   ├── dto/
│   └── controllers/
│
├── agent/                            ← AGENTIC AI CONVERTER
│   ├── agent.py                      ← Main orchestrator
│   ├── converter.py                  ← Claude API prompts
│   ├── file_reader.py                ← Reads src/ files
│   ├── file_writer.py                ← Writes output files
│   ├── requirements.txt              ← Python dependencies
│   └── .env                          ← API key (NOT in git)
│
├── pom.xml                           ← Maven build file
├── DEV_README.md                     ← This file
└── .gitignore
```

---

## 5. Prerequisites

| Software | Version | Download |
|---|---|---|
| Java JDK | 17 (LTS) | https://www.oracle.com/java/technologies/downloads/#java17-windows |
| Maven | 3.8+ | https://maven.apache.org/download.cgi |
| Python | 3.8+ | https://www.python.org/downloads/ |
| Git | Latest | https://git-scm.com/downloads |

### Verify Installation
```cmd
java -version
mvn --version
python --version
git --version
```

---

## 6. Quick Start

### Step 1 — Clone the Repository
```cmd
cd C:\Study
git clone https://github.com/ugvenkat/carddemo-online.git
cd carddemo-online
```

### Step 2 — Build the Project
```cmd
mvn compile
```

### Step 3 — Run the Application
```cmd
mvn spring-boot:run
```

Wait for:
```
Started CardDemoApplication in X.XXX seconds
Tomcat started on port(s): 8080
```

### Step 4 — Test Login (new PowerShell window)
```powershell
$body = '{"userId":"USER0001","password":"USER1234"}'
Invoke-RestMethod -Uri "http://localhost:8080/api/auth/login" -Method POST -ContentType "application/json" -Body $body
```

Expected: `success: True`, `redirect: COMEN01C`

---

## 7. Running the Agentic AI Converter

Use this to regenerate all `converted-usingAgent/` files from scratch.

### Step 1 — Get a Claude API Key
1. Go to https://console.anthropic.com
2. Sign in → **API Keys** → **Create Key**
3. Copy key (starts with `sk-ant-api03-...`)

### Step 2 — Create .env File
```cmd
cd C:\Study\carddemo-online\agent
python -c "
key = input('Paste your Claude API key: ')
with open('.env', 'w', encoding='utf-8') as f:
    f.write(f'ANTHROPIC_API_KEY={key}\n')
print('Done!')
"
```

> ⚠️ **NEVER commit `.env` to git!**

### Step 3 — Install Python Dependencies
```cmd
pip install -r requirements.txt
```

### Step 4 — Run the Agent
```cmd
cd C:\Study\carddemo-online\agent
python agent.py --src ..\src --out ..\converted-usingAgent --clean
```

Expected output: **28 files written** (9 DTOs + 9 DTO tests + 5 controllers + 5 controller tests)

### Step 5 — Copy to Maven Structure
```cmd
cd C:\Study\carddemo-online

copy /Y converted-usingAgent\java\dto\*.java         src\main\java\com\carddemo\dto\
copy /Y converted-usingAgent\java\controllers\*.java  src\main\java\com\carddemo\controllers\
copy /Y converted-usingAgent\tests\java\dto\*.java         src\test\java\com\carddemo\dto\
copy /Y converted-usingAgent\tests\java\controllers\*.java src\test\java\com\carddemo\controllers\
```

### Step 6 — Build
```cmd
mvn compile
```

---

## 8. Building and Running the Spring Boot App

### Build Only
```cmd
mvn compile
```

### Run Tests
```cmd
mvn test
```

### Run Application
```cmd
mvn spring-boot:run
```

### Build JAR
```cmd
mvn package
java -jar target/carddemo-online-1.0.0.jar
```

### Application runs on
```
http://localhost:8080
```

---

## 9. Testing All REST Endpoints

### Complete Test Flow (PowerShell)

```powershell
# ============================================================
# Step 1: Login as regular user
# ============================================================
$loginBody = '{"userId":"USER0001","password":"USER1234"}'
$loginResult = Invoke-RestMethod -Uri "http://localhost:8080/api/auth/login" `
    -Method POST -ContentType "application/json" -Body $loginBody

Write-Host "Login:" $loginResult.success $loginResult.redirect
# Expected: success=True, redirect=COMEN01C

# ============================================================
# Step 2: Get Main Menu (pass commArea from login)
# ============================================================
$commArea = $loginResult.commArea | ConvertTo-Json
$menuResult = Invoke-RestMethod -Uri "http://localhost:8080/api/menu" `
    -Method POST -ContentType "application/json" -Body $commArea

Write-Host "Menu:" $menuResult.success
Write-Host "Title:" $menuResult.data.title01
# Expected: success=True, title includes "AWS Mainframe Modernization"

# ============================================================
# Step 3: List Transactions
# ============================================================
$tranList = Invoke-RestMethod -Uri "http://localhost:8080/api/transactions" -Method GET
Write-Host "Transactions:" $tranList.data.transactions.Count
$tranList.data.transactions
# Expected: 10 transactions with IDs, amounts, dates

# ============================================================
# Step 4: View a Transaction
# ============================================================
$tranView = Invoke-RestMethod -Uri "http://localhost:8080/api/transactions/0000000000000001" `
    -Method GET
Write-Host "Transaction ID:" $tranView.data.tranId
Write-Host "Amount:" $tranView.data.tranAmt
# Expected: full transaction details

# ============================================================
# Step 5: Add a New Transaction
# ============================================================
$addBody = '{
  "cardNumber":"4111111111111111",
  "typeCode":"PU",
  "categoryCode":"5001",
  "source":"ONLINE",
  "description":"Test Purchase from REST API",
  "amount":"100.00",
  "merchantId":"12345678901",
  "merchantName":"TEST MERCHANT",
  "merchantCity":"DALLAS",
  "merchantZip":"75001",
  "origDate":"2026-03-22",
  "procDate":"2026-03-22",
  "confirm":"Y"
}'
$addResult = Invoke-RestMethod -Uri "http://localhost:8080/api/transactions" `
    -Method POST -ContentType "application/json" -Body $addBody

Write-Host "Add Transaction:" $addResult.success $addResult.message
# Expected: success=True, message includes new Tran ID

# ============================================================
# Step 6: Login as Admin
# ============================================================
$adminBody = '{"userId":"ADMIN001","password":"ADMIN123"}'
$adminResult = Invoke-RestMethod -Uri "http://localhost:8080/api/auth/login" `
    -Method POST -ContentType "application/json" -Body $adminBody

Write-Host "Admin Login:" $adminResult.success $adminResult.redirect
# Expected: success=True, redirect=COADM01C

# ============================================================
# Step 7: Logout
# ============================================================
$logoutResult = Invoke-RestMethod -Uri "http://localhost:8080/api/auth/logout" `
    -Method POST -ContentType "application/json" -Body '{}'
Write-Host "Logout:" $logoutResult.message
# Expected: Thank you message
```

### Expected Results Summary

| Test | Endpoint | Expected |
|---|---|---|
| Login (user) | POST /api/auth/login | success=True, redirect=COMEN01C |
| Login (admin) | POST /api/auth/login | success=True, redirect=COADM01C |
| Login (wrong pwd) | POST /api/auth/login | success=False, "Wrong Password" |
| Login (not found) | POST /api/auth/login | success=False, "User not found" |
| Main Menu | POST /api/menu | success=True, menu options returned |
| Menu (no session) | GET /api/menu | 401 Unauthorized |
| Transaction List | GET /api/transactions | 10 transactions, page info |
| Transaction View | GET /api/transactions/0000000000000001 | Full transaction details |
| Transaction View (bad ID) | GET /api/transactions/BADID | 404 Not Found |
| Add Transaction | POST /api/transactions | success=True, new Tran ID |
| Add (missing field) | POST /api/transactions | 400, field error message |

---

## 10. Troubleshooting

### `mvn compile` fails — package javax.annotation
**Fix:** The generated files use `jakarta.annotation`. Run:
```cmd
python fix_imports.py
```
Or search for `javax.annotation` and replace with `jakarta.annotation` in all controller files.

### `mvn compile` fails — cannot find symbol CardDemoCommArea
**Fix:** DTO imports missing from controllers. Run:
```cmd
python fix_imports.py
```

### `mvn compile` fails — incompatible types CardDemoCommArea
**Fix:** A test or controller has redefined `CardDemoCommArea` as an inner class. Search for `class CardDemoCommArea` in controller/test files and remove the local definition.

### `mvn compile` fails — cannot find symbol LoginRequest
**Fix:** Inner class imports missing from tests. Run:
```cmd
python fix_test_imports.py
```

### Spring Boot won't start — port 8080 in use
**Fix:**
```cmd
# Find and kill the process using port 8080
netstat -ano | findstr :8080
taskkill /PID <PID> /F
```

### Login returns 401
**Fix:** Use exact credentials: `USER0001`/`USER1234` or `ADMIN001`/`ADMIN123`

### Add Transaction returns "Type CD must be Numeric"
**Fix:** `typeCode` must be alphabetic like `PU` or `SA` — not `01` or `02`.
The original COBOL `TRAN-TYPE-CD` is `PIC X(02)` (alphanumeric).

### Agent fails — credit balance too low
**Fix:** Add credits at https://console.anthropic.com/settings/billing

### After running agent — package declarations missing
**Fix:** Package declarations are now added automatically by the agent.
If you see this error, ensure you are using the latest converter.py from the agent/ folder.

---

## 11. Key Technical Notes

### CICS to REST Mapping

| CICS Concept | Java/REST Equivalent |
|---|---|
| `EXEC CICS RECEIVE MAP` | `@PostMapping` with `@RequestBody` |
| `EXEC CICS SEND MAP` | `return ResponseEntity.ok(response)` |
| `EXEC CICS READ DATASET` | `HashMap.get(key)` |
| `EXEC CICS WRITE DATASET` | `HashMap.put(key, record)` |
| `EXEC CICS STARTBR/READNEXT/ENDBR` | Sorted `ArrayList` with pagination |
| `EXEC CICS XCTL PROGRAM(x)` | `response.redirect = "ProgramName"` |
| `EXEC CICS RETURN TRANSID COMMAREA` | Return `ResponseEntity` with `commArea` |
| `DFHCOMMAREA` | `CardDemoCommArea` request/response object |
| `EIBCALEN = 0` | First call / no session |
| `EIBAID = DFHENTER` | POST request |
| `EIBAID = DFHPF3` | Back navigation / `action=back` |
| `EIBAID = DFHPF7` | Previous page |
| `EIBAID = DFHPF8` | Next page |
| `DFHRESP(NORMAL)` | HTTP 200 / map.get() != null |
| `DFHRESP(NOTFND)` | HTTP 404 / map.get() == null |
| `DFHRESP(ENDFILE)` | End of list |

### COBOL PIC Type Mappings

| COBOL PIC | Java Type | Notes |
|---|---|---|
| `PIC X(n)` | `String` | Initialized to `""` |
| `PIC 9(n)` n≤4 | `int` | Initialized to `0` |
| `PIC 9(n)` n>4 | `long` | Initialized to `0L` |
| `PIC S9(n)V99` | `BigDecimal` | Initialized to `BigDecimal.ZERO` |
| `FILLER` | (skipped) | Not mapped |

### Important Field Types in COTRN02C

| COBOL Field | PIC | Java | Valid Values |
|---|---|---|---|
| `TRAN-TYPE-CD` | `X(02)` | `String` | `"PU"`, `"SA"`, `"CR"` — **NOT numeric** |
| `TRAN-CAT-CD` | `9(04)` | `int` | `5001`, `5002` etc |
| `TRAN-CARD-NUM` | `X(16)` | `String` | `"4111111111111111"` |
| `TRAN-MERCHANT-ID` | `9(09)` | `long` | `12345678901` |

### CardDemoCommArea (COMMAREA)
The session context object passed between all CICS programs — now passed as JSON in REST requests/responses:

```json
{
  "cdemoFromTranid": "CC00",
  "cdemoFromProgram": "COSGN00C",
  "cdemoUserId": "USER0001",
  "cdemoUserType": "U",
  "cdemoPgmContext": 0
}
```

Helper methods (call with parentheses):
- `commArea.isAdmin()` — returns `true` if `cdemoUserType = "A"`
- `commArea.isRegularUser()` — returns `true` if `cdemoUserType = "U"`

---

*This project is based on the AWS CardDemo open source application, licensed under Apache 2.0.*  
*Original source: https://github.com/aws-samples/aws-mainframe-modernization-carddemo*
