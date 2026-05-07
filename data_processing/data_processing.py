#!/usr/bin/env python3
import sys
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', stream=sys.stdout)

def main():
    if len(sys.argv) != 2:
        logging.error("Usage: analyse_data.py <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]
    
    if not os.path.isfile(file_path):
        logging.error(f"File does not exist or is not a file: {file_path}")
        sys.exit(1)

    logging.info(f"Processing new file: {file_path}")
    # Your analysis logic for the specific file
    # process(file_path)

if __name__ == "__main__":
    main()