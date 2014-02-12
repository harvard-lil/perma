import sys
sys.path.append("..")

from perma import settings
from django.core.management import setup_environ
from django.forms.models import model_to_dict
from datetime import datetime

setup_environ(settings)

from perma.models import Asset, Stat, Registrar, LinkUser, Link, VestingOrg

"""
A little utility that will generate usage stats, using our stats model for the 
past seven days.
"""

def print_stats_line(current_stats, previous_stats, stats_name, metric):
    print "%s %s added. From %s to %s." % (current_stats[metric] - previous_stats[metric], stats_name, previous_stats[metric], current_stats[metric])

# Get the last seven stats entries, then get last one. This feels so clunky.
previous_stats_query_set = Stat.objects.order_by('-creation_timestamp')[:8][7]
current_stats_query_set = Stat.objects.filter().latest('creation_timestamp')

format = '%b %d, %Y, %H:%M %p'

print "###########################"
print "For the team "
print "###########################"

print "Perma.cc weekly numbers."
print "From %s through %s" % (previous_stats_query_set.creation_timestamp.strftime(format), current_stats_query_set.creation_timestamp.strftime(format))
print

# Convert querysets to dicts so that we can access them easily in our print_stats_line util
previous_stats = model_to_dict(previous_stats_query_set)
current_stats = model_to_dict(current_stats_query_set)

# Users
print "## The Folks"
print_stats_line(current_stats, previous_stats, 'regular users', 'regular_user_count')
print_stats_line(current_stats, previous_stats, 'vesting members', 'vesting_member_count')
print_stats_line(current_stats, previous_stats, 'vesting managers', 'vesting_manager_count')
print_stats_line(current_stats, previous_stats, 'registrar members', 'registrar_member_count')
print_stats_line(current_stats, previous_stats, 'registry members', 'registry_member_count')
print

# Vesting Orgs
print "## The Vesting Organizations"
print_stats_line(current_stats, previous_stats, 'vesting organizations', 'vesting_org_count')
print

# Libraries
print "## The Libraries"
print_stats_line(current_stats, previous_stats, 'libraries', 'registrar_count')
print

# Hits
print "## The Hits"
print "n unique visitors to all of Perma.cc"
print "n unique page views to all of Perma.cc"
print

# Links
print "## The Links"
print_stats_line(current_stats, previous_stats, 'unvested links', 'unvested_count')
print_stats_line(current_stats, previous_stats, 'vested links', 'vested_count')
print_stats_line(current_stats, previous_stats, 'takedown related, darchived links', 'darchive_takedown_count')
print_stats_line(current_stats, previous_stats, 'robots.txt or meta noarchive related, darchived links', 'darchive_robots_count')
print

# Storage
print "## The Storage"
# Since we do some formatting, we don't use our helper function for this.
print "%.2fGB %s. From %.2fGB to %.2fGB." % (float(current_stats['disk_usage'] - previous_stats['disk_usage'])/1024/1024/1024, 'disk space used', float(previous_stats['disk_usage'])/1024/1024/1024, float(current_stats['disk_usage'])/1024/1024/1024)
print


print "###########################"
print "For the partners "
print "###########################"

print "Perma.cc weekly numbers."
print "From %s through %s" % (previous_stats_query_set.creation_timestamp.strftime(format), current_stats_query_set.creation_timestamp.strftime(format))
print

# Users
print "## The Folks"
print_stats_line(current_stats, previous_stats, 'regular users', 'regular_user_count')
print_stats_line(current_stats, previous_stats, 'vesting members', 'vesting_member_count')
print_stats_line(current_stats, previous_stats, 'vesting managers', 'vesting_manager_count')
print_stats_line(current_stats, previous_stats, 'registrar members', 'registrar_member_count')
print

# Vesting Orgs
print "## The Vesting Organizations"
print_stats_line(current_stats, previous_stats, 'vesting organizations', 'vesting_org_count')
print

# Libraries
print "## The Libraries"
print_stats_line(current_stats, previous_stats, 'libraries', 'registrar_count')
print

# Hits
print "## The Hits"
print "n unique visitors to all of Perma.cc"
print "n unique page views to all of Perma.cc"
print

# Links
print "## The Links"
print_stats_line(current_stats, previous_stats, 'unvested links', 'unvested_count')
print_stats_line(current_stats, previous_stats, 'vested links', 'vested_count')
print

# Storage
print "## The Storage"
# Since we do some formatting, we don't use our helper function for this.
print "%.2fGB %s. From %.2fGB to %.2fGB." % (float(current_stats['disk_usage'] - previous_stats['disk_usage'])/1024/1024/1024, 'disk space used', float(previous_stats['disk_usage'])/1024/1024/1024, float(current_stats['disk_usage'])/1024/1024/1024)
print
