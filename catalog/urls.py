from django.urls import path
from . import views

urlpatterns = [
    path("",views.landing_page, name="landing-page"),
    path("home/", views.home_page, name="index"),
    path('books/', views.BookListView.as_view(), name='books'),
    path('book/<uuid:pk>', views.BookDetailView.as_view(), name='book-detail'),
]
## URL for form views
urlpatterns += [
    path('books/add/', views.add_book_collection, name='add-book'),
]
## URL to delete a book
urlpatterns += [
    path('book/<uuid:pk>/delete/',views.delete_book, name='delete-book'),
]
