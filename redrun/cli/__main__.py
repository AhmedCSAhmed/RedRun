"""
Entry point for running redrun as a module: python -m redrun
This ensures the editable finder is loaded before imports.
"""
import sys
import os

# Ensure editable install finder is loaded (for development installs)
# This fixes the issue where 'redrun' command can't find the module
try:
    import site
    # Add site-packages to path if not already there (ensures .pth files are processed)
    site_packages = [p for p in sys.path if 'site-packages' in p]
    if site_packages:
        site.addsitedir(site_packages[0])
    
    # Try to load the editable finder explicitly
    import importlib.util
    finder_path = None
    for sp in site_packages:
        try:
            for file in os.listdir(sp):
                if file.startswith('__editable__') and file.endswith('_finder.py'):
                    finder_path = os.path.join(sp, file)
                    break
            if finder_path:
                break
        except (OSError, PermissionError):
            continue
    
    if finder_path and os.path.exists(finder_path):
        spec = importlib.util.spec_from_file_location("_editable_finder", finder_path)
        if spec and spec.loader:
            finder_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(finder_module)
            if hasattr(finder_module, 'install'):
                finder_module.install()
except Exception:
    pass  # Not an editable install, or finder already loaded

# Now import and run main
from redrun.cli.main import main

if __name__ == '__main__':
    sys.exit(main())

