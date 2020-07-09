from django.urls import path
from . import views

urlpatterns = [
    path("",views.LandingPageView.as_view(), name="landing-page"),
    path("home/", views.HomePageView.as_view(), name="index"),
    path("home/<int:pk>",views.BestsellerDetailView.as_view(),name="bestseller-detail"),
    path('books/', views.BookListView.as_view(), name='books'),
    path('book/<uuid:pk>', views.BookDetailView.as_view(), name='book-detail'),
]
## URL for form views
urlpatterns += [
    path('books/add/', views.AddBookToCollection.as_view(), name='add-book'),
]
## URL to delete a book
urlpatterns += [
    path('book/<uuid:pk>/delete/',views.delete_book, name='delete-book'),
]
