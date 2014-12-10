from django.core.urlresolvers import reverse


def new_class(name, *args, **kwargs):
    return type(name, args, kwargs)


# via http://stackoverflow.com/questions/2120813/django-inlinemodeladmin-show-partially-an-inline-model-and-link-to-the-complete
# this could be replaced by show_change_link in DJango 1.8
class InlineEditLinkMixin(object):
    edit_label = "Edit"

    def __init__(self, *args, **kwargs):
        super(InlineEditLinkMixin, self).__init__(*args, **kwargs)
        self.fields = list(self.fields) + ['edit_details']
        self.readonly_fields = list(self.readonly_fields) + ['edit_details']

    def edit_details(self, obj):
        if obj.pk:
            opts = self.model._meta
            return "<a href='%s'>%s</a>" % (reverse(
                'admin:%s_%s_change' % (opts.app_label, opts.object_name.lower()),
                args=[obj.pk]
            ), self.edit_label)
        else:
            return "(save to edit details)"
    edit_details.allow_tags = True