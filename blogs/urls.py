from django.urls import path
from . import views

urlpatterns = [
    path("",views.BlogLandingPage.as_view(), name="blog-list"),
]
