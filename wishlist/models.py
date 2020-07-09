from django.db import models
import uuid
from django.utils import timezone
from catalog.models import Book, Author
from django.contrib.auth.models import User
# Create your models here.
class WishlistBookInstance(models.Model):
    """Model representing a specific copy of a book in wishlist."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, help_text='Unique ID for this particular book across whole library')
    book = models.ForeignKey(Book, on_delete=models.SET_NULL, null=True,blank=True)
    # imprint = models.CharField(max_length=200)
    reason_to_buy = models.TextField(max_length=1000, help_text='Enter a brief description of the book',null=True,blank=True)
    added_on = models.DateField(default=timezone.now, null=True, blank=True)
    book_owner = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        ordering = ['added_on']
        # permissions = (("can_delete_book", "Can delete book instance"),)

    # def get_absolute_url(self):
    #     """Returns the url to access a detail record for this book."""
    #     return reverse('wishlist-book-detail', args=[str(self.id)])

    # def get_delete_url(self):
    #     return reverse('delete-book', args=[str(self.id)])

    def __str__(self):
        """String for representing the Model object."""
        return f'{self.id} ({self.book.title})'
