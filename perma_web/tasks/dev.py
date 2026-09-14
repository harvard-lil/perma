from datetime import datetime, timedelta
from invoke import task
import json
import os
import requests
import signal
import subprocess
import sys
from tqdm import tqdm

from django.conf import settings
from django.http import HttpRequest
from django.utils import timezone

from perma.email import send_user_email, send_self_email, registrar_users, registrar_users_plus_stats
from perma.models import Link, LinkUser, Registrar, CaptureJob
from perma.utils import DEFAULT_IA_UPLOAD_HEALTH_SPAN_DAYS, build_ia_upload_health_report

import logging
logger = logging.getLogger(__name__)


@task
def run(ctx, port="0.0.0.0:8000", cert_file='perma-test.crt', key_file='perma-test.key', debug_toolbar=False):
    """
        Run django test server on open port, so it's accessible outside Docker.

        Use runserver_plus for SSL.
    """
    commands = []

    if settings.CELERY_TASK_ALWAYS_EAGER:
        print("\nWarning! Batch Link creation will not work as expected:\n" +
              "to create new batches you should run with settings.CELERY_TASK_ALWAYS_EAGER = False\n")
    else:
        print("\nStarting background celery process.")
        commands.append("watchmedo auto-restart -d ./ -p '*.py' -R -- celery -A perma worker --loglevel=info -Q celery,background,ia,ia-readonly,wacz-conversion -B -n w1@%h")

    # Only run the webpack background process in debug mode -- with debug False, dev server uses static assets,
    # and running webpack just messes up the webpack stats file.
    if settings.DEBUG:
        commands.append('npm start')

    proc_list = [subprocess.Popen(command, shell=True, stdout=sys.stdout, stderr=sys.stderr) for command in commands]

    with ctx.prefix(f'export DEBUG_TOOLBAR={"1" if debug_toolbar else ""}'):

        try:
            # use runserver_plus
            import django_extensions  # noqa
            if not os.path.exists(os.path.join(settings.PROJECT_ROOT, cert_file)) or not os.path.exists(os.path.join(settings.PROJECT_ROOT, key_file)):
                print("\nError! The required SSL cert and key files are missing. See developer.md for instructions on how to generate.")
                return
            options = f'--cert-file {cert_file} --key-file {key_file} --keep-meta-shutdown'
            ctx.run(f"python manage.py runserver_plus {port} {options}")
        finally:
            for proc in proc_list:
                os.kill(proc.pid, signal.SIGKILL)


@task
def lock(ctx, args=''):
    ctx.run(
        f'uv lock {args} && uv export --format requirements.txt -o requirements.txt',
        echo=True,
    )


@task
def init_db(ctx):
    """
        Apply migrations and import fixtures for new dev database.
    """
    ctx.run("python manage.py migrate")
    ctx.run("python manage.py loaddata fixtures/sites.json fixtures/users.json fixtures/folders.json")


@task
def report_ia_upload_health(
    ctx,
    mode='auto',
    auto_detail_max_days=10,
    span_days=DEFAULT_IA_UPLOAD_HEALTH_SPAN_DAYS,
    span_start='',
    span_end='',
):
    """
    Report Internet Archive daily upload backlog health as JSON.

    Output is grouped by scope:
      span — the analysis period (start, end, days)
      global — metrics across all time (not limited to span)
      in_span — metrics limited to span

    Span (pick one style):
      span_days=10 (default) — last 10 days ending today, with per-day detail
      span_days=90 --span-start DATE — N days starting on that date
      span_days=90 --span-end DATE — N days ending on that date
      span_start + span_end — explicit range (span_days ignored)
      span_days=all — full daily-item dataset (backlog floor through today by
        default; combine with span_start and/or span_end to adjust). May be expensive.

    mode:
      auto (default) — per-day breakdown when the count of in-span days with initial_uploads_incomplete
        and in-span missing days are both <= auto_detail_max_days; otherwise aggregate only
      detailed — always per-day breakdown for the span
      summary — always aggregate counts for the span

    Examples:
      invoke report-ia-upload-health
      invoke report-ia-upload-health --span-days 90 --span-start 2010-01-01
      invoke report-ia-upload-health --span-days 90 --span-end 2015-06-01
      invoke report-ia-upload-health --span-start 2010-01-01 --span-end 2010-06-30
      invoke report-ia-upload-health --span-days all --mode summary
      invoke report-ia-upload-health --span-days all --span-start 2022-01-01
    """
    report = build_ia_upload_health_report(
        mode=mode,
        auto_detail_max_days=auto_detail_max_days,
        span_days=span_days,
        span_start=span_start or None,
        span_end=span_end or None,
    )
    print(json.dumps(report, indent=2))


