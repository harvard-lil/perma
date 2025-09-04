"""
Tasks for investigating the state of our primary storage and mirrors.
Some reflect earlier Perma storage architectures and are here for
historical purposes and future reference.
"""
from datetime import date, datetime, timezone as tz
from dateutil.relativedelta import relativedelta
import hashlib
from invoke import task
import inspect
import os
from pathlib import Path
import re
import sys
from tqdm import tqdm

from django.conf import settings
from django.core.files.storage import storages
from django.db.models import Q
from django.utils import timezone

from perma.models import Capture, Link
from perma.utils import calculate_s3_etag


def md5hash(path, storage):
    """
    helper function to calculate MD5 hash of a file

    """
    blocksize = 2 ** 20
    m = hashlib.md5()
    with storage.open(path) as f:
        while True:
            buf = f.read(blocksize)
            if not buf:
                break
            m.update(buf)
        return m.hexdigest()


@task
def check_s3_hashes(ctx):
    """
        Confirm that files in primary (disk) storage are also in secondary (s3) storage.

        One-off helper function, kept for example purposes.
    """
    local_cache_path = '/tmp/perma_local_file_list'
    remote_cache_path = '/tmp/perma_remote_file_list'
    remote_paths = {}

    if not os.path.exists(local_cache_path):
        print("Building local state ...")
        local_warc_path = os.path.join(settings.MEDIA_ROOT, settings.WARC_STORAGE_DIR)
        remove_char_count = len(settings.MEDIA_ROOT+1)
        with open(local_cache_path, 'w') as tmp_file:
            for root, subdirs, files in tqdm(os.walk(local_warc_path)):
                for f in files:
                    tmp_file.write(os.path.join(root, f)[remove_char_count:]+"\n")
    else:
        print(f"Using cached local state from {local_cache_path}")

    if not os.path.exists(remote_cache_path):
        print("Building remote state ...")
        remove_char_count = len(settings.SECONDARY_MEDIA_ROOT)
        with open(remote_cache_path, 'w') as tmp_file:
            for f in tqdm(storages[settings.WARC_STORAGE].secondary_storage.bucket.list('generated/warcs/')):
                key = f.key[remove_char_count:]
                val = f.etag[1:-1]
                tmp_file.write(f"{key}\t{val}\n")
                remote_paths[key] = val
    else:
        print(f"Using cached remote state from {remote_cache_path}")
        for line in open(remote_cache_path):
            key, val = line[:-1].split("\t")
            remote_paths[key] = val

    print("Comparing local and remote ...")
    blocksize = 2 ** 20
    for local_path in tqdm(open(local_cache_path)):
        local_path = local_path[:-1]
        if local_path not in remote_paths:
            print("Missing from remote:", local_path)
            continue
        m = hashlib.md5()
        with open(os.path.join(settings.MEDIA_ROOT, local_path), "rb") as f:
            while True:
                buf = f.read(blocksize)
                if not buf:
                    break
                m.update(buf)
        if m.hexdigest() != remote_paths[local_path]:
            print(f"Hash mismatch! Local: {m.hexdigest()} Remote: {remote_paths[local_path]}")


