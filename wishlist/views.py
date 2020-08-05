from django.shortcuts import render
from django.views import View
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import WishlistBookInstance
from catalog.views import BookListView, BookDetailView, AddBookToCollection, DeleteBookView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404, redirect
from catalog.crawlers.nytimes_api import NYTimesAPI
from catalog.crawlers.idreambook_reviews import CriticReviewsAPI
from catalog.forms import AddBookForm
# Create your views here.

class WishlistListView(BookListView):
    def __init__(self):
        self.model_name = WishlistBookInstance
        self.template_name = 'wishlist/wishlist_landing_page.html'

class WishlistDetailView(LoginRequiredMixin, View):
    login_url = "/accounts/login/"
    redirect_field_name = "login"
    def get(self, request, pk):
        context = {}
        book_instance = get_object_or_404(WishlistBookInstance, pk=pk)
        if book_instance:
            book_data = BookListView().prepare_books_data(book_instance)
            if book_data:
                context["bookinstance_obj"] = book_instance
                context.update(BookDetailView().clip_description(book_data, 200))
                context["nytimes_review"] = NYTimesAPI().get_book_review(book_instance.book)
                context["critcs_review"] = CriticReviewsAPI().get_critics_review(book_data)
                # context["user_review"] =
        return render(request,'wishlist/wishlist_book_detail.html',context)

class AddBookToWishlist(LoginRequiredMixin, View):
    login_url = "/accounts/login/"
    redirect_field_name = "login"
    def get(self, request):
        # If the method is get then the form is being called for the first time
        form = AddBookForm(initial = {})
        context = {'form': form,}
        return render(request, 'wishlist/add_book_form_wishlist.html', context)

    def post(self, request):
        # If this is a POST request then process the Form data
        # If the method is post that means the form is submitted
        # Create a form instance and populate it with data from the request (binding):
        form = AddBookForm(request.POST)
        if form.is_valid():
            # add the book to database
            book_obj = AddBookToCollection().create_book_object(form.cleaned_data)
            summary = form.cleaned_data["summary"]
            ## Now create a book instance object using the book object for a given user
            wishlistinst_obj = WishlistBookInstance.objects.create(book=book_obj, reason_to_buy=summary, book_owner=request.user)
            wishlistinst_obj.save()
            # redirect to a new URL:
            return HttpResponseRedirect(reverse('wishlist-initial'))

        context = {'form': form,}
        return render(request, 'wishlist/add_book_form_wishlist.html', context)

class DeleteBookWishlist(DeleteBookView):
    def __init__(self):
        self.model_name = WishlistBookInstance
        self.reverse_page = 'wishlist-initial'
        self.template_name = 'wishlist/delete_book_confirm_wishlist.html'