@task
def count_links_without_cached_playback_status(ctx):
    """
    For use in monitoring the size of the queue.
    """
    count = Link.objects.permanent().filter(cached_can_play_back__isnull=True).count()
    print(count)


@task
def capture_queue_health(ctx, quiet=False, window=50, max_uncompleted=25, stuck_minutes=20, max_stuck=25):
    """
    Report on whether captures are completing, flagging two conditions:

      1. Of the most recently created {window} links, how many still have a
         capture (other than a user upload) in the 'pending' state. This is the
         original status.perma.cc/monitor heuristic -- a snapshot of whether
         recent captures are succeeding right now -- and fires when more than
         {max_uncompleted} of them are unfinished. This can happen the moment 50
         links are submitted, even in a healthy queue.
      2. How many CaptureJobs are old enough to have finished but are still
         pending/in_progress: fires when
         more than {max_stuck} jobs have been unfinished for over
         {stuck_minutes} minutes.

    Report if *either* condition is exceeded.
    With --quiet (for cron/alerting) print nothing unless something is wrong;
    otherwise print both numbers for a human.
    """
    # 1. Recent-window pending snapshot (original /monitor heuristic).
    recent_link_ids = list(
        Link.objects.order_by('-creation_timestamp')
        .values_list('pk', flat=True)[:window]
    )
    uncompleted = Link.objects.filter(
        pk__in=recent_link_ids,
        captures__status='pending',
        captures__user_upload=False,
    ).distinct().count()

    # 2. Stuck jobs: too old to still be unfinished. Age comes from
    # Link.creation_timestamp (write-once); CaptureJob.creation_timestamp is
    # auto_now and so tracks last save, not submission.
    cutoff = timezone.now() - timedelta(minutes=stuck_minutes)
    stuck = CaptureJob.objects.filter(
        status__in=['pending', 'in_progress'],
        link__creation_timestamp__lt=cutoff,
    ).count()

    problems = []
    if uncompleted > max_uncompleted:
        problems.append(f"{uncompleted} uncompleted captures in the most recent {window}")
    if stuck > max_stuck:
        problems.append(f"{stuck} captures unfinished for over {stuck_minutes} minutes")

    if problems:
        print("; ".join(problems))
    elif not quiet:
        print(f"OK: {uncompleted} uncompleted in last {window}, {stuck} unfinished over {stuck_minutes} min")


@task
def ping_all_users(ctx, limit_to="", exclude="", batch_size=500):
    '''
       Sends an email to all our current users. See templates/email/special.txt

       Arguments should be strings, with multiple values separated by semi-colons
       e.g. invoke ping-all-users --limit-to "14;27;30" --batch-size 1000

       Limit filters are applied before exclude filters.
    '''
    logger.info("BEGIN: ping_all_users")

    # load desired Perma users
    if limit_to:
        users = LinkUser.objects.filter(id__in=limit_to.split(";"))
    else:
        users = LinkUser.objects.filter(is_confirmed=True, is_active=True)
    if exclude:
        users = users.exclude(id__in=exclude.split(";"))

    # exclude users we have already emailed
    already_emailed_path = '/tmp/perma_emailed_user_list'
    already_emailed = set()
    if os.path.exists(already_emailed_path):
        logging.info("Loading list of already-emailed users.")
        with open(already_emailed_path) as f:
            lines = f.read().splitlines()
            for line in lines:
                already_emailed.add(int(line))
    if already_emailed:
        users = users.exclude(id__in=already_emailed)

    # limit to our desired batch size
    not_yet_emailed = users.count()
    if not_yet_emailed > batch_size:
        logger.info(f"{not_yet_emailed} users to email: limiting to first {batch_size}")
        users = users[:batch_size]

    to_send_count = users.count()
    if not to_send_count:
        logger.info("No users to email.")
        return

    sent_count = 0
    failed_list = []
    logger.info(f"Begin emailing {to_send_count} users.")
    with open(already_emailed_path, 'a') as f:
        for user in tqdm(users):
            succeeded = send_user_email(user.raw_email,
                                        'email/special.txt',
                                         {'user': user})
            if succeeded:
                sent_count += 1
                f.write(str(user.id)+"\n")
            else:
                failed_list.append(user.id)

    logger.info(f"Emailed {sent_count} users")
    if to_send_count != sent_count:
        if failed_list:
            msg = f"Some users were not emailed: {str(failed_list)}. Check log for fatal SMTP errors."
        else:
            msg = "Some users were not emailed. Check log for fatal SMTP errors."
        logger.error(msg)

    # offer to send another batch if there are any users left to email
    remaining_to_email = not_yet_emailed - sent_count
    if remaining_to_email:
        if input(f"\nSend another batch of size {batch_size}? [y/n]\n").lower() == 'y':
            ping_all_users(batch_size=str(batch_size))
        else:
            logger.info(f"Stopped with ~ {remaining_to_email} remaining users to email")
    else:
        logger.info("Done! Run me again, to catch anybody who signed up while this was running!")


