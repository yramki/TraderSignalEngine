# Special Note for macOS Users with Homebrew Python

If you're using macOS with Python installed via Homebrew, you may encounter the "externally-managed-environment" error when trying to install packages. This is a security feature in Homebrew's Python that prevents potentially breaking your system Python installation.

## Running the Application

The installation script has created special helper scripts for running the application:

```bash
# For the demo version
./run_from_venv.sh demo_trading_parameters.py

# For the headless version
./run_from_venv.sh test_headless.py

# For the GUI version
./run_gui_from_venv.sh
```

## Troubleshooting Tkinter Issues

If you encounter GUI-related errors, you may need to install Tkinter for Homebrew's Python:

```bash
brew install python-tk
```

After installing Tkinter, you'll need to reinstall the application:

```bash
# Remove the existing virtual environment
rm -rf venv

# Run the installation script again
./install.sh
```

## Manual Virtual Environment Setup

If you need to manually set up a virtual environment:

```bash
# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Install setuptools (important for Python 3.13+)
pip install --upgrade pip setuptools wheel

# Install requirements
pip install -r requirements.txt

# Run the application within the virtual environment
python demo_trading_parameters.py
# OR
python test_headless.py
# OR
./run_enhanced_trading_ui.sh
```

## Common Issues and Solutions

### 1. "externally-managed-environment" Error

This occurs because Homebrew's Python is set up to prevent direct pip installations. The solution is to always use a virtual environment as described above.

### 2. Tkinter Not Available

If you get errors like "No module named '_tkinter'" or "No module named 'tkinter'":

```bash
# Install tkinter via Homebrew
brew install python-tk

# Recreate the virtual environment
rm -rf venv
./install.sh
```

### 3. Python 3.13+ Setuptools Issues

If you're using Python 3.13+ and encounter setuptools errors, please refer to PYTHON_313_NOTE.md for specific solutions.