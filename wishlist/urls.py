from django.urls import path
from . import views

urlpatterns = [
    path("", views.WishlistListView.as_view(), name="wishlist-initial"),
    path("wishlist_book/<uuid:pk>", views.WishlistDetailView.as_view(), name="wishlist-detail"),
    path("add_book_wishlist",views.AddBookToWishlist.as_view(), name="add-book-wishlist")
]

## URL to delete a book from wishlist
urlpatterns += [
    path('delete/<uuid:pk>',views.DeleteBookWishlist.as_view(), name='delete-book-wishlist'),
]
