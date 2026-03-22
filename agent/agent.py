"""
agent.py (ONLINE VERSION)
-------------------------
Agentic AI Mainframe Modernization Converter
Converts CICS COBOL programs to Spring Boot REST API
using the Claude API (Anthropic).

Processing Order:
  Phase 1: Copybooks (.cpy) -> Java DTO classes     (dto/)
  Phase 2: COBOL     (.cbl) -> Spring Boot REST controllers (controllers/)

Output Structure:
  converted-usingAgent/
    java/
      dto/          <- copybook Java DTO classes
      controllers/  <- CICS COBOL REST controllers
    tests/
      java/
        dto/        <- JUnit tests for DTOs
        controllers/  <- JUnit tests for controllers
    docs/

Usage:
  1. Set ANTHROPIC_API_KEY in .env file
  2. Run: python agent.py --src ./src --out ./converted-usingAgent
"""

import os
import sys
import time
import argparse
import logging
from pathlib import Path
from dotenv import load_dotenv

from file_reader   import FileReader
from converter     import Converter
from file_writer   import FileWriter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("Agent")

RATE_LIMIT_DELAY = 5


def run_agent(src_dir: str, out_dir: str, clean: bool = False):
    load_dotenv()
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        logger.error("ANTHROPIC_API_KEY not found in .env file!")
        sys.exit(1)

    reader    = FileReader(src_dir)
    converter = Converter(api_key, RATE_LIMIT_DELAY)
    writer    = FileWriter(out_dir, clean)

    # ------------------------------------------------------------------
    # Phase 1: Copybooks -> Java DTO classes
    # ------------------------------------------------------------------
    logger.info("=" * 60)
    logger.info("PHASE 1 — COPYBOOKS -> JAVA DTO CLASSES")
    logger.info("=" * 60)

    copybooks = reader.get_copybooks()
    logger.info(f"Found {len(copybooks)} copybook(s): {[f.name for f in copybooks]}")

    copybook_context = {}
    converted_records = {}

    for cpy_file in copybooks:
        class_name = derive_java_class_name(cpy_file.name, "record")
        out_path = Path(out_dir) / "java" / "dto" / f"{class_name}.java"

        if out_path.exists():
            logger.info(f"Skipping {cpy_file.name} — already converted ({class_name}.java exists)")
            source = cpy_file.read_text(encoding="utf-8", errors="replace")
            copybook_context[cpy_file.stem.upper()] = source
            converted_records[cpy_file.stem.upper()] = class_name
            continue

        logger.info(f"Converting copybook: {cpy_file.name}")
        source = cpy_file.read_text(encoding="utf-8", errors="replace")

        java_class = converter.convert_copybook(cpy_file.name, source)

        if java_class:
            writer.write_java_record(class_name, java_class)
            copybook_context[cpy_file.stem.upper()] = source
            converted_records[cpy_file.stem.upper()] = class_name
            logger.info(f"  -> {class_name}.java written to java/dto/")

            logger.info(f"  Generating JUnit test for {class_name}")
            junit_test = converter.generate_junit_test(class_name, java_class, "record")
            if junit_test:
                writer.write_java_test_record(f"{class_name}Test", junit_test)
                logger.info(f"  -> {class_name}Test.java written to tests/java/dto/")
        else:
            logger.warning(f"  Skipped — no output from API for {cpy_file.name}")

        time.sleep(RATE_LIMIT_DELAY)

    # ------------------------------------------------------------------
    # Phase 2: COBOL -> Spring Boot REST Controllers
    # ------------------------------------------------------------------
    logger.info("=" * 60)
    logger.info("PHASE 2 — CICS COBOL -> SPRING BOOT REST CONTROLLERS")
    logger.info("=" * 60)

    cobol_files = reader.get_cobol_files()
    logger.info(f"Found {len(cobol_files)} COBOL file(s): {[f.name for f in cobol_files]}")

    for cbl_file in cobol_files:
        class_name = derive_java_class_name(cbl_file.name, "service")
        out_path = Path(out_dir) / "java" / "controllers" / f"{class_name}.java"

        if out_path.exists():
            logger.info(f"Skipping {cbl_file.name} — already converted ({class_name}.java exists)")
            continue

        logger.info(f"Converting COBOL: {cbl_file.name}")
        source = cbl_file.read_text(encoding="utf-8", errors="replace")

        used_copybooks = find_used_copybooks(source, copybook_context)
        logger.info(f"  Uses copybooks: {list(used_copybooks.keys())}")

        # Load actual generated Java DTO content for exact field names
        java_class_content = {}
        for cpy_stem in used_copybooks.keys():
            java_class_name = converted_records.get(cpy_stem, cpy_stem)
            java_file = Path(out_dir) / "java" / "dto" / f"{java_class_name}.java"
            if java_file.exists():
                java_class_content[java_class_name] = java_file.read_text(encoding="utf-8")
                logger.info(f"  Loaded DTO: {java_class_name}.java")

        java_service = converter.convert_cobol(
            cbl_file.name, source, used_copybooks, converted_records, java_class_content
        )

        if java_service:
            writer.write_java_service(class_name, java_service)
            logger.info(f"  -> {class_name}.java written to java/controllers/")

            logger.info(f"  Generating JUnit test for {class_name}")
            junit_test = converter.generate_junit_test(class_name, java_service, "service")
            if junit_test:
                writer.write_java_test_service(f"{class_name}Test", junit_test)
                logger.info(f"  -> {class_name}Test.java written to tests/java/controllers/")
        else:
            logger.warning(f"  Skipped — no output from API for {cbl_file.name}")

        time.sleep(RATE_LIMIT_DELAY)

    logger.info("=" * 60)
    logger.info("AGENT COMPLETED SUCCESSFULLY")
    logger.info(f"Output written to: {out_dir}")
    logger.info("=" * 60)
    writer.print_summary()


