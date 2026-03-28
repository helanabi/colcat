## Overview

A tool that combines messy Excel/CSV files into a clean, unified sheet

## Features

- Takes an arbitrary number of Excel/CSV files
- Automatic column alignment
- Automatic schema union
- Empty rows cleanup
- Custom column mapping
- Optional summary sheet
- Optional source tracking column

## Usage

```
usage: colcat [-h] [-b] [-m JSON] [-n NAME] [-o OUTPUT] [-r] [-s] [-v]
              file [file ...]

cat(1) but for columns in Excel/CSV files

positional arguments:
  file                  input data files

options:
  -h, --help            show this help message and exit
  -b, --verbose
  -m, --mapping JSON    JSON file mapping column names
  -n, --sheet-name NAME
  -o, --output OUTPUT   output file name
  -r, --summary         add a summary sheet
  -s, --source          add a column for row source file
  -v, --version         show program's version number and exit
```

## Column Mapping file

A JSON file mapping column names can be specified in the command line using
the `-o`/`--mapping` option. Valid mapping files must have the following format:

```JSON
{
  "Column1": ["alternative name1", ...],
  ...
}
```

* `Column1`: this is the name that will be used in the output file, its case
is conserved but column name matching is case-insensitive.

* `alternative name1`: an arbitrary number of alternative names to `Column1`
can be specified in a list, these alternative names must be in lower case, in
order to perform a case-insensitive matching.  

> See [mapping.json](mapping.json) for an example.

## Exit codes

- `2`: usage error
- `3`: filesystem error
- `4`: invalid input file
- `9`: unknown error

## LICENSE

This project is licensed under the MIT License.