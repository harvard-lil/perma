from perma.forms import ContactForm

from .utils import PermaTestCase


class FormsTestCase(PermaTestCase):

    def test_contact_form(self):
        """
        Crudely test that we're requiring a message in our
        contact form.
        """
        form_data = {'email': 'test@example.com', 'message': 'some message'}
        form = ContactForm(data=form_data)
        self.assertEqual(form.is_valid(), True)