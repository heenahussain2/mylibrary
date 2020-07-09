from django.db import models
from django.urls import reverse # Used to generate URLs by reversing the URL patterns
import uuid # Required for unique book instances
from django.contrib.auth.models import User
from django.utils import timezone
# Create your models here.
class Genre(models.Model):
    """This model represents genre which can store any number of genres.
       we've created the Genre as a model rather than as free text or a selection list so that
       the possible values can be managed through the database rather than being hard coded.
    """
    name = models.CharField(max_length=200, help_text="Enter a book genre (eg.Science Fiction)")

    def __str__(self):
        """String for representing the Model object."""
        return self.name

class Language(models.Model):
    """Model representing a Language (e.g. English, French, Japanese, etc.)"""
    name = models.CharField(max_length=200,
                            help_text="Enter the book's natural language (e.g. English, French, Japanese etc.)")

    def __str__(self):
        """String for representing the Model object (in Admin site etc.)"""
        return self.name

class Book(models.Model):
    """Model representing a book (but not a specific copy of a book)."""
    title = models.CharField(max_length=200)

    # Foreign Key used because book can only have one author, but authors can have multiple books
    # Author as a string rather than object because it hasn't been declared yet in the file
    # id = models.UUIDField(primary_key=True, default=uuid.uuid4, help_text='Unique ID for this particular book across whole library')

    author = models.ForeignKey('Author', on_delete=models.SET_NULL, null=True)
    isbn = models.CharField('ISBN', max_length=13, help_text='13 Character <a href="https://www.isbn-international.org/content/what-isbn">ISBN number</a>')
    # ManyToManyField used because genre can contain many books. Books can cover many genres.
    # Genre class has already been defined so we can specify the object above.
    genre = models.ManyToManyField('Genre', help_text='Select a genre for this book')
    # Genre class has already been defined so we can specify the object above.
    language = models.ForeignKey('Language', on_delete=models.SET_NULL, null=True)
    # book_owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        permissions = (("can_add_book", "Can add book"),)

    def __str__(self):
        """String for representing the Model object."""
        return self.title

    def get_absolute_url(self):
        """Returns the url to access a detail record for this book."""
        return reverse('book-detail', args=[str(self.id)])

    def get_bestseller_url(self):
        """Returns the url to access a detail record for a bestseller book."""
        return reverse('bestseller-detail', args=[str(self.id)])

    def display_genre(self):
        """Create a string for the Genre. This is required to display genre in Admin."""
        return ', '.join(genre.name for genre in self.genre.all()[:3])

    display_genre.short_description = 'Genre'

class BookInstance(models.Model):
    """Model representing a specific copy of a book (i.e. that can be borrowed from the library)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, help_text='Unique ID for this particular book across whole library')
    book = models.ForeignKey('Book', on_delete=models.SET_NULL, null=True,blank=True)
    # imprint = models.CharField(max_length=200)
    summary = models.TextField(max_length=1000, help_text='Enter a brief description of the book',null=True,blank=True)
    # due_back = models.DateField(null=True, blank=True)
    added_on = models.DateField(default=timezone.now, null=True, blank=True)
    book_owner = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    # LOAN_STATUS = (
    #     ('m', 'Maintenance'),
    #     ('o', 'On loan'),
    #     ('a', 'Available'),
    #     ('r', 'Reserved'),
    # )
    #
    # status = models.CharField(
    #     max_length=1,
    #     choices=LOAN_STATUS,
    #     blank=True,
    #     default='m',
    #     help_text='Book availability',
    # )

    class Meta:
        ordering = ['added_on']
        permissions = (("can_delete_book", "Can delete book instance"),)

    def get_absolute_url(self):
        """Returns the url to access a detail record for this book."""
        return reverse('book-detail', args=[str(self.id)])

    def get_delete_url(self):
        return reverse('delete-book', args=[str(self.id)])

    def __str__(self):
        """String for representing the Model object."""
        return f'{self.id} ({self.book.title})'

class Author(models.Model):
    """Model representing an author."""
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    # date_of_birth = models.DateField(null=True, blank=True)
    # date_of_death = models.DateField('Died', null=True, blank=True)

    class Meta:
        ordering = ['first_name', 'last_name']

    def get_absolute_url(self):
        """Returns the url to access a particular author instance."""
        return reverse('author-detail', args=[str(self.id)])

    def __str__(self):
        """String for representing the Model object."""
        return f'{self.first_name} {self.last_name}'
