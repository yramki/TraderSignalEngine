# Note for Python 3.13+ Users

If you're using Python 3.13 or newer, you might encounter installation issues related to `setuptools` when trying to install packages. This is a known issue with Python 3.13's handling of build dependencies.

## Common Error

```
pip._vendor.pyproject_hooks._impl.BackendUnavailable: Cannot import 'setuptools.build_meta'
```

## Solution

Before running the installation script, manually install setuptools:

```bash
python3 -m pip install --upgrade pip setuptools wheel
```

Then run the installation script:

```bash
chmod +x install.sh
./install.sh
```

The installation script has been updated to automatically handle this for Python 3.13+ users when creating a virtual environment, but this manual step might be needed if you're installing in the global Python environment.

## Alternative Solution

If you continue to have issues, you can try creating a virtual environment with an older Python version (3.11 or 3.12) if available on your system:

```bash
# For example, if you have Python 3.11 installed
python3.11 -m venv venv
source venv/bin/activate
./install.sh
```

## Additional Notes

- The `tk` package might not be available via pip. If you get an error about `tk`, you may need to install it via your system package manager:
  - Ubuntu/Debian: `sudo apt-get install python3-tk`
  - macOS (Homebrew): `brew install python-tk`
  - Windows: Tkinter is included with the standard Python installer

- If you encounter issues with OpenCV, try installing system dependencies:
  - Ubuntu/Debian: `sudo apt-get install libopencv-dev`
  - macOS (Homebrew): `brew install opencv`