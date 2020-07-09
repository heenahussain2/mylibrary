from django.contrib import admin
from catalog.models import Book, Author, Genre, Language
from .models import WishlistBookInstance

# Register your models here.
@admin.register(WishlistBookInstance)
class WishlistBookInstanceAdmin(admin.ModelAdmin):
    list_display = ('book', 'book_owner', 'added_on', 'id')
    list_filter = ('book_owner','added_on')
    fieldsets = (
        (None, {
            'fields': ('id','book','reason_to_buy')
        }),
        ('Owner', {
            'fields':('book_owner', 'added_on')
        }),
    )
