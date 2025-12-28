# Publishing RedRun to PyPI

This guide explains how to publish RedRun to PyPI so it can be installed via `pip install redrun`.

## Prerequisites

1. **PyPI Account**: Create an account at https://pypi.org/account/register/
2. **TestPyPI Account** (recommended for first-time publishing): Create an account at https://test.pypi.org/account/register/
3. **API Token**: Generate an API token at https://pypi.org/manage/account/token/ (or https://test.pypi.org/manage/account/token/ for TestPyPI)

## Step 1: Test on TestPyPI (Recommended)

Before publishing to the main PyPI, test on TestPyPI:

```bash
# Make sure you're in the RedRun directory
cd /Users/ahmed/Desktop/RedRun

# Activate your virtual environment
source .venv/bin/activate

# Upload to TestPyPI
python -m twine upload --repository testpypi dist/*
```

You'll be prompted for:
- Username: `__token__`
- Password: Your TestPyPI API token (starts with `pypi-`)

## Step 2: Test Installation from TestPyPI

```bash
# Create a new virtual environment to test
python3 -m venv test_env
source test_env/bin/activate

# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ redrun

# Test it works
redrun --help
```

## Step 3: Publish to PyPI

Once you've verified everything works on TestPyPI:

```bash
# Make sure you're in the RedRun directory
cd /Users/ahmed/Desktop/RedRun

# Activate your virtual environment
source .venv/bin/activate

# Upload to PyPI
python -m twine upload dist/*
```

You'll be prompted for:
- Username: `__token__`
- Password: Your PyPI API token (starts with `pypi-`)

## Step 4: Verify Installation

After publishing, test the installation:

```bash
# Create a new virtual environment
python3 -m venv test_env
source test_env/bin/activate

# Install from PyPI
pip install redrun

# Test it works
redrun --help
redrun analyze build.log
```

## Updating the Package

When you make changes and want to publish a new version:

1. **Update version** in `pyproject.toml`:
   ```toml
   version = "0.1.1"  # Increment version number
   ```

2. **Rebuild the package**:
   ```bash
   python -m build
   ```

3. **Upload the new version**:
   ```bash
   python -m twine upload dist/*
   ```

## Important Notes

- **Version numbers**: Follow semantic versioning (MAJOR.MINOR.PATCH)
- **Package name**: The package name `redrun` must be unique on PyPI
- **First upload**: Once a version is uploaded, it cannot be overwritten or deleted
- **API tokens**: Store your API tokens securely. Never commit them to git.

## Troubleshooting

### "Package already exists"
- The version number already exists on PyPI. Increment the version in `pyproject.toml`.

### "Invalid credentials"
- Make sure you're using `__token__` as the username and your full API token (including `pypi-` prefix) as the password.

### "File already exists"
- The exact file already exists. Either increment the version or delete the old files from `dist/` and rebuild.

## Current Package Files

The build process creates:
- `dist/redrun-0.1.0-py3-none-any.whl` - Wheel distribution (preferred)
- `dist/redrun-0.1.0.tar.gz` - Source distribution

Both files are needed for PyPI upload.

