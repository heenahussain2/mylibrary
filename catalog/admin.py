from django.contrib import admin
from .models import Author, Genre, Book, Language
from .models import BookInstance
# Register your models here.

#admin.site.register(Book)
# admin.site.register(Author)
admin.site.register(Genre)
#admin.site.register(BookInstance)
admin.site.register(Language)

@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name')
    fields = ['first_name', 'last_name']
# Register the admin class with the associated model
# admin.site.register(Author, AuthorAdmin)
# class BooksInstanceInline(admin.TabularInline):
#     model = BookInstance

# Register the Admin classes for Book using the decorator
@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('id','title', 'author', 'display_genre')
    # list_filter = ('book_owner',)
    # inlines = [BooksInstanceInline]

# Register the Admin classes for BookInstance using the decorator
@admin.register(BookInstance)
class BookInstanceAdmin(admin.ModelAdmin):
    list_display = ('book', 'book_owner', 'added_on', 'id')
    list_filter = ('book_owner','added_on')
    fieldsets = (
        (None, {
            'fields': ('id','book','summary')
        }),
        ('Owner', {
            'fields':('book_owner', 'added_on')
        }),
    )
