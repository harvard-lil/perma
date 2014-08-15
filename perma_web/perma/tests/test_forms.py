from django.test import TestCase
from perma.forms import ContactForm

class FormsTestCase(TestCase):

    def test_contact_form(self):
        """
        Cruedely test that we're requiring a message in our
        contact form.
        """
        form_data = {'email': 'test@example.com', 'message': 'some message'}
        form = ContactForm(data=form_data)
        self.assertEqual(form.is_valid(), True)