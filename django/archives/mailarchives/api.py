from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.db import connection
import ipaddress

from .views import cache
from .models import Message, List

import json
import requests
from django.http import JsonResponse

def is_host_allowed(request):
    for ip_range in settings.API_CLIENTS:
        if ipaddress.ip_address(request.META['REMOTE_ADDR']) in ipaddress.ip_network(ip_range):
            return True
    return False


@cache(hours=4)
def listinfo(request):
    if not settings.PUBLIC_ARCHIVES:
        return HttpResponseForbidden('No API access on private archives for now')

    if not is_host_allowed(request):
        return HttpResponseForbidden('Invalid host')

    resp = HttpResponse(content_type='application/json')
    json.dump([{
        'name': l.listname,
        'shortdesc': l.shortdesc,
        'description': l.description,
        'active': l.active,
        'group': l.group.groupname,
    } for l in List.objects.select_related('group').all()], resp)

    return resp


@cache(hours=4)
def latest(request, listname):
    if not settings.PUBLIC_ARCHIVES:
        return HttpResponseForbidden('No API access on private archives for now')

    if not is_host_allowed(request):
        return HttpResponseForbidden('Invalid host')

    # Return the latest <n> messages on this list.
    # If <n> is not specified, return 50. Max value for <n> is 100.
    if 'n' in request.GET:
        try:
            limit = int(request.GET['n'])
        except Exception:
            limit = 0
    else:
        limit = 50
    if limit <= 0 or limit > 100:
        limit = 50

    extrawhere = []
    extraparams = []

    # Return only messages that have attachments?
    if 'a' in request.GET:
        if request.GET['a'] == '1':
            extrawhere.append("has_attachment")

    # Restrict by full text search
    if 's' in request.GET and request.GET['s']:
        extrawhere.append("fti @@ plainto_tsquery('public.pg', %s)")
        extraparams.append(request.GET['s'])

    if listname != '*':
        list = get_object_or_404(List, listname=listname)
        extrawhere.append("threadid IN (SELECT threadid FROM list_threads WHERE listid=%s)" % list.listid)
    else:
        list = None
        extrawhere = ''

    mlist = Message.objects.defer('bodytxt', 'cc', 'to').select_related().extra(where=extrawhere, params=extraparams).order_by('-date')[:limit]
    allyearmonths = set([(m.date.year, m.date.month) for m in mlist])

    resp = HttpResponse(content_type='application/json')
    json.dump([
        {
            'msgid': m.messageid,
            'date': m.date.isoformat(),
            'from': m.mailfrom,
            'subj': m.subject,
        }
        for m in mlist], resp)

    # Make sure this expires from the varnish cache when new entries show
    # up in this month.
    # XXX: need to deal with the global view, but for now API callers come in directly
    if list and settings.PUBLIC_ARCHIVES:
        resp['xkey'] = ' '.join(['pgam_{0}/{1}/{2}'.format(list.listid, year, month) for year, month in allyearmonths])
    return resp


@cache(hours=4)
def thread(request, msgid):
    if not settings.PUBLIC_ARCHIVES:
        return HttpResponseForbidden('No API access on private archives for now')

    if not is_host_allowed(request):
        return HttpResponseForbidden('Invalid host')

    # Return metadata about a single thread. A list of all the emails
    # that are in the thread with their basic attributes are included.
    msg = get_object_or_404(Message, messageid=msgid)
    mlist = Message.objects.defer('bodytxt', 'cc', 'to').filter(threadid=msg.threadid)

    resp = HttpResponse(content_type='application/json')
    json.dump([
        {
            'msgid': m.messageid,
            'date': m.date.isoformat(),
            'from': m.mailfrom,
            'subj': m.subject,
            'atts': [{'id': a.id, 'name': a.filename, 'is_patch': a.is_patch, 'content_type': a.contenttype}
                    for a in m.attachment_set.extra(select={'is_patch': 'attachments.is_patch'}).all()],
        }
        for m in mlist], resp)
    if settings.PUBLIC_ARCHIVES:
        resp['xkey'] = 'pgat_{0}'.format(msg.threadid)
    return resp

