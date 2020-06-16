from django.urls import path
from . import views

urlpatterns = [
    path("", views.WishlistListView.as_view(), name="wishlist-initial"),
]
