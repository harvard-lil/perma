from django.test import TestCase
from django.urls import reverse


class BookmarkletServiceTest(TestCase):
    """Test the bookmarklet service endpoint."""
    
    def test_bookmarklet_redirect_simple_url(self):
        """Test bookmarklet redirect with a simple URL."""
        response = self.client.get('/service/bookmarklet-create/', {
            'v': '1',
            'url': 'https://example.com/page'
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/manage/create/?url=https%3A%2F%2Fexample.com%2Fpage')
    
    def test_bookmarklet_redirect_url_with_query(self):
        """Test bookmarklet redirect with URL containing query parameters."""
        response = self.client.get('/service/bookmarklet-create/', {
            'v': '1',
            'url': 'https://example.com/page?search=test&page=2'
        })
        
        self.assertEqual(response.status_code, 302)
        # Query parameters should be encoded
        self.assertIn('url=https%3A%2F%2Fexample.com%2Fpage%3Fsearch%3Dtest%26page%3D2', response.url)
    
    def test_bookmarklet_redirect_url_with_fragment(self):
        """Test bookmarklet redirect with URL containing fragment."""
        response = self.client.get('/service/bookmarklet-create/', {
            'v': '1',
            'url': 'https://example.com/page#section'
        })
        
        self.assertEqual(response.status_code, 302)
        # Fragment should be encoded
        self.assertIn('url=https%3A%2F%2Fexample.com%2Fpage%23section', response.url)
    
    def test_bookmarklet_redirect_without_url(self):
        """Test bookmarklet redirect without URL parameter."""
        response = self.client.get('/service/bookmarklet-create/', {
            'v': '1'
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/manage/create/')
    
    def test_bookmarklet_redirect_empty_url(self):
        """Test bookmarklet redirect with empty URL parameter."""
        response = self.client.get('/service/bookmarklet-create/', {
            'v': '1',
            'url': ''
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/manage/create/')