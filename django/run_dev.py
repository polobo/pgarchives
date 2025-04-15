#!/usr/bin/env python3
from importlib.machinery import PathFinder
import subprocess
import sys

django_path = PathFinder().find_spec("django").submodule_search_locations[0]

django_admin_path = django_path + "/contrib/admin/static/admin"

if len(sys.argv) > 1:
    ini_file = sys.argv[1]
else:
    ini_file = "uwsgi_dev.ini"

subprocess.run(
    [
        "uwsgi",
        "--static-map",
        f"/static/admin={django_path}/contrib/admin/static/admin",
        ini_file,
    ]
)
