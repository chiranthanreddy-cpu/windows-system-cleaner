import os
import platform
import argparse
import logging
from cleaner_engine import CleanerEngine

# Setup logging
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "cleanup.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

def main():
    parser = argparse.ArgumentParser(description="Windows System Cleaner - Automation Tool")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be deleted without actually deleting")
    args = parser.parse_args()

    engine = CleanerEngine()

    if platform.system() != "Windows":
        logging.error("This script is designed for Windows only.")
        return

    logging.info("--- Windows System Cleaner v1.2 (Modular) ---")
    if args.dry_run:
        logging.info("!!! DRY RUN MODE ACTIVE !!!")
    
    if not engine.is_admin:
        logging.info("Note: Run as Administrator to clean System Temp and Prefetch folders.")

    # Logging Wrapper for the engine
    def cli_log(msg):
        logging.info(msg)

    # Scan
    count, size = engine.scan(cli_log)
    
    if args.dry_run:
        logging.info(f"\n[DRY RUN SUMMARY] Would delete {count} items ({engine.format_bytes(size)})")
    else:
        # Clean
        if count > 0:
            deleted_count, cleared_size = engine.clean(cli_log)
            logging.info(f"\n--- Summary ---")
            logging.info(f"Files/Folders Deleted: {deleted_count}")
            logging.info(f"Disk space cleared: {engine.format_bytes(cleared_size)}")
        else:
            logging.info("No files found to clean.")
    
    logging.info("Cleanup session finished.")

if __name__ == "__main__":
    main()
