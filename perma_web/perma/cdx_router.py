class CDXRouter(object):
    """
    A router to control all database operations on cdx models.
    """

    def db_for_read(self, model, **hints):
        """
        Attempts to read cdx models go to perma-cdxline.
        """
        if model.__name__ == 'CDXLine':
            return 'perma-cdxline'
        return None

    def db_for_write(self, model, **hints):
        """
        Attempts to write cdx models go to perma-cdxline.
        """
        if model.__name__ == 'CDXLine':
            return 'perma-cdxline'
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Make sure only cdx models appear in the 'perma-cdxline'
        database.
        """
        if db == 'perma-cdxline':
           return model_name == 'cdxline'
        else:
           return model_name != 'cdxline'