@task
def check_storage(ctx, start_date=None):
    """
        Confirm that, for every link, there is a WARC in each storage, and that their hashes match.

        start_date is in the format YYYY-MM-DD

        Ground truth is the list of link objects: compare its list of warcs with those of each storage,
        and compare hashes when more than one such file is present.

        Derived from check_s3_hashes
    """
    # check the arg
    if not start_date:
        # use first archive date
        start_datetime = Link.objects.order_by('creation_timestamp')[0].creation_timestamp
    elif re.match(r'^\d\d\d\d-\d\d-\d\d$', start_date):
        start_datetime = datetime.strptime(start_date, "%Y-%m-%d").astimezone(tz.utc)
    else:
        print("Bad argument")
        return
    end_datetime = timezone.now()

    # The abstraction of multiple warc storages is an artifact of the
    # transition to S3 for warc storage; although it's conceivable that we'd
    # want multiple warc storages at some point again, there's no need right now
    # to diverge from the Django norm. The abstraction remains here as a
    # point of historical interest.
    warc_storages = {'primary': {'storage': storages[settings.WARC_STORAGE], 'lookup': {}}}

    # only use cache files when all are present: link cache, and one for each storage
    link_cache = '/tmp/perma_link_cache{0}.txt'.format("" if start_date is None else start_date)
    caches = [link_cache]
    for key in warc_storages:
        caches.append('/tmp/perma_storage_cache_{0}{1}.txt'.format(key, "" if start_date is None else start_date))

    if not all(os.path.exists(p) for p in caches):
        print("Building link cache ...")
        with open(link_cache, 'w') as tmp_file:
            capture_filter = (Q(role="primary") & Q(status="success")) | (Q(role="screenshot") & Q(status="success"))
            # assemble list of links by year-month
            start_month = date(year=start_datetime.year, month=start_datetime.month, day=1)
            today = date.today()
            while start_month <= today:
                for link in Link.objects.filter(
                        creation_timestamp__year=start_month.year,
                        creation_timestamp__month=start_month.month,
                        creation_timestamp__gte=start_datetime,
                        creation_timestamp__lt=end_datetime,
                        captures__in=Capture.objects.filter(capture_filter)
                ).distinct():
                    tmp_file.write(f"{link.warc_storage_file()}\n")
                    # this produces strings like u'warcs/0G/GO/XR/XG/0-GGOX-RXGQ.warc.gz'; make the storage paths match
                    # by chopping off the prefix, whether storage.location, ._root_path, or .base_location
                start_month += relativedelta(months=1)

        print("Building storage cache{0} ...".format("s" if len(warc_storages) > 1 else ""))
        for key in warc_storages:
            storage = warc_storages[key]['storage']
            with open('/tmp/perma_storage_cache_{0}{1}.txt'.format(key, "" if start_date is None else start_date), 'w') as tmp_file:
                if hasattr(storage, 'bucket'):
                    # S3
                    for f in storage.bucket.list('generated/warcs/'):
                        if (not start_date) or (start_datetime <= datetime.strptime(f.last_modified, '%Y-%m-%dT%H:%M:%S.%fZ').astimezone(tz.utc) < end_datetime):
                            # here we chop off the prefix aka storage.location
                            path = f.key[(len(storage.location)):]
                            # etag is a string like u'"3ea8c903d9991d466ec437d1789379a6"', so we need to
                            # knock off the extra quotation marks
                            hash = f.etag[1:-1]
                            tmp_file.write(f"{path}\t{hash}\n")
                            warc_storages[key]['lookup'][path] = hash
                else:
                    if hasattr(storage, '_root_path'):
                        # SFTP -- no longer in use, but leaving this here to show that different storages may have
                        # different bases
                        base = storage._root_path
                    else:
                        # local file storage -- are there other possibilities to consider?
                        base = storage.base_location
                    for f in storage.walk(os.path.join(base, 'warcs')):
                        # os.walk: "For each directory in the tree rooted at directory top (including top itself),
                        # it yields a 3-tuple (dirpath, dirnames, filenames)" -- so:
                        for filename in f[2]:
                            full_path = os.path.join(f[0], filename)
                            if (not start_date) or (start_datetime <= storage.modified_time(full_path).astimezone(tz.utc) < end_datetime):
                                # here we chop off the prefix, whether storage._root_path or storage.base_location
                                path = full_path[len(base):]
                                # note that etags are not always md5sums, but should be in these cases; we can rewrite
                                # or replace md5hash if necessary
                                hash = md5hash(full_path, storage)
                                tmp_file.write(f"{path}\t{hash}\n")
                                warc_storages[key]['lookup'][path] = hash
    else:
        print("Reading storage caches ...")
        for key in warc_storages:
            with open('/tmp/perma_storage_cache_{0}{1}.txt'.format(key, "" if start_date is None else start_date)) as f:
                for line in f:
                    path, hash = line[:-1].split("\t")
                    warc_storages[key]['lookup'][path] = hash

    # now check ground truth against storage lookup tables
    print("Comparing link cache against storage caches ...")
    with open(link_cache) as f:
        for line in f:
            path = line[:-1]
            file_present = True
            for key in warc_storages:
                if path not in warc_storages[key]['lookup']:
                    print(f"{path} not in {key}")
                    file_present = False
            if file_present and len(warc_storages) > 1:
                hashes = []
                for key in warc_storages:
                    hashes.append(warc_storages[key]['lookup'][path])
                # this looks funny (and is unnecessary here) but is faster than using set, per
                # http://stackoverflow.com/a/3844948/4074877
                if hashes.count(hashes[0]) != len(hashes):
                    print("Hash mismatch for {0}: {1}".format(path, str(zip(warc_storages.keys(), hashes))))


