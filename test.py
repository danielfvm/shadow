#!/bin/python3
import sys

sys.argv = [ 'test.py', 'script.py' ]

for script_path in sys.argv[1:]:
    module_name = script_path[:-3]
    script = __import__(module_name)

    if hasattr(script, "test"):
        print(script.test(2))
