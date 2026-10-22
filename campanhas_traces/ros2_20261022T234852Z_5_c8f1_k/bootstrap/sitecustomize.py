import os, runpy
previous = '/usr/lib/python3.12/sitecustomize.py'
if previous and os.path.isfile(previous):
    runpy.run_path(previous)
