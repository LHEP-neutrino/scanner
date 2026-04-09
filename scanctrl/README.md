# MyProject CLI

A simple Python command-line tool built with Click, providing `debug` and `print` subcommands with auto-completion support.

## Requirements

- Python 3.8 or higher
- `pip`

## Installation

1. **Clone or create the project directory** and navigate into it.
2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   ```
3. **Activate the virtual environment**:
Linux/macOS:
```bash
source venv/bin/activate
```
4. **Install the module in development mode**:
```bash
pip install -e .
```
Note: The activate script has been modified to automatically load shell completions upon activation.

## Usage

Once installed and the virtual environment is active, the myproject command becomes available in your terminal.

1. **Get Help**
View all available commands, options, and subcommands:
```bash
myproject --help
```
2. **Debug Command**
Prints "hello" to the terminal:
```bash
myproject debug
```
3. **Print Command**
Prints a custom text string passed via the --text argument:
```bash
myproject print --text "Hello World"
```
Note: You can also use the short flag -t.

Auto-Completion Tab-completion is automatically enabled when the virtual environment is active.
Type myproject <TAB> to see available subcommands (debug, print).
Type myproject print --<TAB> to see available options (--text, -t).
Module Structure

This project follows a standard Python package structure optimized for CLI tools:

myproject/
    ├── pyproject.toml # Project metadata, dependencies, and entry point definition
    ├── README.md # This documentation file (or .txt equivalent)
    ├── venv/ # Virtual environment (created locally) 
    │ └── bin/ 
    │ └── activate # Modified script to auto-source shell completions 
    └── myproject/ # The Python package
        ├── init.py # Package marker (optional for simple scripts)
        └── cli.py # Core logic: # - cli: Main Click group entry point 
                                # - debug: Subcommand printing "hello"
                                # - print_cmd: Subcommand with --text argument

## Uninstallation
To remove the command from your system (while keeping the project files):
```bash
    pip uninstall myproject
```
To remove the virtual environment;
```bash
    deactivate
    rm -rf venv
```
