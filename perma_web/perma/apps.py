import logging

from django.apps import AppConfig


logger = logging.getLogger(__name__)


class PermaConfig(AppConfig):
    name = 'perma'

    def ready(self):
        # register our signals
        from . import signals  # noqa

        # check timezone config
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("SELECT CONVERT_TZ('2004-01-01 12:00:00','UTC','UTC')")
        if cursor.fetchone()[0] is None:
            print("""
Mysql does not have the UTC time zone configured! Some date queries will not work.
Please run the following as the mysql root user on the database named `mysql`:

    INSERT INTO time_zone (Use_leap_seconds) VALUES ('N');
    SET @time_zone_id= LAST_INSERT_ID();
    INSERT INTO time_zone_name (Name, Time_zone_id) VALUES ('UTC', @time_zone_id);
    INSERT INTO time_zone_transition_type (Time_zone_id, Transition_type_id, Offset, Is_DST, Abbreviation) VALUES
     (@time_zone_id, 0, 0, 0, 'UTC');
""")


