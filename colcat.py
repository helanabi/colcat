#!/usr/bin/env python

import argparse
import sys
import pandas as pd

VERSION = "%(prog)s 0.1.0"

def parse_args():
    parser = argparse.ArgumentParser(
        prog="colcat",
        description="cat(1) but for columns in Excel/CSV files",
        epilog=f"{VERSION} copyright (c) 2026 Hassan El anabi"
    )
    parser.add_argument("file", nargs='+', help="input data files")
    parser.add_argument("-o", "--output", help="output file name")
    parser.add_argument("-v", "--version", action="version", version=VERSION)
    return parser.error, parser.parse_args()

def normalize(name):
    return name.strip().capitalize()

def load_file(filename):
    if filename.endswith(".csv"):
        return pd.read_csv(filename)
    elif filename.endswith(".xlsx"):
        return pd.read_excel(filename, engine="openpyxl")
    else:
        raise ValueError("Unsupported file type")

def main():
    usage_error, args = parse_args()
    for filename in args.file:
        if not any(filename.endswith(ext) for ext in (".csv", ".xlsx")):
            usage_error(f"unsupported file: {filename}")

    cols = []
    frames = tuple(map(load_file, args.file))
    for header in map(lambda df: df.columns.values, frames):
        for i, col in enumerate(header):
            normalized = normalize(col)
            header[i] = normalized
            if normalized not in cols:
                cols.append(normalized)

    output = args.output
    if not output.endswith(".xlsx"):
        output += ".xlsx"
    pd.concat(frames, ignore_index=True).to_excel(output, index=False)
            
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(e, file=sys.stderr)
        sys.exit(9)
