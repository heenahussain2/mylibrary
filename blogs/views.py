from django.shortcuts import render
from django.views import View
# Create your views here.

class BlogLandingPage(View):
    def get(self, request):
        return render(request, 'blogs/blog_list.html',{})
        