def threads_with_patches(request):
    if not settings.PUBLIC_ARCHIVES:
        return HttpResponseForbidden('No API access on private archives for now')

    with connection.cursor() as cursor:
        cursor.execute("""-- Find threads with patches
                select *
                from (
                    select distinct on (threadid)
                        pm.threadid,
                        pm.id,
                        pm._from,
                        pm.subject,
                        pm.messageid,
                        ma.patch_count,
                        tm.subject AS thread_subject,
                        pm.date AS patch_date,
                        tm.date AS thread_date,
                        tm.messageid AS thread_messageid
                    from messages AS pm --patch message
                    -- threadid is a shared value but not a foreign key to anything
                    -- in particular, it is not a self-join of messages
                    join lateral (
                       select *
                       from messages as im
                       where im.threadid = pm.threadid
                       order by im.date asc
                       limit 1
                    ) AS tm on true --thread message is first known message
                    join lateral (
                       select count(*) as patch_count
                       from attachments
                       where pm.id = attachments.message and is_patch(attachments)
                    ) as ma on true
                    where pm.has_attachment and ma.patch_count > 0 and pm.hiddenstatus is null
                    order by pm.threadid, pm.date desc
                ) as threads_with_patches
                order by patch_date DESC
                limit 10;
                       """)
        rows = cursor.fetchall()

    # Convert the SQL result into thread_list
    thread_list = [
        {
            "thread_id": str(row[0]),
            "message_id": row[1],
            "file_count": row[5],
            "file_version": None,
            "commit_sha": None,
            "patch_id": None,
            "subject_line": row[3],
            "thread_subject": row[6],
            "sender": row[2],
            "id": row[1],
            "patch_date": row[7].strftime('%Y-%m-%d %H:%M:%S') if row[7] else None,
            "thread_date": row[8].strftime('%Y-%m-%d %H:%M:%S') if row[8] else None,
            "message_code": row[4],
            "thread_code": row[9]
        }
        for row in rows
    ]

    resp = HttpResponse(content_type='application/json')
    json.dump(thread_list, resp)

    return resp

def get_patch_data_as_json(threadid, messageid):
    with connection.cursor() as cursor:
        cursor.execute("""-- Find threads with patches
                    select
                        pm.threadid,
                        pm.id,
                        tm.messageid as thread_messageid,
                        mrm.mostrecent_messageid,
                        pm.messageid as patch_messageid,
                        ma.fileset,
                        pm._from as patch_from_author,
                        tm.date as thread_messagedate,
                        mrm.mostrecent_messagedate,
                        pm.date as patch_messagedate,
                        tm.subject as thread_subject_line,
                        mrm.most_recent_subject_line,
                        mrm.most_recent_from_author,
                        tm._from as thread_from_author
                    from messages AS pm --patch message
                    join lateral (
                       select *
                       from messages as im
                       where im.threadid = pm.threadid
                       order by im.date asc
                       limit 1
                    ) AS tm on true --thread message is first known message
                    join lateral (
                        select
                            id as mostrecent_id,
                            messageid as mostrecent_messageid,
                            date as mostrecent_messagedate,
                            subject as most_recent_subject_line,
                            _from as most_recent_from_author
                        from messages
                        where threadid = pm.threadid
                       order by date desc limit 1
                    ) as mrm on true
                    join lateral (
                       select jsonb_agg(
                                jsonb_build_object(
                                    'attachment_id', a.id,
                                    'filename', a.filename,
                                    'content_type', a.contenttype,
                                    'is_patch', is_patch(a)
                                ) order by a.filename) as fileset
                       from attachments as a
                       where pm.id = a.message
                    ) as ma on true
                    where pm.id = %s;
                       """,
                       (messageid,))
        row = cursor.fetchone()

    # Convert the SQL result into patch_data
    patch_data = {
        "thread_id": row[0],
        "message_id": row[1],
        "thread_message_id": row[2],
        "most_recent_message_id": row[3],
        "patch_message_id": row[4],
        "patch_from_author": row[6],
        "fileset": json.loads(row[5]) if row[5] else [],
        "thread_message_date": row[7].isoformat() if row[7] else None,
        "most_recent_message_date": row[8].isoformat() if row[8] else None,
        "patch_message_date": row[9].isoformat() if row[9] else None,
        "thread_subject_line": row[10],
        "most_recent_subject_line": row[11],
        "most_recent_from_author": row[12],
        "thread_from_author": row[13],
    }

    return json.dumps(patch_data)

def create_cfapp_patch(request):
    if not settings.PUBLIC_ARCHIVES:
        return HttpResponseForbidden('No API access on private archives for now')

    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)

    body_string = request.body.decode("utf-8")
    body_json = json.loads(body_string)

    try:
        # Forward the request body to the external service
        response = requests.post(
            'http://localhost:8007/api/test/cfapp/create_patch',
            headers={'Content-Type': 'application/json'},
            data=get_patch_data_as_json(body_json["thread_id"], body_json["message_id"]),
        )

        # Return the response from the external service
        return JsonResponse(response.json(), status=response.status_code)
    except requests.RequestException as e:
        return JsonResponse({'error': f'Failed to proxy request: {str(e)}'}, status=500)
