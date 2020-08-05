from django.shortcuts import render, get_object_or_404, redirect
from django.views import generic, View
from .models import Book, Author, Genre, Language, BookInstance
from wishlist.models import WishlistBookInstance
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse
from catalog.forms import AddBookForm, SignUpForm, BookReviewForm
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import Group, Permission
from .crawlers.google_books_api import GoogleBooksAPIData
from .crawlers.nytimes_api import NYTimesAPI
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from collections import OrderedDict
import base64
import datetime
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
        return render(request, 'landing_page.html', {'form': form})


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
        from_date = datetime.datetime.now() + datetime.timedelta(days=-30)
        to_date = datetime.date.today()
        current_user = request.user
        bookinst_obj = BookInstance.objects.filter(book_owner=request.user)
        wishlist_obj = WishlistBookInstance.objects.filter(book_owner=request.user)
        context["num_books_collection"] = len(bookinst_obj)
        context["num_books_wishlist"] =  len(wishlist_obj)
        context["from_date"] = from_date.date().strftime("%d/%m/%Y")
        context["to_date"] = to_date.strftime("%d/%m/%Y")
        recently_added_to_collection = self.recently_added("collection", current_user, from_date, to_date)
        recently_added_to_wishlist = self.recently_added("wishlist", current_user, from_date, to_date)
        ## For Recently added Books
        context["recently_added_data"] = [("Collection",recently_added_to_collection),("Wishlist",recently_added_to_wishlist)]

        return render(request, 'index.html', context=context)

    def recently_added(self, added_to, current_user, from_date, to_date):
        books_to_return = []
        # from_date = datetime.date(2020,6,27)
        ### NOTE: For now taking 30 days due to lack of data later will change to 3-4 days
        try:
            if added_to == "collection":
                recent_books = BookInstance.objects.filter(added_on__gte=from_date.date(), added_on__lte=to_date).exclude(book_owner=current_user).order_by('-added_on')
            elif added_to == "wishlist":
                recent_books = WishlistBookInstance.objects.filter(added_on__gte=from_date.date(), added_on__lte=to_date).exclude(book_owner=current_user).order_by('-added_on')
        except Exception:
            recent_books = []
        recent_books = recent_books[:6] if len(recent_books) > 6 else recent_books
        if recent_books:
            for book_inst in recent_books:
                temp_data = {}
                try:
                    google_books_data = GoogleBooksAPIData().get_book_data(isbn=book_inst.book.isbn)
                except Exception:
                    google_books_data = {}
                if google_books_data:
                    temp_data["book_inst_obj"] = book_inst
                    temp_data["book_thumbnail"] = google_books_data["book_image_links"]["thumbnail"]
                    books_to_return.append(temp_data)
        return books_to_return

class NytBestsellerView(LoginRequiredMixin, View):
    login_url = "/accounts/login/"
    redirect_field_name = "login"
    def get(self, request, genre):
        context = {}
        context["fiction_flag"] = True if genre == 'fiction' else False
        try:
            ## Get NYT Bestsellers List
            nyt_list_obj = NYTimesAPI().nyt_bestsellers_list(genre)
            context["from_date"] =nyt_list_obj["published_date"].strftime("%d/%m/%Y")
            context["to_date"] = nyt_list_obj["next_published_date"].strftime("%d/%m/%Y")
            context["nyt_list_data"] = list(nyt_list_obj["book_list"].values())
        except Exception:
             context["nyt_list_data"] = []
        return render(request, "catalog/nyt_bestseller_list.html",context)

class BestsellerDetailView(LoginRequiredMixin, View):
    login_url = "/accounts/login/"
    redirect_field_name = "login"
    def get(self, request, genre, isbn):
        context = {}
        book_obj = Book.objects.get(isbn=isbn)
        if book_obj:
            isbn_no = book_obj.isbn
            ny_times_data = NYTimesAPI().nyt_bestsellers_list(genre)
            encoded_str = str(base64.b64encode(isbn_no.encode("utf-8")),"utf-8")
            context["book_obj"] = book_obj
            context["google_books_data"] = GoogleBooksAPIData().get_book_data(isbn=isbn_no)
            context["nytimes_data"] = ny_times_data["book_list"].get(encoded_str,{})
            context["nytimes_review"] = NYTimesAPI().get_book_review(book_obj)
            context["fiction_flag"] = True if genre == 'fiction' else False
        return render(request, 'catalog/bestseller_details.html', context=context)

