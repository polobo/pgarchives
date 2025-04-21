from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render
from django.conf import settings
from django.db import connection
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import subprocess
import os
import datetime
import json
import random
import requests

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
            "thread_subject": "Initial discussion on feature X",
            "sender": "user1@example.com",
            "id": 101,
            "patch_date": "2023-01-01 12:00:00",
            "thread_date": "2023-01-01 10:00:00"
        },
        {
            "thread_id": "2",
            "message_id": "msg-002",
            "file_count": 3,
            "file_version": "v1",
            "commit_sha": "def456",
            "patch_id": None,
            "subject_line": "Follow-up on feature Y",
            "thread_subject": "Follow-up on feature Y",
            "sender": "user2@example.com",
            "id": 102,
            "patch_date": "2023-01-02 14:00:00",
            "thread_date": "2023-01-02 12:00:00"
        },
        {
            "thread_id": "3",
            "message_id": "msg-003",
            "file_count": 7,
            "file_version": "v2",
            "commit_sha": None,
            "patch_id": "patch-003",
            "subject_line": "Bug fix discussion",
            "thread_subject": "Bug fix discussion",
            "sender": "user3@example.com",
            "id": 103,
            "patch_date": "2023-01-03 16:00:00",
            "thread_date": "2023-01-03 14:00:00"
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

    # Execute a placeholder SQL query
    with connection.cursor() as cursor:
        cursor.execute("""-- Find threads with patches
                    select distinct on (threadid)
                        pm.threadid,
                        pm.id, 
                        pm._from, 
                        pm.subject, 
                        pm.messageid,
                        ma.patch_count,
                        tm.subject AS thread_subject,
                        pm.date AS patch_date,
                        tm.date AS thread_date
                    from messages AS pm --patch message
                    left join messages AS tm on (pm.threadid = tm.id) --thread message
                    join lateral (
                       select count(*) as patch_count 
                       from attachments 
                       where pm.id = attachments.message and is_patch(attachments)
                    ) as ma on true 
                    where pm.has_attachment and ma.patch_count > 0 and pm.hiddenstatus is null 
                    order by pm.threadid, pm.date desc 
                    limit 5;
                       """)
        rows = cursor.fetchall()

    # Convert the SQL result into thread_list
    thread_list = [
        {
            "thread_id": str(row[0]),
            "message_id": row[4],
            "file_count": row[5],
            "file_version": None,
            "commit_sha": None,
            "patch_id": None,
            "subject_line": row[3],
            "thread_subject": row[6],
            "sender": row[2],
            "id": row[1],
            "patch_date": row[7].strftime('%Y-%m-%d %H:%M:%S') if row[7] else None,
            "thread_date": row[8].strftime('%Y-%m-%d %H:%M:%S') if row[8] else None
        }
        for row in rows
    ]

    resp = HttpResponse(content_type='application/json')
    json.dump(thread_list, resp)

    return resp



def create_cfapp_patch(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)

    print("Request body:", request.body)
    try:
        # Forward the request body to the external service
        response = requests.post(
            'http://localhost:8007/api/test/cfapp/create_patch',
            headers={'Content-Type': 'application/json'},
            data=request.body)

        # Return the response from the external service
        return JsonResponse(response.json(), status=response.status_code)
    except requests.RequestException as e:
        return JsonResponse({'error': f'Failed to proxy request: {str(e)}'}, status=500)
