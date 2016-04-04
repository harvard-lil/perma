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

    # def allow_relation(self, obj1, obj2, **hints):
    #     """
    #     Allow relations if a model in the cdx app is involved.
    #     """
    #     print "allow_relation: getting model?", obj1, obj2, hints
    #     if obj1._meta.app_label == 'cdx' or \
    #        obj2._meta.app_label == 'cdx':
    #        return True
    #     return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Make sure only cdx models appear in the 'cdx_db'
        database.
        """
        if model_name == 'cdxline':
            return db == 'cdx_db'
        return None
