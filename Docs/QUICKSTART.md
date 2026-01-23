# Quick Start Guide

## Installation

1. Extract the archive
2. Navigate to the directory

## Windows

```cmd
nken.bat info
nken.bat build
nken.bat run
```

## Linux/Mac

```bash
chmod +x nken.sh
./nken.sh info
./nken.sh build
./nken.sh run
```

## Common Commands

- `nken build` - Build all projects
- `nken build --config Release` - Build in Release mode
- `nken clean` - Clean build artifacts
- `nken rebuild` - Clean and build
- `nken run` - Run the CLI application
- `nken info` - Show workspace information

## Test the System

The included example project demonstrates:
- Core library with system utilities
- Logger library for logging
- Jenga library for build system
- Unitest library for testing
- CLI application that uses all libraries

Run `nken build` to compile everything, then `nken run` to execute!

## Customization

Edit `jenga.nken` to:
- Add new projects
- Change compiler settings
- Add dependencies
- Configure platforms

See README.md for full documentation.
