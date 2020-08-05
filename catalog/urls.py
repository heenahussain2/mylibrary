from django.urls import path
from . import views

urlpatterns = [
    path("",views.LandingPageView.as_view(), name="landing-page"),
    path("home/", views.HomePageView.as_view(), name="index"),
    path("nytbestseller/<str:genre>", views.NytBestsellerView.as_view(), name="bestseller-list"),
    path("nytbestseller/<str:genre>/<str:isbn>",views.BestsellerDetailView.as_view(),name="bestseller-detail"),
    path('books/', views.BookListView.as_view(), name='books'),
    path('book/<uuid:pk>', views.BookDetailView.as_view(), name='book-detail'),
    path("home/recently_added/<uuid:pk>", views.BookDetailView.as_view(), name="recently-added-details"),
]
## URL for form views
urlpatterns += [
    path('books/add/', views.AddBookToCollection.as_view(), name='add-book'),
]
## URL to delete a book
urlpatterns += [
    path('book/delete/<uuid:pk>',views.DeleteBookView.as_view(), name='delete-book'),
]
