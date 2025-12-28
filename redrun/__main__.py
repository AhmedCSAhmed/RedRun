"""
Entry point for running redrun as a module: python -m redrun
"""
import sys
from redrun.cli.main import main

if __name__ == '__main__':
    sys.exit(main())

