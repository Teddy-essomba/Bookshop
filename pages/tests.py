# ==========================================================================
# pages/tests.py  |  Bookshop — file guide
# ==========================================================================
# Automated tests for the API.  Run them with:
#
#     python manage.py test
#
# Django spins up a throwaway database for the run and destroys it after, so
# these never touch db.sqlite3.
#
# APIClient is DRF's version of Django's test Client -- it knows how to send
# JSON and how to attach credentials.
#
# Covered here:
#   - reading is public, writing is not          (IsAuthenticatedOrReadOnly)
#   - the ?year= / ?title= filters actually work (they used to 500)
#   - the JWT carries our custom claims          (they used to be dropped)
#   - a reading list is private to its owner     (row-level security)
#   - serializer validation rejects bad data
# ==========================================================================

import base64
import json

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from .models import Author, Book, ReadingListItem


def claims_of(access_token):
    """Decode a JWT payload without verifying it -- fine inside a test."""
    payload = access_token.split('.')[1]
    payload += '=' * (-len(payload) % 4)          # re-pad for base64
    return json.loads(base64.urlsafe_b64decode(payload))


class BookAPITests(TestCase):
    def setUp(self):
        # A fresh, unauthenticated client is initialized before every test case
        self.client = APIClient()
        self.user = User.objects.create_user('alice', 'a@example.com', 'pw12345!')
        self.author = Author.objects.create(
            name='J.R.R. Tolkien', birth_year=1892, country='UK'
        )
        self.book = Book.objects.create(
            title='The Hobbit', year_published=1937,
            author=self.author, category='fantasy', added_by=self.user,
        )

    def auth(self):
        """Log in over the API and attach the access token to the client."""
        r = self.client.post(
            '/api/token/',
            {'username': 'alice', 'password': 'pw12345!'},
            format='json',
        )
        self.assertEqual(r.status_code, 200)
        # Fixes the authorization header on the client for subsequent requests
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + r.data['access'])
        return r.data['access']

    def test_anyone_can_read_books(self):
        # Verifies the GET endpoint is public (unauthenticated client can access)
        r = self.client.get('/api/books/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.data), 1)

    def test_anonymous_cannot_create(self):
        # Verifies POST endpoint requires authentication
        r = self.client.post(
            '/api/books/',
            {'title': 'Dune', 'year_published': 1965, 'author': self.author.id},
            format='json',
        )
        self.assertEqual(r.status_code, 401)

    def test_year_filter(self):
        """Regression test: this raised FieldError when it filtered on `year`."""
        self.assertEqual(len(self.client.get('/api/books/?year=1937').data), 1)
        self.assertEqual(len(self.client.get('/api/books/?year=1999').data), 0)

    def test_title_filter_is_case_insensitive(self):
        self.assertEqual(len(self.client.get('/api/books/?title=hObB').data), 1)

    def test_added_by_is_set_from_the_request(self):
        """The client cannot claim authorship -- the server decides."""
        self.auth()
        r = self.client.post(
            '/api/books/',
            {'title': 'Dune', 'year_published': 1965,
             'author': self.author.id, 'added_by': 999},
            format='json',
        )
        self.assertEqual(r.status_code, 201)
        # Proves the backend ignored 'added_by': 999 and used the request user instead
        self.assertEqual(Book.objects.get(pk=r.data['id']).added_by, self.user)

    def test_year_out_of_range_is_rejected(self):
        # Validates custom business rules (min/max bounds check) in serializer
        self.auth()
        r = self.client.post(
            '/api/books/',
            {'title': 'X', 'year_published': 800, 'author': self.author.id},
            format='json',
        )
        self.assertEqual(r.status_code, 400)
        self.assertIn('year_published', r.data)

    def test_book_cannot_predate_its_author(self):
        # Validates cross-field dependency checks in backend validation
        self.auth()
        r = self.client.post(
            '/api/books/',
            {'title': 'X', 'year_published': 1850, 'author': self.author.id},
            format='json',
        )
        self.assertEqual(r.status_code, 400)


class TokenTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        User.objects.create_user('bob', 'b@example.com', 'pw12345!', is_staff=True)

    def test_token_carries_custom_claims(self):
        """
        Regression test: a duplicate 'api/token/' route used to shadow
        CustomTokenObtainPairView, so these claims never appeared.
        """
        r = self.client.post(
            '/api/token/',
            {'username': 'bob', 'password': 'pw12345!'},
            format='json',
        )
        self.assertEqual(r.status_code, 200)
        # Decodes token payload to ensure extra user contexts are encoded directly inside it
        c = claims_of(r.data['access'])
        self.assertEqual(c['username'], 'bob')
        self.assertEqual(c['email'], 'b@example.com')
        self.assertTrue(c['is_staff'])


class ReadingListTests(TestCase):
    """Row-level security: two users must never see each other's lists."""

    def setUp(self):
        self.client = APIClient()
        self.alice = User.objects.create_user('alice', 'a@example.com', 'pw12345!')
        self.bob = User.objects.create_user('bob', 'b@example.com', 'pw12345!')
        author = Author.objects.create(name='A', birth_year=1900, country='IE')
        self.book = Book.objects.create(title='B', year_published=1950, author=author)
        # Alice starts with 1 item in her list; Bob's list starts empty
        self.alice_item = ReadingListItem.objects.create(
            user=self.alice, book=self.book, notes='mine'
        )

    def login(self, username):
        """Helper to switch active user contexts mid-test."""
        r = self.client.post(
            '/api/token/',
            {'username': username, 'password': 'pw12345!'},
            format='json',
        )
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + r.data['access'])

    def test_endpoint_exists(self):
        """Regression test: the viewset was never registered, so this 404'd."""
        self.login('alice')
        self.assertEqual(self.client.get('/api/reading-list/').status_code, 200)

    def test_anonymous_is_rejected(self):
        self.assertEqual(self.client.get('/api/reading-list/').status_code, 401)

    def test_list_shows_only_your_own_items(self):
        # Bob should see 0 items (row-level isolation verification)
        self.login('bob')
        self.assertEqual(len(self.client.get('/api/reading-list/').data), 0)

        # Alice should see 1 item
        self.login('alice')
        self.assertEqual(len(self.client.get('/api/reading-list/').data), 1)

    def test_cannot_fetch_someone_elses_item_by_id(self):
        # Blocks guessing individual asset IDs belonging to other users
        self.login('bob')
        r = self.client.get(f'/api/reading-list/{self.alice_item.id}/')
        self.assertIn(r.status_code, (403, 404))

    def test_owner_is_set_from_the_request(self):
        self.login('bob')
        r = self.client.post(
            '/api/reading-list/',
            {'book': self.book.id, 'notes': 'bobs', 'priority': 2},
            format='json',
        )
        self.assertEqual(r.status_code, 201)
        self.assertEqual(ReadingListItem.objects.get(pk=r.data['id']).user, self.bob)

    def test_cannot_save_the_same_book_twice(self):
        # Verifies unique-together constraint on user + book fields
        self.login('alice')
        r = self.client.post(
            '/api/reading-list/',
            {'book': self.book.id, 'notes': 'again', 'priority': 1},
            format='json',
        )
        self.assertEqual(r.status_code, 400)
        self.assertEqual(len(self.client.get('/api/reading-list/').data), 1)
