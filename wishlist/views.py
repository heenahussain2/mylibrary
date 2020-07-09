from django.shortcuts import render
from django.views import View
from .models import WishlistBookInstance
from catalog.views import BookListView, BookDetailView
# Create your views here.

class WishlistListView(View):
    def get(self, request):
        context = {}
        book_data_list = []
        book_obj = WishlistBookInstance.objects.filter(book_owner= request.user).order_by('added_on')
        if book_obj:
            for each_book in book_obj:
                book_data = BookListView().prepare_books_data(each_book)
                if book_data:
                    book_data["wishlist_instance_obj"] = each_book
                    book_data_list.append(book_data)
        # paginator = Paginator(book_data_list,4)
        # try:
        #     paginated_list = paginator.page(page)
        # except PageNotAnInteger:
        #     paginated_list = paginator.page(1)
        # except EmptyPage:
        #     paginated_list = paginator.page(paginator.num_pages)
        return render(request, 'wishlist/wishlist_landing_page.html', {"book_data_list":book_data_list})
