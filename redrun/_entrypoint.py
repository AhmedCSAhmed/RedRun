"""
Wrapper entry point for the RedRun CLI command.

This module serves as the entry point for the 'redrun' command-line tool.
It ensures that the editable finder is loaded before importing the main
application code, which fixes import issues that can occur with editable
(development) installs using pip install -e.

The problem: When a package is installed in editable mode, pip creates
a special finder module (__editable__..._finder.py) that must be loaded
before the package can be imported. However, entry point scripts sometimes
execute before this finder is properly initialized.

The solution: This wrapper explicitly:
1. Adds the project root to sys.path
2. Finds and loads the editable finder if it exists
3. Then imports and executes the main CLI code

This ensures that 'redrun' command works correctly whether installed in
editable mode or as a regular package.
"""

import sys
import os

# CRITICAL: Add project root to sys.path FIRST, before any imports
# This ensures the editable finder can be found and loaded
def _setup_path():
    """
    Add project root to sys.path if not already there.
    
    This function ensures that the RedRun project root is in sys.path,
    which is necessary for the editable finder to locate the package.
    The project root is determined by finding the parent directory of
    this file's directory (since this file is in redrun/, the parent
    is the project root).
    
    Note:
        This modifies sys.path at runtime, which is generally not
        recommended, but is necessary here to fix editable install issues.
    """
    # Find the project root (where this file is located)
    current_file = os.path.abspath(__file__)
    project_root = os.path.dirname(os.path.dirname(current_file))
    
    # Add to sys.path if not already there
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

# Setup path first
_setup_path()

# Load editable finder BEFORE any redrun imports
def _load_editable_finder():
    """
    Load the editable finder if this is a development install.
    
    When a package is installed in editable mode (pip install -e),
    pip creates a special finder module named __editable__..._finder.py
    in site-packages. This finder must be loaded and its install()
    method called before the package can be imported.
    
    This function:
    1. Locates site-packages directories
    2. Searches for the editable finder module
    3. Loads and executes its install() method
    
    If no editable finder is found (regular install) or if an error
    occurs, the function silently returns. This allows the code to
    work in both editable and regular install modes.
    
    Raises:
        No exceptions are raised - all errors are silently ignored
        to allow fallback to regular import behavior.
    """
    try:
        import site
        import importlib.util
        
        # Find site-packages directory
        site_packages = [p for p in sys.path if 'site-packages' in p]
        if not site_packages:
            return
        
        # Ensure .pth files are processed
        site.addsitedir(site_packages[0])
        
        # Find and load the editable finder
        for sp in site_packages:
            try:
                for file in os.listdir(sp):
                    if file.startswith('__editable__') and file.endswith('_finder.py'):
                        finder_path = os.path.join(sp, file)
                        if os.path.exists(finder_path):
                            spec = importlib.util.spec_from_file_location("_editable_finder", finder_path)
                            if spec and spec.loader:
                                finder_module = importlib.util.module_from_spec(spec)
                                spec.loader.exec_module(finder_module)
                                if hasattr(finder_module, 'install'):
                                    finder_module.install()
                                    return
            except (OSError, PermissionError):
                continue
    except Exception:
        pass  # Not an editable install, or finder already loaded

# Load finder first
_load_editable_finder()

# Now import and run main
from redrun.cli.main import main

if __name__ == '__main__':
    sys.exit(main())

