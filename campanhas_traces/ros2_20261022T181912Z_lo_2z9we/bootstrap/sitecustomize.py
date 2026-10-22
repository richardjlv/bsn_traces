import os, runpy
previous = '/usr/lib/python3.12/sitecustomize.py'
if previous and os.path.isfile(previous):
    runpy.run_path(previous)
import coverage
coverage.process_startup()
import sys, faulthandler
if os.path.basename(sys.argv[0]) == 'emergency_detection':
    faulthandler.dump_traceback_later(40, repeat=False)
