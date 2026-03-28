#!/usr/bin/env python

import argparse
import json
import sys
import pandas as pd
from zipfile import BadZipFile

VERSION = "%(prog)s 0.1.0"

ERROR_CODES = {
    3: [FileNotFoundError, PermissionError],
    4: [
        UnicodeDecodeError,
        pd.errors.EmptyDataError,
        BadZipFile,
        json.JSONDecodeError
    ]
}

def parse_args():
    parser = argparse.ArgumentParser(
        prog="colcat",
        description="cat(1) but for columns in Excel/CSV files",
        epilog=f"{VERSION} copyright (c) 2026 Hassan El anabi"
    )
    parser.add_argument("file", nargs='+', help="input data files")
    parser.add_argument("-b", "--verbose", action="store_true")
    parser.add_argument("-m", "--mapping", metavar="JSON",
                        help="JSON file mapping column names")
    parser.add_argument("-n", "--sheet-name", metavar="NAME")
    parser.add_argument("-o", "--output", default="output.xlsx",
                        help="output file name")
    parser.add_argument("-r", "--summary", action="store_true",
                        help="add a summary sheet")
    parser.add_argument("-s", "--source", action="store_true",
                        help="add a column for row source file")
    parser.add_argument("-v", "--version", action="version", version=VERSION)
    return parser.error, parser.parse_args()

def handle_errors(func):
    def wrapped(filename, *args, **kwargs):
        try:
            return func(filename, *args, **kwargs)
        except Exception as e:
            e.add_note("An error occured while processing file: " + filename)
            raise
    return wrapped

@handle_errors
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

@handle_errors
def load_file(filename, add_source, verbose):
    if verbose:
        print("Loading file:", filename, end=" ... ")

    if filename.endswith(".csv"):
        df = pd.read_csv(filename)
    elif filename.endswith(".xlsx"):
        df = pd.read_excel(filename, engine="openpyxl")
    else:
        raise ValueError("Unsupported file type")

    if verbose:
        print("done")

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

    def report(*status, **kwd):
        if args.verbose:
            print(*status, **kwd)

    if args.mapping:
        normalize = load_mapping(args.mapping)
        report("Mapping file loaded")
    else:
        normalize = lambda name: name.strip().capitalize()

    frames = tuple(load_file(f, args.source, args.verbose) for f in args.file)
    for header in map(lambda df: df.columns.values, frames):
        for i, col in enumerate(header):
            header[i] = normalize(col)

    output = args.output
    if not output.endswith(".xlsx"):
        output += ".xlsx"

    report("Concatenating files", end=" ... ")
    df = pd.concat(frames, ignore_index=True)
    report("done")

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

    report("Writing to", output)
    try:
        with pd.ExcelWriter(output) as writer:
            opts = {"index": False, "engine": "openpyxl"}
            if args.sheet_name:
                opts["sheet_name"] = args.sheet_name
            df.to_excel(writer, **opts)
            if args.summary:
                opts["sheet_name"] = "Summary"
                row_stat.to_excel(writer, **opts)
                total_rows.to_excel(writer,
                                    header=False,
                                    startrow=len(frames) + 1,
                                    **opts)
    except Exception as e:
        e.add_note("Unable to write file: " + output)
        raise

def error(msg, code=None):
    print(str(msg), file=sys.stderr)
    if code is not None:
        sys.exit(code)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        if e.__notes__:
            error('\n'.join(e.__notes__))
        exit_code = 9
        for code, exceptions in ERROR_CODES.items():
            if any(isinstance(e, exception) for exception in exceptions):
                exit_code = code
        error(e, exit_code)
