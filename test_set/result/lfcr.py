#!/usr/bin/env python

"Replace LF with CRLF in argument files.  Print names of changed files."

import sys
import re
import os

# Define named constants for magic numbers
NEWLINE = "\r\n"
NULL_BYTE = "\0"

def replace_lf_with_crlf(file_path):
    """Replace LF with CRLF in a file."""
    try:
        with open(file_path, "rb") as file:
            data = file.read()
            if NULL_BYTE in data:
                print(f"{file_path} is a binary file.")
                return
            new_data = re.sub(r"\r?\n", NEWLINE, data)
            if new_data != data:
                print(file_path)
                with open(file_path, "wb") as file:
                    file.write(new_data)
    except Exception as e:
        print(f"Error processing {file_path}: {e}")

def main():
    for file in sys.argv[1:]:
        if os.path.isdir(file):
            print(f"{file} is a directory.")
            continue
        replace_lf_with_crlf(file)

if __name__ == "__main__":
    main()