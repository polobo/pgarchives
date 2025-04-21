from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render
from django.conf import settings
import subprocess
import os
import datetime
import json
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

def threads(request):
    thread_list = [
        {
            "thread_id": "1",
            "message_id": "msg-001",
            "file_count": 5,
            "file_version": "v1",
            "commit_sha": None,
            "patch_id": None,
            "subject_line": "Initial discussion on feature X",
            "sender": "user1@example.com",
            "id": 101
        },
        {
            "thread_id": "2",
            "message_id": "msg-002",
            "file_count": 3,
            "file_version": "v1",
            "commit_sha": "def456",
            "patch_id": None,
            "subject_line": "Follow-up on feature Y",
            "sender": "user2@example.com",
            "id": 102
        },
        {
            "thread_id": "3",
            "message_id": "msg-003",
            "file_count": 7,
            "file_version": "v2",
            "commit_sha": None,
            "patch_id": "patch-003",
            "subject_line": "Bug fix discussion",
            "sender": "user3@example.com",
            "id": 103
        }
    ]

    return render(
        request,
        'dev_threads.html',
        {
            'request': request,
            'thread_list': thread_list,
        })


def threads_with_patches(request):
    if not settings.PUBLIC_ARCHIVES:
        return HttpResponseForbidden('No API access on private archives for now')

    # Generate a fake result similar to dev.threads
    thread_list = [
        {
            "thread_id": "1",
            "message_id": "msg-001",
            "file_count": 5,
            "file_version": "v1",
            "commit_sha": None,
            "patch_id": None,
            "subject_line": "Initial discussion on feature X",
            "sender": "user1@example.com",
            "id": 101
        },
        {
            "thread_id": "2",
            "message_id": "msg-002",
            "file_count": 3,
            "file_version": "v1",
            "commit_sha": "def456",
            "patch_id": None,
            "subject_line": "Follow-up on feature Y",
            "sender": "user2@example.com",
            "id": 102
        },
        {
            "thread_id": "3",
            "message_id": "msg-003",
            "file_count": 7,
            "file_version": "v2",
            "commit_sha": None,
            "patch_id": "patch-003",
            "subject_line": "Bug fix discussion",
            "sender": "user3@example.com",
            "id": 103
        }
    ]

    resp = HttpResponse(content_type='application/json')
    json.dump(thread_list, resp)

    return resp
