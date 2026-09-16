# Directory Lister Script

A lightweight Python utility script that prints a greeting and lists all files and directories in the current working directory.

## Overview

This project contains a minimal Python script (`main.py`) designed to inspect and display the contents of the directory from which it is executed. It relies solely on Python's built-in `os` standard library module, requiring no third-party packages.

## Features

- **Greeting Message**: Prints `"Hello from the patch tool!"` to standard output upon execution.
- **Directory Listing**: Scans the current working directory (`.`) using `os.listdir()`.
- **File Output**: Iterates over and prints the name of each file and folder present in the directory.

## Prerequisites

- **Python**: Version 3.6 or higher recommended (uses standard library modules only).

## How to Run

Execute `main.py` using Python from your terminal:

```bash
python3 main.py
```

Alternatively, on systems where `python` defaults to Python 3:

```bash
python main.py
```

## Example Output

Executing the script produces output similar to the following:

```text
Hello from the patch tool!
.git
main.py
README.md
```

## Project Structure

```text
.
├── main.py     # Python script that prints a greeting and lists directory contents
└── README.md   # Project documentation
```
