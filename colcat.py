#!/usr/bin/env python

import argparse
import json
import sys
import pandas as pd
from zipfile import BadZipFile

VERSION = "%(prog)s 0.1.0"

def parse_args():
    parser = argparse.ArgumentParser(
        prog="colcat",
        description="cat(1) but for columns in Excel/CSV files",
        epilog=f"{VERSION} copyright (c) 2026 Hassan El anabi"
    )
    parser.add_argument("file", nargs='+', help="input data files")
    parser.add_argument("-m", "--mapping", metavar="JSON",
                        help="JSON file mapping column names")
    parser.add_argument("-o", "--output", default="output.xlsx",
                        help="output file name")
    parser.add_argument("-r", "--summary", action="store_true",
                        help="add a summary sheet")
    parser.add_argument("-s", "--source", action="store_true",
                        help="add a column for row source file")
    parser.add_argument("-v", "--version", action="version", version=VERSION)
    return parser.error, parser.parse_args()

def load_mapping(mapping_file):
    with open(mapping_file) as f:
        mapping = json.load(f)
    if not isinstance(mapping, dict):
        error("Error: mapping file must consist of a mapping object", 4)
    if not all(map(lambda obj: isinstance(obj, list), mapping.values())):
        error("Error: mapping object values must be lists", 4)

    def normalize(name):
        name = name.strip()
        name_lower = name.lower()
        for normalized, alt in mapping.items():
            if name_lower in alt or name_lower == normalized.lower():
                return normalized
        return name
    return normalize

def load_file(filename, add_source):
    if filename.endswith(".csv"):
        try:
            df = pd.read_csv(filename)
        except pd.errors.EmptyDataError as e:
            error(f"{e}: {filename}", 4)
    elif filename.endswith(".xlsx"):
        try:
            df = pd.read_excel(filename, engine="openpyxl")
        except BadZipFile as e:
            error(f"Invalid Excel file: {filename}", 4)
    else:
        raise ValueError("Unsupported file type")

    df.dropna(how="all", inplace=True)
    if add_source:
        rows, cols = df.shape
        df.insert(cols, "Source", (filename,) * rows, allow_duplicates=True)
    return df

def main():
    usage_error, args = parse_args()
    for filename in args.file:
        if not any(filename.endswith(ext) for ext in (".csv", ".xlsx")):
            usage_error(f"unsupported file: {filename}")

    if args.mapping:
        normalize = load_mapping(args.mapping)
    else:
        normalize = lambda name: name.strip().capitalize()

    frames = tuple(load_file(f, args.source) for f in args.file)
    for header in map(lambda df: df.columns.values, frames):
        for i, col in enumerate(header):
            header[i] = normalize(col)

    output = args.output
    if not output.endswith(".xlsx"):
        output += ".xlsx"

    df = pd.concat(frames, ignore_index=True)
    if args.summary:
        row_stat = pd.DataFrame(
            zip(args.file,
                (f.shape[0] for f in frames),
                (','.join(f.columns) for f in frames)),
            columns=("File", "Row Count", "Columns Present")
        )
        total_rows = pd.DataFrame.from_records(
            (("Total rows", df.shape[0]),)
        )
                                  
    with pd.ExcelWriter(output) as writer:
        df.to_excel(writer, index=False, engine="openpyxl")
        if args.summary:
            row_stat.to_excel(writer,
                              sheet_name="Summary",
                              index=False,
                              engine="openpyxl")
            
            total_rows.to_excel(writer,
                                sheet_name="Summary",
                                header=False,
                                index=False,
                                startrow=len(frames) + 1,
                                engine="openpyxl")

def error(msg, code):
    print(str(msg), file=sys.stderr)
    sys.exit(code)

if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, PermissionError) as e:
        error(e, 3)
    except (json.JSONDecodeError,
            UnicodeDecodeError) as e:
        error(e, 4)
    except Exception as e:
        error(e, 9)