def derive_java_class_name(filename: str, kind: str) -> str:
    stem = Path(filename).stem.upper()

    # Copybook -> DTO class name
    copybook_map = {
        "COCOM01Y": "CardDemoCommArea",
        "CVCUS01Y": "CustomerRecord",
        "CVTRA05Y": "TransactionRecord",
        "CVACT01Y": "AccountRecord",
        "CVACT03Y": "CardXrefRecord",
        "COTTL01Y": "TitleData",
        "CSDAT01Y": "DateData",
        "CSMSG01Y": "MessageData",
        "CSUSR01Y": "UserSecurityData",
    }

    if kind == "record" and stem in copybook_map:
        return copybook_map[stem]

    # COBOL -> Controller class name
    if kind == "service":
        service_map = {
            "COSGN00C": "AuthController",
            "COMEN01C": "MenuController",
            "COTRN00C": "TransactionListController",
            "COTRN01C": "TransactionViewController",
            "COTRN02C": "TransactionAddController",
        }
        if stem in service_map:
            return service_map[stem]
        return stem.title() + "Controller"

    return stem.title().replace("_", "")


def find_used_copybooks(cobol_source: str, copybook_context: dict) -> dict:
    used = {}
    for line in cobol_source.splitlines():
        stripped = line.strip()
        if stripped.startswith("COPY "):
            parts = stripped.replace(".", "").split()
            if len(parts) >= 2:
                cpy_name = parts[1].strip().upper()
                if cpy_name in copybook_context:
                    used[cpy_name] = copybook_context[cpy_name]
    return used


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Agentic CICS COBOL to Spring Boot REST converter")
    parser.add_argument("--src", default="./src",                    help="Source directory")
    parser.add_argument("--out", default="./converted-usingAgent",   help="Output directory")
    parser.add_argument("--clean", action="store_true",              help="Clean output before running")
    args = parser.parse_args()

    run_agent(args.src, args.out, args.clean)
