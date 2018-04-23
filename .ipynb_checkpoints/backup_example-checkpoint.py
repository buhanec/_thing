#!/usr/bin/env python
"""A file-level docstring. Boilerplate example."""

import glob
import os
import shutil
import sys
from typing import List


def files_of_interest(directory: str) -> List[str]:
    return glob.glob(os.path.join(directory, '*.txt'))


def backup_files(files: List[str], backup_directory: str):
    for file in files:
        shutil.copy(file, backup_directory)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print(f'Usage: {sys.argv[0]} <src> <dest>')
        sys.exit(1)
    _, src, dest = sys.argv
    backup_files(files_of_interest(src), dest)