@task
def sample_objects(ctx, n=1000):
    """
    Produce a sample of archive paths and etags for assessing completeness
    of mirroring; because the comparison happens on the mirror, which doesn't
    know anything about Perma, it produces a Python program to run on the
    mirror.

    The sample size, n, must be of a size to produce at least ten failures,
    given an expected proportion of failures.
    """
    def get_etag(bucket, path):
        return storages[bucket].connection.Object(
            bucket_name=storages[bucket].bucket_name,
            key=os.path.join(settings.MEDIA_ROOT, path)
        ).e_tag.strip('"')

    # obtain a sample of size n
    links = Link.objects.filter(cached_can_play_back=True).order_by("?")[:n]

    # build a list of paths
    objects = [
        {
            "warc": {
                "path": link.warc_storage_file() if link.warc_size else None,
                "etag": None
            },
            "wacz": {
                "path": link.wacz_storage_file() if link.wacz_size else None,
                "etag": None
            }
        }
        for link in links
    ]

    buckets = {
        "warc": settings.WARC_STORAGE,
        "wacz": settings.WACZ_STORAGE
    }

    # add etags
    for o in tqdm(objects):
        for archive in ["warc", "wacz"]:
            if o[archive]["path"]:
                o[archive]["etag"] = get_etag(
                    buckets[archive], o[archive]["path"]
                )

    # write to output file
    timestamp = datetime.isoformat(datetime.now()).replace(":", "")
    filename = f"/tmp/sample-{n}-{timestamp}.py"
    with open(filename, "w") as f:
        f.write("import hashlib\n")
        f.write("import math\n")
        f.write("import sys\n")
        f.write("from pathlib import Path\n")
        f.write("from statistics import NormalDist\n\n")
        f.write(f"objects = {objects}\n")
        f.write(inspect.getsource(calculate_s3_etag))
        f.write(inspect.getsource(check_mirror))
        f.write('if __name__ == "__main__":\n    check_mirror()\n')

    print(f"Sample of size {n} written into script {filename}")
    print("Check it, then copy to the mirror and run it, e.g. with")
    print(f"python3 {filename} {10 / n} <mirror directory> <...>")


def check_mirror():
    """
    This is intended for use on the mirror as a main function.
    The first argument on the command line is the expected proportion of
    failures, expressed as a float.
    The remaining arguments on the command line are directories containing
    the folder "generated".
    """
    p = float(sys.argv[1])
    directories = sys.argv[2:]

    n = len(objects)  # noqa
    if n * p < 10 or n - (n * p) < 10:
        print(f"Sample size of {n} does not satisfy the success/failure condition for p of {p}.")  # noqa
        return

    successes = 0
    failures = 0
    blocksize = 2 ** 20 * 8

    for o in objects:  # noqa
        success = 0
        failure = 0
        for archive in ["warc", "wacz"]:
            if o[archive]["path"]:
                for d in directories:
                    full_path = Path(d) / "generated" / o[archive]["path"]
                    if full_path.exists():
                        with open(full_path, "rb") as f:
                            multipart = "-" in o[archive]["etag"]
                            etag = calculate_s3_etag(f, blocksize, multipart)
                        if etag != o[archive]["etag"]:
                            failure += 1
                            print(
                                f'etag mismatch for {o[archive]["path"]}'
                            )
                        else:
                            success += 1
        if failure or not success:
            failures += 1
        elif not success:
            failures += 1
            print(f'no file found for {o[archive]["path"]}')
        else:
            successes += 1

    # observed proportion
    p_hat = failures / n

    # standard deviation
    sd = math.sqrt((p * (1 - p)) / n)  # noqa

    # z-score
    z = (p_hat - p) / sd

    # area under the standard Normal curve
    probability = NormalDist().cdf(z)  # noqa

    print(f"From a sample of {n} links:")
    print(f"{successes} successes, {failures} failures")
    print(f"Expected proportion is {p}")
    print(f"Standard deviation is {sd}")
    print(f"Observed proportion is {p_hat}")
    print(f"z-score is {z}")
    print(f"Chance of this result is {probability*100:.3f}%")