@task
def ping_registrar_users(ctx, limit_to="", limit_by_tag="", exclude="", exclude_by_tag="", email="stats", year=""):
    '''
       Sends an email to our current registrar users. See templates/email/registrar_user_ping.txt

       Arguments should be strings, with multiple values separated by semi-colons
       e.g. invoke dev.ping-registrar-users --limit-to "14;27;30" --exclude-by-tag "opted_out" --email "special"

       Limit filters are applied before exclude filters.
    '''
    registrars = Registrar.objects.all()
    if limit_to:
        registrars = registrars.filter(id__in=limit_to.split(";"))
    if limit_by_tag:
        registrars = registrars.filter(tags__name__in=limit_by_tag.split(";")).distinct()
    if exclude:
        registrars = registrars.exclude(id__in=exclude.split(";"))
    if exclude_by_tag:
        registrars = registrars.exclude(tags__name__in=exclude_by_tag.split(";")).distinct()
    if year:
        year = int(year)
    else:
        year = datetime.now().year - 1

    if email == 'stats':
        template = 'email/registrar_user_ping.txt'
        users = registrar_users_plus_stats(registrars=registrars, year=year)
    elif email == 'special':
        # update special template as desired, to send one-off emails
        # update email.registrar_users if you need more context variables
        template = 'email/special.txt'
        users = registrar_users(registrars=registrars)
    else:
        NotImplementedError()

    logger.info("Begin emailing registrar users.")
    send_count = 0
    failed_list = []
    for user in tqdm(users):
        context = {}
        context.update(user)
        context["year"] = year
        succeeded = send_user_email(user['raw_email'],
                                    template,
                                     context)
        if succeeded:
            send_count += 1
        else:
            failed_list.append(user.id)

    # Another option is to use Django's send_mass_email.
    # It's unclear which would be more performant in real life.
    # send_count = send_mass_user_email('email/registrar_user_ping.txt',
    #                                   [(user['email'], user) for user in users])
    logger.info("Done emailing registrar users.")
    if len(users) != send_count:
        if failed_list:
            msg = f"Some registrar users were not emailed: {failed_list}. Check log for fatal SMTP errors."
        else:
            msg = "Some registrar users were not emailed. Check log for fatal SMTP errors."
        logger.error(msg)
        result = "incomplete"
    else:
        result = "ok"
    send_self_email("Registrar Users Emailed",
                     HttpRequest(),
                     'email/admin/pinged_registrar_users.txt',
                     {"users": users, "result": result})
    return json.dumps({"result": result, "send_count": send_count})


@task
def update_cloudflare_cache(ctx):
    """ Update Cloudflare IP lists. """
    for ip_filename in ('ips-v4', 'ips-v6'):
        with open(os.path.join(settings.CLOUDFLARE_DIR, ip_filename), 'w') as ip_file:
            ip_file.write(requests.get(f'https://www.cloudflare.com/{ip_filename}').text)
