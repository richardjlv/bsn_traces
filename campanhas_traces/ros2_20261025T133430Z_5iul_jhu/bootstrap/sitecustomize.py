import os, runpy, sys
previous = '/usr/lib/python3.12/sitecustomize.py'
if previous and os.path.isfile(previous):
    runpy.run_path(previous)
if os.path.basename(sys.argv[0]) != 'ros2':
    import coverage
    coverage.process_startup()
