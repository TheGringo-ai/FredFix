# fredfixos/tools/file_utils.py
import hashlib
from pathlib import Path

def delete_duplicate_files(*directories):
    """Scan multiple directories and their subdirectories for duplicate files and delete them."""
    seen_hashes = {}
    deleted_files = []

    for directory in directories:
        p = Path(directory)
        for file in p.rglob("*"):
            if file.is_file():
                file_hash = hashlib.md5(file.read_bytes()).hexdigest()
                if file_hash in seen_hashes:
                    file.unlink()
                    deleted_files.append(str(file))
                else:
                    seen_hashes[file_hash] = file

    return deleted_files