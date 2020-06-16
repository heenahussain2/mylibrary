from django.shortcuts import render
from django.views import View
# Create your views here.

class WishlistListView(View):
    def get(self, request):
        context = {}
        return render(request, 'wishlist/wishlist_landing_page.html', context)
    def post(self, request):
        pass
