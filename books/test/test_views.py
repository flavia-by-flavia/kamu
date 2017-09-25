import json

from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from books.models import Book, Library, BookCopy


# VIEWS

class BookCopyAutocompleteView(TestCase):
    def setUp(self):
        self.client = Client()
        self.endpoint = reverse('book-autocomplete')

    def test_endpoint_working(self):
        """Tests if the endpoint book-autocomplete/ is working"""
        response = self.client.get(self.endpoint)

        self.assertEqual(200, response.status_code)

    def test_user_not_logged_in(self):
        """Tests if request that has no user logged in returns nothing"""
        response = self.client.get(self.endpoint)

        response = json.loads(response.content)

        # Asserts that no result is returned
        self.assertTrue(len(response.get('results')) == 0)
        self.assertFalse(response.get('pagination').get('more'))

    def test_user_logged_in_receives_result(self):
        """Tests if a user can receive results when logged in"""

        # creates and logs user
        self.user = User.objects.create_user(username="user")
        self.user.set_password("user")
        self.user.save()
        self.client.force_login(user=self.user)

        # saves a library
        self.library = Library.objects.create(name="Santiago", slug="slug")

        # saves a new book
        title = "the title of my new super book"
        self.book = Book.objects.create(author="Author", title=title, subtitle="The subtitle",
                                        publication_date=timezone.now())

        # creates a book copy
        self.bookCopy = BookCopy.objects.create(book=self.book, library=self.library)

        response = self.client.get(self.endpoint)

        self.assertContains(response, title)


class BookCopyBorrowViewCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="claudia")
        self.user.set_password("123")
        self.user.save()
        self.client.force_login(user=self.user)

    def test_user_can_borrow_book_copy(self):
        self.book = Book.objects.create(author="Author", title="the title", subtitle="The subtitle",
                                        publication_date=timezone.now())
        self.library = Library.objects.create(name="Santiago", slug="slug")
        self.bookCopy = BookCopy.objects.create(book=self.book, library=self.library)

        self.request = self.client.post('/api/copies/' + str(self.bookCopy.id) + "/borrow")

        self.assertEqual(200, self.request.status_code)
        self.assertTrue(str(self.request.data).__contains__("Book borrowed"))

        book_copy = BookCopy.objects.get(pk=self.bookCopy.id)
        self.assertEqual(self.user, book_copy.user)
        self.assertIsNotNone(book_copy.borrow_date)

    def test_shouldnt_borrow_book_copy_when_invalid_id(self):
        self.request = self.client.post('/api/copies/' + str(99) + "/borrow")
        self.assertEqual(404, self.request.status_code)


class BookCopyReturnView(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="claudia")
        self.user.set_password("123")
        self.user.save()
        self.client.force_login(user=self.user)

    def test_user_can_return_book_copy(self):
        self.book = Book.objects.create(author="Author", title="the title", subtitle="The subtitle",
                                        publication_date=timezone.now())
        self.library = Library.objects.create(name="Santiago", slug="slug")
        self.bookCopy = BookCopy.objects.create(book=self.book, library=self.library, user=self.user,
                                                borrow_date=timezone.now())

        self.request = self.client.post('/api/copies/' + str(self.bookCopy.id) + '/return')

        self.assertEqual(self.request.status_code, 200)
        self.assertTrue(str(self.request.data).__contains__("Book returned"))

        book_copy = BookCopy.objects.get(pk=self.bookCopy.id)

        self.assertEqual(None, book_copy.user)
        self.assertIsNone(book_copy.borrow_date)

    def test_shouldnt_return_book_copy_when_invalid_id(self):
        self.request = self.client.post('/api/copies/' + str(99) + "/return")
        self.assertEqual(404, self.request.status_code)


class LibraryViewSet(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="claudia")
        self.user.set_password("123")
        self.user.save()
        self.client.force_login(user=self.user)

        self.book = Book.objects.create(author="Author", title="the title", subtitle="The subtitle",
                                        publication_date=timezone.now())
        self.library = Library.objects.create(name="Santiago", slug="slug")
        self.bookCopy = BookCopy.objects.create(book=self.book, library=self.library)

    def test_user_can_retrieve_library_information_with_existing_slug(self):
        self.request = self.client.get("/api/libraries/" + self.library.slug + "/")

        self.assertEqual(self.request.status_code, 200)

        library_json = json.loads(json.dumps(self.request.data))

        self.assertEqual(self.library.name, library_json['name'])
        self.assertEqual(self.library.slug, library_json['slug'])

        print(library_json)

        # Get the books
        self.request = self.client.get(library_json['books'])

        self.assertEqual(self.request.status_code, 200)

        library_json = json.loads(json.dumps(self.request.data))
        print(library_json["results"][0])

        self.assertEqual(1, library_json['count'])
        self.assertEqual(1, len(library_json['results'][0]['copies']))


class UserView(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="claudia")
        self.user.set_password("123")
        self.user.save()
        self.client.force_login(user=self.user)

    def test_user_should_be_able_to_see_its_own_profile(self):
        self.request = self.client.get("/api/profile")
        user_json = json.loads(json.dumps(self.request.data))

        self.assertEqual(self.user.username, user_json['user']['username'])
