from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from .models import Genre, Language
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .crawlers.google_books_api import GoogleBooksAPIData
## Create from fields with this file
## The declaration syntax for a Form is very similar
## to that for declaring a Model, and shares the same field types (and some similar parameters).

class AddBookForm(forms.Form):
    book_title = forms.CharField(min_length=3, max_length=200,
                                 widget= forms.TextInput(attrs={"placeholder":"Enter Book Title", "class":"form-control"}))
    author_firstname = forms.CharField(max_length=50,
                                       widget= forms.TextInput(attrs={"placeholder":"First Name", "class":"author-form-control"}))
    author_lastname = forms.CharField(max_length=50,
                                      widget= forms.TextInput(attrs={"placeholder":"Last Name", "class":"author-form-control"}))
    summary = forms.CharField(max_length=1000,
                              widget=forms.Textarea(attrs={"placeholder":"Enter a brief description of the book", "class":"form-control"}))
    # isbn = forms.CharField(max_length=13,
    #                       widget = forms.TextInput(attrs={"placeholder":"13 Character ISBN No", "class":"form-control"}),
    #                       help_text='<a href="https://www.isbn-international.org/content/what-isbn">ISBN number</a>', required=True)
    # genre = forms.ModelMultipleChoiceField(queryset=Genre.objects.all(),widget=forms.widgets.CheckboxSelectMultiple())
    language = forms.ModelChoiceField(queryset=Language.objects.all(), empty_label="Select a Language")

    def clean(self):
        # super().clean()
        if self.cleaned_data["book_title"]:
            book_title = self.cleaned_data["book_title"].strip().lower()
            author = self.cleaned_data["author_firstname"].strip().lower() + " " + self.cleaned_data["author_lastname"].strip().lower()
            ## get book data from google books api and check if book title and author match
            book_data = GoogleBooksAPIData().get_book_data(book_title, author)
            # import pdb; pdb.set_trace()
            if book_data:
                if book_data["book_title"] == book_title and book_data["authors"][0].lower() == author:
                    book_data["language"] = self.cleaned_data["language"]
                    book_data["summary"] = self.cleaned_data["summary"]
                    ## first checkif the genre exists
                    book_data["genre_obj"] = []
                    for each_genre in book_data["genre"]:
                        try:
                            genre_obj = Genre.objects.get(name= each_genre)
                        except Exception:
                            genre_obj = Genre.objects.create(name= each_genre)
                            genre_obj.save()
                        book_data["genre_obj"].append(genre_obj)
                    return book_data

                elif book_data["book_title"] == book_title and book_data["authors"][0].lower() != author:
                    msg = "The author name doesnot match the book title\nDid you mean {}".format(book_data["authors"][0])
                    self.add_error("author_firstname",msg)
                else:
                    raise ValidationError(_("Title or Author Name is incorrect.\nPlease check the data and try again"))
            else:
                raise ValidationError(_("Cannot get any results\nPlease check if you have entered correct data\nOr check your internet connection"))

class SignUpForm(UserCreationForm):
# class SignUpForm(forms.Form):
    first_name = forms.CharField(max_length=30, required=True,
                                widget= forms.TextInput(attrs={"placeholder":"First Name", "class":"name-form-control"}))
    last_name = forms.CharField(max_length=30, required=True,
                                widget= forms.TextInput(attrs={"placeholder":"Last Name", "class":"name-form-control"}))
    email = forms.EmailField(max_length=254,required=False,
                            widget=forms.EmailInput(attrs={"placeholder":"Enter Your Email", "class":"form-control"}))
    def __init__(self, *args, **kwargs):
        super(SignUpForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget = forms.TextInput()
        self.fields["username"].help_text = []
        self.fields['username'].widget.attrs = {'class': 'form-control',"placeholder":"Enter username"}
        self.fields['password1'].widget.attrs = {'class': 'form-control',}
        self.fields['password1'].help_text = ["Your password must contain at least 8 characters.","Your password can’t be entirely numeric."]
        self.fields['password2'].widget.attrs = {'class': 'form-control',}
        self.fields['password2'].help_text = ["Enter the same password as before, for verification."]
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', )
        labels = {
                    'first_name': "First Name",
                    'last_name':"Last Name",
                }

class BookReviewForm(forms.Form):
    user_book_review = forms.CharField(max_length=1000,
                              widget=forms.Textarea(attrs={"placeholder":"Enter your review here"}))

    def clean_user_book_review(self):
        review_data = self.cleaned_data["user_book_review"]
        if len(review_data.split()) < 15:
            raise ValidationError(_("Review is too short. Please write a more detailed review"))
        else:
            return review_data
