from django.shortcuts import render, get_object_or_404, redirect
from django.views import generic, View
from .models import Book, Author, Genre, Language, BookInstance
from wishlist.models import WishlistBookInstance
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse
from catalog.forms import AddBookForm, SignUpForm
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import Group, Permission
from .crawlers.google_books_api import GoogleBooksAPIData
from .crawlers.nytimes_api import NYTimesAPI
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from collections import OrderedDict
import base64
# Create your views here.
# from catalog.models import Book, Author, BookInstance, Genre

class LandingPageView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return HttpResponseRedirect(reverse('index'))
        else:
            form = SignUpForm(initial ={})
            return render(request, 'landing_page.html', {'form': form})

    def post(self, request):
        form = SignUpForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            ## if form is valid then create a new user
            self.add_new_user(form)
            ## USer Authentication Part
            user = authenticate(username=username, password=password)
            login(request, user)
            return redirect('index')

    def add_new_user(self, form):
        user_obj = form.save()
        group_name = "Library Members"
        try:
            group = Group.objects.get(name=group_name)
        except Group.DoesNotExist:
            ## Exception only ifgroup doesnot exist
            group = self.create_new_group(group_name)
        user_obj.groups.add(group)
        self.add_user_permissions(group, user_obj)

    def add_user_permissions(self, group, user_obj):
        for each_perm in group.permissions.all():
            user_obj.user_permissions.add(each_perm)

    def create_new_group(self, group_name):
        permissions_to_add = ["Can add book", "Can view book", "Can change book",
                              "Can add book instance","Can delete book instance",
                              "Can view book instance","Can change book instance"]
        group = Group.objects.create(name=group_name)
        group.save()
        for each_permission in permissions_to_add:
            try:
                perms = Permission.objects.get(name=each_permission)
                group.permissions.add(perms)
            except Exception:
                print(each_permission)
        return group

class HomePageView(LoginRequiredMixin, View):
    login_url = "/accounts/login/"
    redirect_field_name = "login"
    def get(self, request):
        context = {}
        final_top_list = []
        bookinst_obj = BookInstance.objects.filter(book_owner=request.user)
        wishlist_obj = WishlistBookInstance.objects.filter(book_owner=request.user)
        ## Get NYT Bestsellers List
        nyt_list_obj = NYTimesAPI().nyt_bestsellers_list()
        nyt_book_list = list(nyt_list_obj["book_list"].values())
        nyt_top10 = nyt_book_list[:7] if len(nyt_book_list) > 7 else nyt_book_list
        ### get top 5 book data from google books api and create a book object
        for top_book in nyt_top10:
             temp_data = OrderedDict()
             google_books_data = GoogleBooksAPIData().get_book_data(isbn=top_book["isbn_13"], nytimes_fiction=True)
             ## Create Book Object for detail view
             if google_books_data:
                 google_books_data["language"] = Language.objects.get(name="English")
                 google_books_data["genre_obj"] = []
                 for each_genre in google_books_data["genre"]:
                     try:
                         genre_obj = Genre.objects.get(name= each_genre)
                     except Exception:
                         genre_obj = Genre.objects.create(name= each_genre)
                         genre_obj.save()
                     google_books_data["genre_obj"].append(genre_obj)

                 book_obj = AddBookToCollection().create_book_object(google_books_data)
                 temp_data["book_obj"] = book_obj
                 temp_data["book_thumbnail"] = google_books_data["book_image_links"]["thumbnail"]
                 temp_data["rank"] = top_book["book_rank"]
                 temp_data["rank_last_week"] = top_book["rank_last_week"]
                 final_top_list.append(temp_data)
        context["num_books_collection"] = len(bookinst_obj)
        context["num_books_wishlist"] =  len(wishlist_obj)
        context["from_date"] =nyt_list_obj["published_date"].strftime("%d/%m/%Y")
        context["to_date"] = nyt_list_obj["next_published_date"].strftime("%d/%m/%Y")
        context["nyt_list_data"] = final_top_list[:5] if len(final_top_list) >5 else final_top_list
        return render(request, 'index.html', context=context)

class BestsellerDetailView(LoginRequiredMixin, View):
    login_url = "/accounts/login/"
    redirect_field_name = "login"
    def get(self, request, pk):
        context = {}
        book_obj = get_object_or_404(Book, pk=pk)
        if book_obj:
            google_books_data = GoogleBooksAPIData().get_book_data(isbn=book_obj.isbn)
            ny_times_data = NYTimesAPI().nyt_bestsellers_list()
            string_to_encode = google_books_data["isbn_13"]
            encoded_str = str(base64.b64encode(string_to_encode.encode("utf-8")),"utf-8")
            context["book_obj"] = book_obj
            context["google_books_data"] = google_books_data
            context["nytimes_data"] = ny_times_data["book_list"][encoded_str]
            context["nytimes_review"] = NYTimesAPI().get_book_review(google_books_data)
        return render(request, 'catalog/bestseller_details.html', context=context)