class BookListView(LoginRequiredMixin, View):
    login_url = "/accounts/login/"
    redirect_field_name = "login"

    def __init__(self, **kwargs):
        super(BookListView, self).__init__()
        self.model_name = BookInstance
        self.template_name = 'catalog/book_list.html'

    def get_queryset(self, current_user):
        return self.model_name.objects.filter(book_owner= current_user).order_by('added_on')

    def get(self, request):
        url_name = 'books'
        context = {}
        book_data_list = []
        try:
            book_obj =  self.get_queryset(request.user)
        except Exception:
            return HttpResponseRedirect(reverse(url_name))
        if book_obj:
            for each_book in book_obj:
                if each_book.book != None:
                    book_data = self.prepare_books_data(each_book)
                    if book_data:
                        clipped_data = BookDetailView().clip_description(book_data, 20)
                        clipped_data["book_data"]["bookinstance_obj"] = each_book
                        clipped_data["book_data"]["clipped_desc"] = clipped_data["clipped_desc"]
                        book_data_list.append(clipped_data["book_data"])
        ### For Pagination - each page will contain 4 objects
        paginated_list = self.paginate_data(request, book_data_list)
        return render(request, self.template_name, {"book_data_list": paginated_list})

    def prepare_books_data(self, each_book_obj):
        temp_book_data = {}
        book_title = each_book_obj.book.title.lower()
        author = each_book_obj.book.author.first_name.lower() + " " + each_book_obj.book.author.last_name.lower()
        temp_book_data = GoogleBooksAPIData().get_book_data(book_title=book_title, author=author)
        return temp_book_data

    def paginate_data(self, request, book_data_list):
        page = request.GET.get('page', 1)

        paginator = Paginator(book_data_list,6)
        try:
            paginated_list = paginator.page(page)
        except PageNotAnInteger:
            paginated_list = paginator.page(1)
        except EmptyPage:
            paginated_list = paginator.page(paginator.num_pages)
        return paginated_list

class BookDetailView(LoginRequiredMixin, View):
    login_url = "/accounts/login/"
    redirect_field_name = "login"
    def get(self, request, pk):
        context = {}
        book_instance = get_object_or_404(BookInstance, pk=pk)
        book_data = BookListView().prepare_books_data(book_instance)
        if book_data:
            context["bookinstance_obj"] = book_instance
            context.update(self.clip_description(book_data, 50))
            if book_instance.user_book_review == None:
                form = BookReviewForm(initial={})
                context["form"] = form
        return render(request,'catalog/book_detail.html',context)

    def post(self, request, pk):
        ### This part is to save user review of the book
        context = {}
        book_instance = get_object_or_404(BookInstance, pk=pk)
        form = BookReviewForm(request.POST)
        if form.is_valid():
            book_instance.user_book_review = form.cleaned_data["user_book_review"]
            book_instance.save()
            return HttpResponseRedirect(reverse("book-detail",args=[str(book_instance.id)]))

        book_data = BookListView().prepare_books_data(book_instance)
        if book_data:
            context["bookinstance_obj"] = book_instance
            context.update(self.clip_description(book_data, 50))
        context["form"] = form
        return render(request, 'catalog/book_detail.html', context)


    def clip_description(self, book_data, words_to_clip):
        temp_dict = {}
        temp_dict["clipped_desc"] = False
        desc = book_data["description"].split()
        if len(desc) > words_to_clip:
            temp_dict["clipped_desc"] = True
            book_data["clipped_description"] = " ".join(desc[:words_to_clip])
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

class DeleteBookView(LoginRequiredMixin, View):
    login_url = "/accounts/login/"
    redirect_field_name = "login"
    def __init__(self):
        super(DeleteBookView, self).__init__()
        self.model_name = BookInstance
        self.reverse_page = 'books'
        self.template_name = 'catalog/delete_book_confirm.html'

    def get(self, request, pk):
        book_instance = get_object_or_404(self.model_name, pk=pk)
        context = {'book_instance':book_instance}
        return render(request, self.template_name, context)

    def post(self, request, pk):
        book_instance = get_object_or_404(self.model_name, pk=pk)
        book_instance.delete()
        return HttpResponseRedirect(reverse(self.reverse_page))
