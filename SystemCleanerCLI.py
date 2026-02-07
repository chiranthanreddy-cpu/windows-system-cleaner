import os
import platform
import argparse
import logging
from pathlib import Path
from cleaner_engine import CleanerEngine

# CLI-specific logging (The CLI is the entry point here)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    parser = argparse.ArgumentParser(description="Windows System Cleaner - Automation Tool")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be deleted without actually deleting")
    args = parser.parse_args()

    engine = CleanerEngine()

    if platform.system() != "Windows":
        logging.error("This script is designed for Windows only.")
        return

    logging.info("--- Windows System Cleaner v1.5 (Professional) ---")
    if args.dry_run:
        logging.info("!!! DRY RUN MODE ACTIVE !!!")
    
    if not engine.is_admin:
        logging.info("Note: Run as Administrator for full system access.")

    # Scan
    results = engine.scan(lambda m: logging.info(m))
    
    if not results:
        logging.info("No items found to clean.")
        return

    total_size = sum(item['size'] for item in results)
    logging.info(f"\nScan complete. Found {len(results)} items ({engine.format_bytes(total_size)})")

    if args.dry_run:
        logging.info("[DRY RUN] No files were touched.")
    else:
        # For CLI, we clean everything found (no manual review step yet)
        deleted_count, cleared_size = engine.clean(results, lambda m: logging.info(m))
        logging.info(f"\n--- Summary ---")
        logging.info(f"Items Trashed: {deleted_count}")
        logging.info(f"Space Reclaimed: {engine.format_bytes(cleared_size)}")
    
    logging.info("Cleanup session finished.")

if __name__ == "__main__":
    main()