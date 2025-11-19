#!/usr/bin/env python3
import sys
import os

# Set UTF-8 encoding for stdout/stderr before importing anything else
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Now run the actual merge script
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.chdir('..')  # Go to ag_analyst directory

# Import and run the merge_soybean module
import importlib.util
spec = importlib.util.spec_from_file_location("merge_soybean", "etl/merge_soybean.py")
merge_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(merge_module)

if __name__ == "__main__":
    merge_module.main()
