import os
import shutil
import ctypes
import platform
import argparse
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("cleanup.log"),
        logging.StreamHandler()
    ]
)

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def get_size(start_path='.'):
    total_size = 0
    try:
        if os.path.isfile(start_path):
            return os.path.getsize(start_path)
        for dirpath, dirnames, filenames in os.walk(start_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if not os.path.islink(fp):
                    total_size += os.path.getsize(fp)
    except Exception:
        pass
    return total_size

def format_bytes(size):
    power = 2**10
    n = 0
    power_labels = {0 : '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power and n < 4:
        size /= power
        n += 1
    return f"{size:.2f} {power_labels[n]}B"

def clean_folder(folder_path, dry_run=False):
    logging.info(f"Checking: {folder_path}")
    files_deleted = 0
    size_cleared = 0
    
    if not os.path.exists(folder_path):
        logging.warning(f"Path not found: {folder_path}")
        return 0, 0

    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)
        try:
            current_size = get_size(item_path)
            
            if dry_run:
                logging.info(f"[DRY RUN] Would delete: {item_path} ({format_bytes(current_size)})")
                files_deleted += 1
                size_cleared += current_size
                continue

            if os.path.isfile(item_path) or os.path.islink(item_path):
                os.unlink(item_path)
                files_deleted += 1
                size_cleared += current_size
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)
                files_deleted += 1
                size_cleared += current_size
        except Exception as e:
            # Skip files in use
            pass
            
    return files_deleted, size_cleared

def empty_recycle_bin(dry_run=False):
    if dry_run:
        logging.info("[DRY RUN] Would empty Recycle Bin")
        return True
    
    logging.info("Emptying Recycle Bin...")
    try:
        flags = 0x00000001 | 0x00000002 | 0x00000004
        ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, flags)
        return True
    except Exception as e:
        logging.error(f"Error emptying recycle bin: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Windows System Cleaner - Automation Tool")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be deleted without actually deleting")
    args = parser.parse_args()

    if platform.system() != "Windows":
        logging.error("This script is designed for Windows only.")
        return

    logging.info("--- Windows System Cleaner v1.1 ---")
    if args.dry_run:
        logging.info("!!! DRY RUN MODE ACTIVE !!!")
    
    targets = [
        os.environ.get('TEMP'),
        os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'Temp'),
    ]
    
    if is_admin():
        targets.append(os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'Prefetch'))
    else:
        logging.info("Note: Run as Administrator to clean System Temp and Prefetch folders.")

    total_files = 0
    total_size = 0

    for target in targets:
        if target:
            files, size = clean_folder(target, dry_run=args.dry_run)
            total_files += files
            total_size += size

    empty_recycle_bin(dry_run=args.dry_run)
    
    logging.info("\n--- Summary ---")
    action = "Would be deleted" if args.dry_run else "Deleted"
    logging.info(f"Files/Folders {action}: {total_files}")
    logging.info(f"Disk space {action.lower()}: {format_bytes(total_size)}")
    logging.info("Cleanup session finished.")

if __name__ == "__main__":
    main()