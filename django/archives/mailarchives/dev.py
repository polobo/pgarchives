from django.shortcuts import render
from django.conf import settings
import subprocess
import os
import datetime

def debug(request):
    try:
        pg_repo_code = subprocess.check_output(
            ['git', '-C', settings.LOCAL_PGREPO_DIR, 'log', '-n', '1', '--pretty=format:%H %ci %s%n%b', '--grep=Discussion:', '--since=10 months ago'],
            text=True
        )
    except subprocess.CalledProcessError as e:
        pg_repo_code = f"Error running git log: {e}"

    try:
        mbox_repo_files = [
            {
                "name": entry.name,
                "creation_time": datetime.datetime.fromtimestamp(entry.stat().st_ctime).strftime('%Y-%m-%d %H:%M:%S')
            }
            for entry in os.scandir(settings.LOCAL_MBOXREPO_DIR)
            if entry.is_file()
        ]
    except Exception as e:
        mbox_repo_files = [{"error": f"Error retrieving directory contents: {e}"}]

    return render(
        request,
        'dev_debug.html',
        {
            'request': request,
            'pg_repo': settings.LOCAL_PGREPO_DIR,
            'mbox_repo': settings.LOCAL_MBOXREPO_DIR,
            'pg_repo_code': pg_repo_code,
            'mbox_repo_files': mbox_repo_files,
        })