class BookListView(LoginRequiredMixin, View):
    login_url = "/accounts/login/"
    redirect_field_name = "login"
    def get(self, request):
        context = {}
        book_data_list = []
        book_obj = BookInstance.objects.filter(book_owner= request.user).order_by('added_on')
        ### For Pagination - each page will contain 4 objects
        page = request.GET.get('page', 1)
        if book_obj:
            for each_book in book_obj:
                book_data = self.prepare_books_data(each_book)
                if book_data:
                    book_data["bookinstance_obj"] = each_book
                    book_data_list.append(book_data)
        paginator = Paginator(book_data_list,6)
        try:
            paginated_list = paginator.page(page)
        except PageNotAnInteger:
            paginated_list = paginator.page(1)
        except EmptyPage:
            paginated_list = paginator.page(paginator.num_pages)

        return render(request,'catalog/book_list.html',{"book_data_list": paginated_list})

    def prepare_books_data(self, each_book_obj):
        temp_book_data = {}
        book_title = each_book_obj.book.title.lower()
        author = each_book_obj.book.author.first_name.lower() + " " + each_book_obj.book.author.last_name.lower()
        temp_book_data = GoogleBooksAPIData().get_book_data(book_title=book_title, author=author)
        return temp_book_data

class BookDetailView(LoginRequiredMixin, View):
    login_url = "/accounts/login/"
    redirect_field_name = "login"
    def get(self, request, pk):
        context = {}
        book_instance = get_object_or_404(BookInstance, pk=pk)
        if book_instance:
            book_data = BookListView().prepare_books_data(book_instance)
            if book_data:
                context["bookinstance_obj"] = book_instance
                context.update(self.clip_description(book_data))
        return render(request,'catalog/book_detail.html',context)

    def clip_description(self, book_data):
        temp_dict = {}
        temp_dict["clipped_desc"] = False
        desc = book_data["description"].split()
        if len(desc) > 50:
            temp_dict["clipped_desc"] = True
            book_data["clipped_description"] = " ".join(desc[:50])
        temp_dict["book_data"] = book_data
        return temp_dict

class AddBookToCollection(LoginRequiredMixin, View):
    login_url = "/accounts/login/"
    redirect_field_name = "login"
    def get(self, request):
        # If the method is get then the form is being called for the first time
        form = AddBookForm(initial = {})
        context = {'form': form,}
        return render(request, 'catalog/add_book_form.html', context)

    def post(self, request):
        # If this is a POST request then process the Form data
        # If the method is post that means the form is submitted
        # Create a form instance and populate it with data from the request (binding):
        form = AddBookForm(request.POST)
        if form.is_valid():
            # add the book to database
            book_obj = self.create_book_object(form.cleaned_data)
            summary = form.cleaned_data["summary"]
            ## Now create a book instance object using the book object for a given user
            bookinst_obj = BookInstance.objects.create(book=book_obj,summary=summary,book_owner=request.user)
            bookinst_obj.save()
            # redirect to a new URL:
            return HttpResponseRedirect(reverse('books'))

        context = {'form': form,}
        return render(request, 'catalog/add_book_form.html', context)

    def create_book_object(self, create_book_data):
        isbn_no = create_book_data["isbn_13"]
        ## Step 1 - Check if the book object exists # NOTE: For now i am using isbn as unique key to
        ## identify if a book object exists. It can be changed later.
        if not Book.objects.filter(isbn=isbn_no):
            ## If the book object does not exists, then create a new book and author objects and save them
            book_title = create_book_data["actual_book_title"]
            author_obj = self.create_author_object(create_book_data)
            ## Now create a new book object
            book_obj = Book.objects.create(title=book_title,author=author_obj,isbn=isbn_no, language=create_book_data["language"])
            book_obj.save()
            for each_obj in create_book_data["genre_obj"]:
                book_obj.genre.add(each_obj.id)
        else:
            ## if the book object exists, then get the book object
            book_obj = Book.objects.get(isbn=isbn_no)
        return book_obj

    def create_author_object(self, create_book_data):
        author_fname =  create_book_data["authors"][0].split()[0]
        author_lname = " ".join(create_book_data["authors"][0].split()[1:])
        ## Ifthe author object exists then get the author name
        if Author.objects.filter(first_name=author_fname, last_name=author_lname).first():
            author_obj =  Author.objects.get(first_name=author_fname, last_name=author_lname)
        else:
            ## else create a new author object and save it
            author_obj = Author.objects.create(first_name=author_fname, last_name=author_lname)
            author_obj.save()
        return author_obj


def delete_book(request, pk):
    book_instance = get_object_or_404(BookInstance, pk=pk)
    context = {'book_instance':book_instance}
    ## if request method is post then delete the book instance
    if request.method == 'POST':
        book_instance.delete()
        return HttpResponseRedirect(reverse('books'))

    return render(request, 'catalog/delete_book_confirm.html',context)
