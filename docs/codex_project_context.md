# Follow The Money – Development Environment

## Environment

Development machine:

* Windows 11 Host
* WSL2 Ubuntu 24.04 Guest
* VS Code Remote WSL

## Project Location

Project lives inside Ubuntu filesystem.

Example:

/home/parthtech/follow-the-money

NOT:

C:\Users...

All code execution happens inside Ubuntu.

## Python

Python is executed from Ubuntu.

Examples:

python -m src.main

source venv/bin/activate

pip install ...

Use Linux commands.

Do not generate Windows-specific commands.

## File Paths

Always use:

from pathlib import Path

Example:

Path("reports/daily")

Avoid:

C:...
D:...
backslash path separators

Never assume Windows paths.

## VS Code

Editor runs on Windows.

Code executes in Ubuntu through VS Code Remote WSL.

When suggesting terminal commands:

Assume Ubuntu terminal.

## Git

Git executes inside Ubuntu.

Configuration:

core.autocrlf=input

Repository standard:

LF line endings only

## Shell

Assume:

bash

not:

PowerShell
CMD

unless explicitly requested.

## Ollama

Runs inside Ubuntu.

Default URL:

http://127.0.0.1:11434

## Development Rules

1. Use pathlib instead of string paths.
2. Use OS-independent file handling.
3. Avoid hardcoded absolute paths.
4. Use environment variables for configuration.
5. Assume Linux execution environment.
6. Do not generate Windows-specific file paths.
7. All scripts must run inside WSL Ubuntu.

## Testing

Any generated code should be executable using:

source venv/bin/activate

python -m src.main

inside Ubuntu.

Always consider WSL compatibility when making changes.
