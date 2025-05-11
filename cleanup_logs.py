#!/usr/bin/env python3
"""
Script to clean up game logs:
1. Remove logs that don't end with a victory condition
2. Remove duplicate logs (by content, not filename)
"""

import os
import hashlib
from pathlib import Path
import re

# Path to the game logs directory
LOGS_DIR = Path('/Users/mariiakoroliuk/codenames-ai/game_logs')

def get_file_hash(filepath):
    """Generate a hash for file content to identify duplicates"""
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        buf = f.read(65536)  # Read in 64kb chunks
        while len(buf) > 0:
            hasher.update(buf)
            buf = f.read(65536)
    return hasher.hexdigest()

def has_victory_ending(filepath):
    """Check if a game log ends with a victory condition"""
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        # First do a quick size check - if it's very small, likely incomplete
        if os.path.getsize(filepath) < 50000:  # 50KB threshold
            # For small files, search the entire content
            content = f.read()
            return bool(re.search(r'Game over!.*team wins!', content))
        
        # For larger files, just check the last few KB where the victory message would be
        f.seek(0, os.SEEK_END)
        filesize = f.tell()
        chunk_size = min(20000, filesize)  # Last 20KB or full file if smaller
        f.seek(filesize - chunk_size, os.SEEK_SET)
        content = f.read()
        return bool(re.search(r'Game over!.*team wins!', content))

def main():
    # Track files to keep/delete
    to_delete = []
    kept_hashes = {}  # hash -> filepath
    kept_files = []

    print(f"Scanning {LOGS_DIR}...")
    
    # First pass: identify incomplete games and duplicates
    for filepath in LOGS_DIR.glob('game_log_*.txt'):
        try:
            if not has_victory_ending(filepath):
                to_delete.append(filepath)
                print(f"Marked for deletion (no victory): {filepath.name}")
                continue
            
            # Check for duplicates
            file_hash = get_file_hash(filepath)
            if file_hash in kept_hashes:
                # This is a duplicate
                to_delete.append(filepath)
                print(f"Marked for deletion (duplicate of {kept_hashes[file_hash].name}): {filepath.name}")
            else:
                kept_hashes[file_hash] = filepath
                kept_files.append(filepath)
        except Exception as e:
            print(f"Error processing {filepath.name}: {e}")
    
    # Second pass: delete files
    print("\nSummary:")
    print(f"Total game logs: {len(list(LOGS_DIR.glob('game_log_*.txt')))}")
    print(f"Keeping: {len(kept_files)} files")
    print(f"Deleting: {len(to_delete)} files")
    
    if to_delete:
        confirm = input("\nDelete marked files? (y/n): ")
        if confirm.lower() == 'y':
            for filepath in to_delete:
                try:
                    os.remove(filepath)
                    print(f"Deleted: {filepath.name}")
                except Exception as e:
                    print(f"Failed to delete {filepath.name}: {e}")
            print(f"Deleted {len(to_delete)} files")
        else:
            print("Operation cancelled. No files were deleted.")
    else:
        print("No files to delete.")

if __name__ == "__main__":
    main()
