class CDXRouter(object):
    """
    A router to control all database operations on cdx models.
    """

    def db_for_read(self, model, **hints):
        """
        Attempts to read cdx models go to cdx_db.
        """
        if model.__name__ == 'CDXLine':
            return 'cdx_db'
        return None

    def db_for_write(self, model, **hints):
        """
        Attempts to write cdx models go to cdx_db.
        """
        if model.__name__ == 'CDXLine':
            return 'cdx_db'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """
        Return True if a relation between obj1 and obj2 should be allowed
        False if the relation should be prevented
        or None if the router has no opinion.
        This is purely a validation operation, used by foreign key
        and many to many operations to determine
        if a relation should be allowed between two objects.
        """
        if 'target_db' in hints:
            return db == hints['target_db']
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Make sure only cdx models appear in the 'cdx_db'
        database.
        """
        if model_name == 'cdxline':
            return db == 'cdx_db'
        return None
