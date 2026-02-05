import os
import shutil
import ctypes
import platform

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def get_size(start_path='.'):
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(start_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                # skip if it is symbolic link
                if not os.path.islink(fp):
                    total_size += os.path.getsize(fp)
    except Exception:
        pass
    return total_size

def format_bytes(size):
    # 2**10 = 1024
    power = 2**10
    n = 0
    power_labels = {0 : '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    return f"{size:.2f} {power_labels[n]}B"

def clean_folder(folder_path):
    print(f"Cleaning: {folder_path}")
    files_deleted = 0
    size_cleared = 0
    
    if not os.path.exists(folder_path):
        print(f"Path not found: {folder_path}")
        return 0, 0

    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)
        try:
            current_size = get_size(item_path) if os.path.isdir(item_path) else os.path.getsize(item_path)
            
            if os.path.isfile(item_path) or os.path.islink(item_path):
                os.unlink(item_path)
                files_deleted += 1
                size_cleared += current_size
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)
                files_deleted += 1
                size_cleared += current_size
        except Exception as e:
            # Files are often in use, which is normal for temp folders
            pass
            
    return files_deleted, size_cleared

def empty_recycle_bin():
    print("Emptying Recycle Bin...")
    try:
        # SHEmptyRecycleBinW constants:
        # SHERB_NOCONFIRMATION = 0x00000001
        # SHERB_NOPROGRESSUI = 0x00000002
        # SHERB_NOSOUND = 0x00000004
        flags = 0x00000001 | 0x00000002 | 0x00000004
        ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, flags)
        return True
    except Exception as e:
        print(f"Error emptying recycle bin: {e}")
        return False

def main():
    if platform.system() != "Windows":
        print("This script is designed for Windows only.")
        return

    print("--- Windows System Cleaner v1.0 ---")
    
    targets = [
        os.environ.get('TEMP'),
        os.path.join(os.environ.get('SystemRoot', 'C:\Windows'), 'Temp'),
    ]
    
    # Prefetch requires admin
    if is_admin():
        targets.append(os.path.join(os.environ.get('SystemRoot', 'C:\Windows'), 'Prefetch'))
    else:
        print("Note: Run as Administrator to clean System Temp and Prefetch folders more effectively.")

    total_files = 0
    total_size = 0

    for target in targets:
        if target:
            files, size = clean_folder(target)
            total_files += files
            total_size += size

    empty_recycle_bin()
    
    print("
--- Summary ---")
    print(f"Files/Folders deleted: {total_files}")
    print(f"Disk space reclaimed: {format_bytes(total_size)}")
    print("Done!")

if __name__ == "__main__":
    main()
