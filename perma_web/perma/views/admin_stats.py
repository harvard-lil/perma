import celery
from datetime import timedelta
import itertools
import redis

from django.conf import settings
from django.db.models import Count
from django.db.models.expressions import RawSQL
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone

from perma.models import LinkUser, Link, Capture, CaptureJob, InternetArchiveItem
from perma.utils import get_complete_ia_rate_limiting_info, user_passes_test_or_403


@user_passes_test_or_403(lambda user: user.is_staff)
def stats(request, stat_type=None):

    out = None

    if stat_type == "days":
        # get link counts for last 30 days
        out = {'days':[]}
        for days_ago in range(30):
            end_date = timezone.now() - timedelta(days=days_ago)
            start_date = end_date - timedelta(days=1)
            day = {
                'days_ago': days_ago,
                'start_date': start_date,
                'end_date': end_date,
                'top_users': list(LinkUser.objects
                                          .filter(created_links__creation_timestamp__gt=start_date,created_links__creation_timestamp__lt=end_date)
                                          .annotate(links_count=Count('created_links'))
                                          .order_by('-links_count')[:3]
                                          .values('email','links_count')),
                'statuses': Capture.objects
                                   .filter(role='primary', link__creation_timestamp__gt=start_date, link__creation_timestamp__lt=end_date)
                                   .values('status')
                                   .annotate(count=Count('status')),
                'capture_time_dist': '-',
                'wait_time_dist': '-',
            }

            # calculate 5%/50%/95% capture and wait timings
            capture_time_fields = CaptureJob.objects.filter(
                link__creation_timestamp__gt=start_date, link__creation_timestamp__lt=end_date
            ).values(
                'capture_start_time', 'link__creation_timestamp', 'capture_end_time'
            ).exclude(capture_start_time=None).exclude(capture_end_time=None)
            if capture_time_fields:
                ctf_len = len(capture_time_fields)
                capture_times = sorted(c['capture_end_time']-c['capture_start_time'] for c in capture_time_fields)
                wait_times = sorted(c['capture_start_time']-c['link__creation_timestamp'] for c in capture_time_fields)
                day['capture_time_dist'] = " / ".join(str(i) for i in [capture_times[int(ctf_len*.05)], capture_times[int(ctf_len*.5)], capture_times[int(ctf_len*.95)]])
                day['wait_time_dist'] = " / ".join(str(i) for i in [wait_times[int(ctf_len*.05)], wait_times[int(ctf_len*.5)], wait_times[int(ctf_len*.95)]])

            day['statuses'] = dict((x['status'], x['count']) for x in day['statuses'])
            day['link_count'] = sum(day['statuses'].values())
            out['days'].append(day)

    elif stat_type == "emails":
        # get users by email top-level domain
        out = {
            'users_by_domain': list(LinkUser.objects
                .filter(is_confirmed=True)
                # Postgres doesn't presently let you extract the last element of a split cleanly:
                # technique from https://www.postgresql-archive.org/split-part-for-the-last-element-td6159483.html
                .annotate(domain=RawSQL("reverse(split_part(reverse(lower(email)), '.', 1))", []))
                .values('domain')
                .annotate(count=Count('domain'))
                .order_by('-count')
                .values('domain', 'count'))
        }

    elif stat_type == "random":
        # random
        out = {
            'total_link_count': Link.objects.count(),
            'private_link_count': Link.objects.filter(is_private=True).count(),
            'private_user_direction': Link.objects.filter(is_private=True, private_reason='user').count(),
            'private_domain': Link.objects.filter(is_private=True, private_reason='domain').count(),
            'private_meta': Link.objects.filter(is_private=True, private_reason='meta').count(),
            'private_meta_perma': Link.objects.filter(is_private=True, private_reason='meta_perma').count(),
            'private_takedown': Link.objects.filter(is_private=True, private_reason='takedown').count(),
            'private_flagged': Link.objects.filter(is_private=True, private_reason='flagged').count(),
            'private_meta_failure': Link.objects.filter(is_private=True, private_reason='failure').count(),
            'links_w_meta_failure_tag': Link.objects.filter(tags__name__in=['meta-tag-retrieval-failure']).count(),
            'links_w_timeout_failure_tag': Link.objects.filter(tags__name__in=['timeout-failure']).count(),
            'links_w_browser_crashed_tag': Link.objects.filter(tags__name__in=['browser-crashed']).count(),
            'total_user_count': LinkUser.objects.count(),
            'unconfirmed_user_count': LinkUser.objects.filter(is_confirmed=False).count(),
            'users_with_ten_links':LinkUser.objects.filter(link_count=10).count(),
            'confirmed_users_with_no_links':LinkUser.objects.filter(is_confirmed=True, link_count=0).count()
        }
        out['private_link_percentage'] = round(100.0*out['private_link_count']/out['total_link_count'], 1) if out['total_link_count'] else 0
        out['private_user_percentage_of_total'] = round(100.0*out['private_user_direction']/out['total_link_count'], 1) if out['total_link_count'] else 0
        out['private_user_percentage_of_private'] = round(100.0*out['private_user_direction']/out['private_link_count'], 1) if out['private_link_count'] else 0
        out['private_domain_percentage_of_total'] = round(100.0*out['private_domain']/out['total_link_count'], 1) if out['total_link_count'] else 0
        out['private_domain_percentage_of_private'] = round(100.0*out['private_domain']/out['private_link_count'], 1) if out['private_link_count'] else 0
        out['private_meta_perma_percentage_of_total'] = round(100.0*out['private_meta_perma']/out['total_link_count'], 1) if out['total_link_count'] else 0
        out['private_meta_perma_percentage_of_private'] = round(100.0*out['private_meta_perma']/out['private_link_count'], 1) if out['private_link_count'] else 0
        out['private_meta_percentage_of_total'] = round(100.0*out['private_meta']/out['total_link_count'], 1) if out['total_link_count'] else 0
        out['private_meta_percentage_of_private'] = round(100.0*out['private_meta']/out['private_link_count'], 1) if out['private_link_count'] else 0
        out['private_flagged_percentage_of_total'] = round(100.0*out['private_flagged']/out['total_link_count'], 1) if out['total_link_count'] else 0
        out['private_flagged_percentage_of_private'] = round(100.0*out['private_flagged']/out['private_link_count'], 1) if out['private_link_count'] else 0
        out['private_takedown_percentage_of_total'] = round(100.0*out['private_takedown']/out['total_link_count'], 1) if out['total_link_count'] else 0
        out['private_takedown_percentage_of_private'] = round(100.0*out['private_takedown']/out['private_link_count'], 1) if out['private_link_count'] else 0
        out['private_meta_failure_percentage_of_total'] = round(100.0*out['private_meta_failure']/out['total_link_count'], 1) if out['total_link_count'] else 0
        out['private_meta_failure_percentage_of_private'] = round(100.0*out['private_meta_failure']/out['private_link_count'], 1) if out['private_link_count'] else 0
        out['tagged_meta_failure_percentage_of_total'] = round(100.0*out['links_w_meta_failure_tag']/out['total_link_count'], 1) if out['total_link_count'] else 0
        out['tagged_timeout_failure_percentage_of_total'] = round(100.0*out['links_w_timeout_failure_tag']/out['total_link_count'], 1) if out['total_link_count'] else 0
        out['tagged_browser_crashed_percentage_of_total'] = round(100.0*out['links_w_browser_crashed_tag']/out['total_link_count'], 1) if out['total_link_count'] else 0

        out['unconfirmed_user_percentage'] = round(100.0*out['unconfirmed_user_count']/out['total_user_count'], 1) if out['total_user_count'] else 0
        out['users_with_ten_links_percentage'] = round(100.0*out['users_with_ten_links']/out['total_user_count'], 1) if out['total_user_count'] else 0
        out['confirmed_users_with_no_links_percentage'] = round(100.0*out['confirmed_users_with_no_links']/out['total_user_count'], 1) if out['total_user_count'] else 0


    elif stat_type == "celery":
        inspector = celery.current_app.control.inspect()
        active = inspector.active()
        reserved = inspector.reserved()
        stats = inspector.stats()
        queues = []
        if active is not None:
            for queue in sorted(active.keys()):
                try:
                    queues.append({
                        'name': queue,
                        'active': active[queue],
                        'reserved': reserved[queue],
                        'stats': stats[queue],
                    })
                except (KeyError, TypeError):
                    pass
        out = {'queues':queues}

    elif stat_type == "celery_queues":
        r = redis.from_url(settings.CELERY_BROKER_URL)
        out = {
            'total_main_queue': r.llen('celery'),
            'total_background_queue': r.llen('background'),
            'total_ia_queue': r.llen('ia'),
            'total_ia_readonly_queue': r.llen('ia-readonly'),
            'total_wacz_conversion_queue': r.llen('wacz-conversion')
        }

    elif stat_type == "job_queue":
        job_queues = CaptureJob.objects.filter(status='pending').order_by('order', 'pk').select_related('link', 'link__created_by')
        job_queues = dict(itertools.groupby(job_queues, lambda x: 'human' if x.human else 'robot'))
        for queue_key, queue in job_queues.items():
            job_queues[queue_key] = [{'email':email, 'count':len(list(jobs))} for email, jobs in itertools.groupby(queue, lambda x: x.link.created_by.email)]
        out = {
            'job_queues': job_queues,
            'active_jobs': [{
                'link_id': j.link_id,
                'email': j.link.created_by.email,
                'attempt': j.attempt,
                'step_count': round(j.step_count, 2),
                'step_description': j.step_description,
                'capture_start_time': j.capture_start_time
            } for j in CaptureJob.objects.filter(status='in_progress').select_related('link', 'link__created_by')]
        }

    elif stat_type == 'rate_limits':
        out = get_complete_ia_rate_limiting_info()
        out["inflight"] = InternetArchiveItem.inflight_task_count()

        r = redis.from_url(settings.CELERY_BROKER_URL)
        out['total_ia_queue'] = r.llen('ia')
        out['total_ia_readonly_queue'] =  r.llen('ia-readonly')

    elif stat_type == 'capture_errors':

        # Set up time ranges
        now = timezone.now()
        last_24_hrs = (
            now - timedelta(days=1),
            now
        )
        previous_24_hrs = (
            now - timedelta(days=2),
            now - timedelta(days=1)
        )
        last_hour = (
            now - timedelta(hours=1),
            now
        )
        last_hour_on_previous_day = (
            now - timedelta(days=1) - timedelta(hours=1),
            now - timedelta(days=1)
        )
        last_3_hrs = (
            now - timedelta(hours=3),
            now
        )
        last_3_hrs_on_previous_day = (
            now - timedelta(days=1) - timedelta(hours=3),
            now - timedelta(days=1)
        )
        ranges = {
            "last_24_hrs": last_24_hrs,
            "previous_24_hrs": previous_24_hrs,
            "last_hour": last_hour,
            "last_hour_on_previous_day": last_hour_on_previous_day,
            "last_3_hrs": last_3_hrs,
            "last_3_hrs_on_previous_day": last_3_hrs_on_previous_day
        }

        out = {}

        for range_name, range_tuple in ranges.items():

            #
            # Get Totals
            #

            completed = CaptureJob.objects.filter(
                engine='scoop-api',
                status='completed',
                capture_start_time__range=range_tuple
            ).count()

            failed = CaptureJob.objects.filter(
                engine='scoop-api',
                status='failed',
                capture_start_time__range=range_tuple
            ).count()

            denominator = completed + failed

            #
            # Get By Error Type
            #
            if denominator:

                celery_timeout = Link.objects.all_with_deleted().filter(
                    tags__name__in=['timeout-failure'],
                    creation_timestamp__range=range_tuple
                ).count()

                proxy_error = Link.objects.all_with_deleted().filter(
                    tags__name__in=['scoop-proxy-failure'],
                    creation_timestamp__range=range_tuple
                ).count()

                blocklist_error = Link.objects.all_with_deleted().filter(
                    tags__name__in=['scoop-blocklist-failure'],
                    creation_timestamp__range=range_tuple
                ).count()

                playwright_error = Link.objects.all_with_deleted().filter(
                    tags__name__in=['scoop-playwright-failure'],
                    creation_timestamp__range=range_tuple
                ).count()

                timeout = Link.objects.all_with_deleted().filter(
                    tags__name__in=['scoop-silent-failure'],
                    creation_timestamp__range=range_tuple
                ).count()

                didnt_load = Link.objects.all_with_deleted().filter(
                    tags__name__in=['scoop-load-failure'],
                    creation_timestamp__range=range_tuple
                ).count()

                out[range_name] = {
                    "completed": completed,
                    "completed_percent": round(completed/denominator * 100, 1),
                    "failed": failed,
                    "failed_percent": round(failed/denominator * 100, 1),
                    "celery_timeout": celery_timeout,
                    "celery_timeout_percent": round(celery_timeout/denominator * 100, 1),
                    "proxy_error": proxy_error,
                    "proxy_error_percent": round(proxy_error/denominator * 100, 1),
                    "blocklist_error": blocklist_error,
                    "blocklist_error_percent": round(blocklist_error/denominator * 100, 1),
                    "playwright_error": playwright_error,
                    "playwright_error_percent": round(playwright_error/denominator * 100, 1),
                    "timeout": timeout,
                    "timeout_percent": round(timeout/denominator * 100, 1),
                    "didnt_load": didnt_load,
                    "didnt_load_percent": round(didnt_load/denominator * 100, 1),
                }

            else:

                out[range_name] = {
                    "completed": 0,
                    "completed_percent": 0,
                    "failed": 0,
                    "failed_percent": 0,
                    "celery_timeout": 0,
                    "celery_timeout_percent": 0,
                    "proxy_error": 0,
                    "proxy_error_percent": 0,
                    "blocklist_error": 0,
                    "blocklist_error_percent": 0,
                    "playwright_error": 0,
                    "playwright_error_percent": 0,
                    "timeout": 0,
                    "timeout_percent": 0,
                    "didnt_load": 0,
                    "didnt_load_percent": 0,
                }

    if out:
        return JsonResponse(out)

    else:
        return render(request, 'admin-stats.html')
